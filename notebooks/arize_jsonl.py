import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyarrow as pa
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import BoolValue, Int64Value
from tqdm import tqdm

from arize.pandas.proto import flight_pb2
from arize.exporter import ArizeExportClient
from arize.utils.types import Environments


def export_traces_to_jsonl(
    client: ArizeExportClient,
    output_path: str,
    space_id: str,
    model_id: str,
    start_time: datetime,
    end_time: datetime,
    model_version: Optional[str] = None,
    where: Optional[str] = None,
    columns: Optional[list] = None,
    stream_chunk_size: Optional[int] = None,
    parallelize_exports: Optional[bool] = None,
    transform_otel: bool = True,
) -> None:
    """
    Export trace data from Arize to JSONL format with streaming to avoid memory issues.
    
    Args:
        client: Initialized ArizeExportClient instance
        output_path: Path to output JSONL file (will be created/overwritten)
        space_id: Space ID from Arize UI
        model_id: Model/project name
        start_time: Start time (inclusive)
        end_time: End time (exclusive)
        model_version: Optional model version filter
        where: Optional SQL-like filter expression
        columns: Optional list of columns to export
        stream_chunk_size: Optional chunk size for streaming (default: server-determined)
        parallelize_exports: Optional flag to enable parallel exports
        transform_otel: Whether to apply OtelTracingDataTransformer (default: True)
    
    Returns:
        None (writes to file)
    """
    
    # Get the stream reader directly from the client's internal method
    stream_reader, num_recs = client._get_model_stream_reader(
        space_id=space_id,
        model_id=model_id,
        environment=Environments.TRACING,
        start_time=start_time,
        end_time=end_time,
        include_actuals=False,  # Not applicable for tracing
        model_version=model_version,
        batch_id=None,  # Not applicable for tracing
        where=where,
        similarity_search_params=None,
        columns=columns,
        stream_chunk_size=stream_chunk_size,
        parallelize_exports=parallelize_exports,
    )
    
    if stream_reader is None:
        print("No data to export")
        return
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize transformer if needed
    transformer = None
    if transform_otel:
        try:
            from arize.utils.tracing import OtelTracingDataTransformer
            transformer = OtelTracingDataTransformer()
        except ImportError:
            print("Warning: openinference-semantic-conventions not installed. "
                  "Skipping OTel transformation.")
            transform_otel = False
    
    progress_bar = tqdm(
        total=num_recs,
        desc=f"  exporting {num_recs} traces",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]",
        ncols=80,
        colour="#008000",
        unit=" trace",
    )
    
    records_written = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        while True:
            try:
                # Read chunk from stream
                flight_batch = stream_reader.read_chunk()
                record_batch = flight_batch.data
                
                # Convert to pandas for transformation (if needed) or direct conversion
                if transform_otel and transformer:
                    import pandas as pd
                    chunk_df = record_batch.to_pandas()
                    chunk_df = transformer.transform(chunk_df)
                    
                    # Write each row as JSONL
                    for _, row in chunk_df.iterrows():
                        # Convert row to dict, handling special types
                        record = row.to_dict()
                        record = _serialize_record(record)
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                        records_written += 1
                else:
                    # Direct conversion from Arrow to dict without pandas
                    for i in range(record_batch.num_rows):
                        record = {}
                        for col_name in record_batch.schema.names:
                            col = record_batch.column(col_name)
                            value = col[i].as_py()
                            record[col_name] = value
                        
                        record = _serialize_record(record)
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                        records_written += 1
                
                progress_bar.update(record_batch.num_rows)
                
            except StopIteration:
                break
    
    progress_bar.close()
    print(f"\nSuccessfully exported {records_written} traces to {output_path}")


def _serialize_record(record: dict) -> dict:
    """
    Convert record values to JSON-serializable types.
    
    Handles common non-serializable types like datetime, bytes, etc.
    """
    import pandas as pd
    from datetime import datetime, date
    
    serialized = {}
    for key, value in record.items():
        if pd.isna(value) or value is None:
            serialized[key] = None
        elif isinstance(value, (datetime, date)):
            serialized[key] = value.isoformat()
        elif isinstance(value, bytes):
            # Convert bytes to base64 string
            import base64
            serialized[key] = base64.b64encode(value).decode('ascii')
        elif isinstance(value, (list, tuple)):
            serialized[key] = [_serialize_value(v) for v in value]
        elif isinstance(value, dict):
            serialized[key] = _serialize_record(value)
        elif hasattr(value, 'item'):  # numpy types
            serialized[key] = value.item()
        else:
            serialized[key] = value
    
    return serialized


def _serialize_value(value):
    """Helper to serialize individual values in lists/arrays."""
    import pandas as pd
    from datetime import datetime, date
    
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, bytes):
        import base64
        return base64.b64encode(value).decode('ascii')
    elif isinstance(value, dict):
        return _serialize_record(value)
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    elif hasattr(value, 'item'):
        return value.item()
    else:
        return value


# Example usage
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    # Initialize client
    client = ArizeExportClient(
        api_key="your-api-key",  # or set ARIZE_API_KEY env var
    )
    
    # Export last 7 days of traces
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    export_traces_to_jsonl(
        client=client,
        output_path="./exports/traces.jsonl",
        space_id="your-space-id",
        model_id="your-model-id",
        start_time=start_time,
        end_time=end_time,
        transform_otel=True,  # Apply OpenInference transformations
        # Optional filters
        # where="span.status_code = 'ERROR'",
        # columns=["span_id", "trace_id", "name", "attributes"],
    )
