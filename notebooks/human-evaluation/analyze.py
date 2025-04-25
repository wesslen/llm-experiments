import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import cohen_kappa_score, fleiss_kappa
from itertools import combinations
import datetime

# Load Excel file with all tabs
def load_eval_data(file_path):
    """Load evaluation data from Excel file with multiple tabs."""
    # Get sheet names
    xls = pd.ExcelFile(file_path)
    # Get sheet names that start with 'Eval'
    eval_sheets = [s for s in xls.sheet_names if s.startswith('Eval')]
    
    # Load each evaluation sheet
    all_evals = {}
    for sheet in eval_sheets:
        all_evals[sheet] = pd.read_excel(file_path, sheet_name=sheet)
    
    return all_evals

# Calculate basic statistics
def calculate_basic_stats(all_evals):
    """Calculate basic acceptability statistics for each evaluator."""
    stats = {}
    
    for evaluator, df in all_evals.items():
        total = len(df)
        acceptable = df['acceptable'].sum()
        acceptability_rate = acceptable / total * 100
        
        stats[evaluator] = {
            'total_queries': total,
            'acceptable_queries': acceptable,
            'acceptability_rate': acceptability_rate
        }
    
    return pd.DataFrame(stats).T

# Find overlapping queries across evaluators
def find_overlapping_queries(all_evals):
    """Identify overlapping queries across evaluators and create a combined dataset."""
    dfs = []
    
    for evaluator, df in all_evals.items():
        # Add evaluator column
        temp_df = df.copy()
        temp_df['evaluator'] = evaluator
        dfs.append(temp_df)
    
    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Find common queries based on query_id and doc_id
    query_counts = combined_df.groupby(['query_id', 'doc_id']).size().reset_index(name='count')
    overlapping_queries = query_counts[query_counts['count'] > 1]
    
    # Filter combined dataset to only include overlapping queries
    overlap_df = combined_df[combined_df.set_index(['query_id', 'doc_id']).index.isin(
        overlapping_queries.set_index(['query_id', 'doc_id']).index)]
    
    return overlap_df

# Calculate IAA metrics
def calculate_iaa(overlap_df):
    """Calculate Inter-Annotator Agreement metrics for overlapping queries."""
    # Pivot the data to get evaluators as columns and queries as rows
    pivot_df = overlap_df.pivot_table(
        index=['query_id', 'doc_id'], 
        columns='evaluator', 
        values='acceptable'
    )
    
    # Calculate pairwise Cohen's Kappa
    evaluators = pivot_df.columns
    kappa_pairs = {}
    
    for eval1, eval2 in combinations(evaluators, 2):
        # Get ratings for each pair of evaluators
        ratings1 = pivot_df[eval1].values
        ratings2 = pivot_df[eval2].values
        
        # Calculate Cohen's Kappa for this pair
        try:
            kappa = cohen_kappa_score(ratings1, ratings2)
            kappa_pairs[f"{eval1}-{eval2}"] = kappa
        except Exception as e:
            kappa_pairs[f"{eval1}-{eval2}"] = f"Error: {e}"
    
    # Try to calculate Fleiss' Kappa (for more than 2 evaluators)
    fleiss_k = None
    try:
        # Prepare data for Fleiss' Kappa
        categories = [0, 1]  # Binary categories: 0 and 1
        # Count how many raters assigned each category
        fleiss_data = []
        
        for _, row in pivot_df.iterrows():
            category_counts = [0] * len(categories)
            for cat in categories:
                category_counts[cat] = (row == cat).sum()
            fleiss_data.append(category_counts)
        
        # Calculate Fleiss' Kappa
        fleiss_k = fleiss_kappa(fleiss_data)
    except Exception as e:
        fleiss_k = f"Error calculating Fleiss' Kappa: {e}"
    
    return {
        'cohen_kappa_pairs': kappa_pairs,
        'fleiss_kappa': fleiss_k,
        'pivot_data': pivot_df
    }

# Create breakdowns by metadata
def metadata_analysis(all_evals):
    """Analyze acceptability rates by metadata categories."""
    combined = pd.concat([df.assign(evaluator=name) for name, df in all_evals.items()])
    
    # Analysis by question_type
    q_type_analysis = combined.groupby(['evaluator', 'question_type'])['acceptable'].agg(['mean', 'count']).reset_index()
    q_type_analysis['mean'] = q_type_analysis['mean'] * 100  # Convert to percentage
    
    # Analysis by doc_type
    doc_type_analysis = combined.groupby(['evaluator', 'doc_type'])['acceptable'].agg(['mean', 'count']).reset_index()
    doc_type_analysis['mean'] = doc_type_analysis['mean'] * 100  # Convert to percentage
    
    # Analysis by vendor
    vendor_analysis = combined.groupby(['evaluator', 'vendor'])['acceptable'].agg(['mean', 'count']).reset_index()
    vendor_analysis['mean'] = vendor_analysis['mean'] * 100  # Convert to percentage
    
    return {
        'question_type': q_type_analysis,
        'doc_type': doc_type_analysis,
        'vendor': vendor_analysis
    }

# Generate output file for unacceptable queries
def generate_unacceptable_report(all_evals, output_path=None):
    """Generate a report of all unacceptable queries with notes."""
    unacceptable_queries = []
    
    for evaluator, df in all_evals.items():
        unacceptable = df[df['acceptable'] == 0].copy()
        unacceptable['evaluator'] = evaluator
        unacceptable_queries.append(unacceptable)
    
    if unacceptable_queries:
        combined_unacceptable = pd.concat(unacceptable_queries, ignore_index=True)
        
        # Add columns for manual review
        combined_unacceptable['correction'] = ""
        combined_unacceptable['reviewed'] = False
        
        # Save to Excel if path provided
        if output_path:
            combined_unacceptable.to_excel(output_path, index=False)
        
        return combined_unacceptable
    else:
        return None

# Visualize the results
def visualize_results(basic_stats, metadata_analysis_results, iaa_results):
    """Create visualizations for the evaluation results."""
    # Set up the figure and axes
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # Plot acceptability rates
    sns.barplot(x=basic_stats.index, y='acceptability_rate', data=basic_stats, ax=axes[0, 0])
    axes[0, 0].set_title('Acceptability Rate by Evaluator')
    axes[0, 0].set_ylabel('Acceptability Rate (%)')
    axes[0, 0].set_xlabel('Evaluator')
    
    # Plot Cohen's Kappa scores
    kappa_df = pd.DataFrame(list(iaa_results['cohen_kappa_pairs'].items()), 
                           columns=['Evaluator Pair', 'Kappa'])
    sns.barplot(x='Evaluator Pair', y='Kappa', data=kappa_df, ax=axes[0, 1])
    axes[0, 1].set_title('Cohen\'s Kappa by Evaluator Pair')
    axes[0, 1].set_ylabel('Kappa Value')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Plot acceptability by question type
    q_type_df = metadata_analysis_results['question_type']
    pivot_q = q_type_df.pivot(index='question_type', columns='evaluator', values='mean')
    pivot_q.plot(kind='bar', ax=axes[1, 0])
    axes[1, 0].set_title('Acceptability Rate by Question Type')
    axes[1, 0].set_ylabel('Acceptability Rate (%)')
    axes[1, 0].set_xlabel('Question Type')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Plot acceptability by document type
    doc_type_df = metadata_analysis_results['doc_type']
    pivot_doc = doc_type_df.pivot(index='doc_type', columns='evaluator', values='mean')
    pivot_doc.plot(kind='bar', ax=axes[1, 1])
    axes[1, 1].set_title('Acceptability Rate by Document Type')
    axes[1, 1].set_ylabel('Acceptability Rate (%)')
    axes[1, 1].set_xlabel('Document Type')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

# Main function to run the evaluation
def run_evaluation(file_path, output_unacceptable_path=None):
    """Run the full evaluation analysis."""
    print("Loading evaluation data...")
    all_evals = load_eval_data(file_path)
    print(f"Loaded {len(all_evals)} evaluation sheets.")
    
    print("\nCalculating basic statistics...")
    basic_stats = calculate_basic_stats(all_evals)
    print(basic_stats)
    
    print("\nFinding overlapping queries...")
    overlap_df = find_overlapping_queries(all_evals)
    print(f"Found {len(overlap_df) // len(all_evals)} overlapping queries.")
    
    print("\nCalculating Inter-Annotator Agreement...")
    iaa_results = calculate_iaa(overlap_df)
    print("Cohen's Kappa for each pair of evaluators:")
    for pair, kappa in iaa_results['cohen_kappa_pairs'].items():
        print(f"  {pair}: {kappa:.4f}")
    print(f"Fleiss' Kappa: {iaa_results['fleiss_kappa']:.4f}")
    
    print("\nAnalyzing by metadata categories...")
    metadata_results = metadata_analysis(all_evals)
    
    print("\nGenerating report for unacceptable queries...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_unacceptable_path is None:
        output_unacceptable_path = f"unacceptable_queries_{timestamp}.xlsx"
    unacceptable_report = generate_unacceptable_report(all_evals, output_unacceptable_path)
    print(f"Unacceptable queries report saved to: {output_unacceptable_path}")
    
    print("\nVisualizing results...")
    fig = visualize_results(basic_stats, metadata_results, iaa_results)
    
    # Save visualization
    viz_path = f"evaluation_results_{timestamp}.png"
    fig.savefig(viz_path)
    print(f"Visualization saved to: {viz_path}")
    
    # Return all results
    return {
        'basic_stats': basic_stats,
        'overlap_data': overlap_df,
        'iaa_results': iaa_results,
        'metadata_analysis': metadata_results,
        'unacceptable_report': unacceptable_report,
        'visualization': fig
    }

# Example usage:
# results = run_evaluation('path_to_your_excel_file.xlsx')
