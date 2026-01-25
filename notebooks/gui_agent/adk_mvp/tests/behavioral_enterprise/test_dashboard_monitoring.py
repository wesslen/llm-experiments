"""
Enterprise behavioral tests for Dashboard Monitoring use case.

Tests GUI agent's ability to:
- Extract metrics from dashboards
- Apply threshold logic correctly
- Handle AJAX/dynamic content loading
- Gracefully handle missing elements

Uses mock dashboard HTML to simulate Grafana-like interface.
"""

import pytest
import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai import types


# Load test specifications
# Evaluations are at project root: adk_mvp/evaluations/
TEST_SPEC_FILE = Path(__file__).parent.parent.parent / "evaluations" / "dashboard_tests.evalset.json"
with open(TEST_SPEC_FILE) as f:
    TEST_SPEC = json.load(f)


@pytest.fixture(scope="module")
def mock_http_server():
    """Start HTTP server to serve mock HTML files."""
    mocks_dir = Path(__file__).parent / "mocks"

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(mocks_dir), **kwargs)

        def log_message(self, format, *args):
            pass  # Suppress logs

    server = HTTPServer(("localhost", 0), Handler)
    port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://localhost:{port}"
    yield base_url
    server.shutdown()


@pytest.fixture
async def dashboard_runner(mcp_toolset, session_service, test_session):
    """Create configured runner for dashboard tests."""
    agent = LlmAgent(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        name="gui_agent_dashboard_test",
        instruction="""You are a GUI automation agent that helps monitor dashboards and extract metrics.

You have access to browser automation tools:
- init-browser: Navigate to a URL
- get-interactive-snapshot: Get page structure
- get-text-snapshot: Extract text content from page
- execute-code: Execute Playwright code
- get-screenshot: Capture visual screenshots

IMPORTANT for dashboard monitoring:
1. Dashboards may have AJAX loading - wait for content to load before extracting data
2. Use waitForSelector or waitForFunction to wait for dynamic content
3. Extract exact metric values - do not hallucinate numbers
4. If a metric is not found, clearly state what you DID find
5. Apply threshold comparisons accurately (>, <, ==)
6. Report all requested metrics even if some are missing
""",
        tools=[mcp_toolset],
    )

    runner = Runner(
        app_name="gui_agent_dashboard_test",
        agent=agent,
        session_service=session_service,
    )

    return runner


def extract_events_data(events):
    """Extract tool calls and responses from runner events."""
    tool_calls = []
    agent_responses = []

    for event in events:
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {}
                    })
                if hasattr(part, "text") and part.text:
                    agent_responses.append(part.text)

    return tool_calls, agent_responses


async def run_agent_task(runner, session, task_text):
    """Execute agent task and collect results."""
    content = types.Content(role="user", parts=[types.Part(text=task_text)])

    events = []
    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content,
    ):
        events.append(event)

    return extract_events_data(events)


@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.dashboard
async def test_dashboard_happy_path(dashboard_runner, test_session, mock_http_server):
    """
    Test: Extract metrics and apply threshold logic.

    Expected behavior:
    - Navigate to dashboard
    - Wait for AJAX loading
    - Extract metric values
    - Apply threshold comparison
    - Report findings
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "dashboard_happy_path")

    dashboard_url = f"{mock_http_server}/mock_dashboard.html"
    task = f"Navigate to {dashboard_url}. {test_case['user_task']}"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    tool_calls, agent_responses = await run_agent_task(dashboard_runner, test_session, task)

    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:300]}...")

    # Assertions

    # 1. Must navigate
    assert "init-browser" in tool_names, f"Expected init-browser. Got: {tool_names}"

    # 2. Should get snapshot or text to extract data
    assert "get-interactive-snapshot" in tool_names or "get-text-snapshot" in tool_names, \
        "Expected snapshot/text extraction to read metrics"

    # 3. Check for expected metric values in response
    response_lower = combined_response.lower()

    expected_metrics = test_case["expected_metric_extraction"]
    metrics_found = []

    if "67" in combined_response or "67.3" in combined_response:
        metrics_found.append("cpu_usage")
    if "58" in combined_response or "58.9" in combined_response:
        metrics_found.append("memory_usage")
    if "2.4" in combined_response:
        metrics_found.append("error_rate")

    assert len(metrics_found) >= 2, \
        f"Expected to find at least 2 metric values in response. Found: {metrics_found}. Response: {combined_response}"

    # 4. Verify threshold logic applied correctly
    # Metrics are below 80%, so should NOT trigger alert
    alert_keywords = ["alert", "warning", "exceeds", "above 80"]
    has_alert = any(kw in response_lower for kw in alert_keywords)

    assert not has_alert, \
        f"Agent should NOT alert (metrics are below 80%). Response: {combined_response}"

    # 5. Should mention normal/healthy status
    normal_indicators = ["normal", "below", "within", "healthy", "ok"]
    has_normal_indication = any(ind in response_lower for ind in normal_indicators)

    assert has_normal_indication, \
        f"Agent should indicate metrics are normal. Response: {combined_response}"

    print("\n[Result] ✅ Test passed - Agent extracted metrics and applied threshold logic correctly")


@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.dashboard
async def test_dashboard_ajax_delay(dashboard_runner, test_session, mock_http_server):
    """
    Test: Handle AJAX loading delays with proper wait strategies.

    Expected behavior:
    - Navigate to dashboard
    - Wait for dynamic content to load (not just fixed delay)
    - Extract metric after loading completes
    - Avoid extracting "Loading..." placeholder text
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "dashboard_ajax_delay")

    dashboard_url = f"{mock_http_server}/mock_dashboard.html"
    task = f"Navigate to {dashboard_url}. {test_case['user_task']}"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    tool_calls, agent_responses = await run_agent_task(dashboard_runner, test_session, task)

    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:300]}...")

    # Assertions

    # 1. Must navigate
    assert "init-browser" in tool_names

    # 2. Should use wait strategy (execute-code with wait)
    # The mock dashboard has 2-second AJAX delay
    execute_code_calls = [tc for tc in tool_calls if tc["name"] == "execute-code"]

    # Check if any execute-code contains wait logic
    has_wait_strategy = False
    for call in execute_code_calls:
        code = str(call.get("args", {})).lower()
        if "wait" in code:
            has_wait_strategy = True
            break

    if not has_wait_strategy:
        print("⚠️  Warning: Agent may not be using explicit wait strategy")
        # Note: Agent might still succeed if it takes snapshots after natural delay

    # 3. Check for latency value in response
    response_lower = combined_response.lower()

    # Expected: 245ms
    has_latency_value = "245" in combined_response or "latency" in response_lower

    assert has_latency_value, \
        f"Expected to find latency metric in response. Response: {combined_response}"

    # 4. Should NOT contain "loading" (would indicate agent extracted placeholder)
    assert "loading" not in response_lower, \
        f"Agent should wait for metrics to load, not extract 'Loading...' text. Response: {combined_response}"

    # 5. Should mention "ms" or "milliseconds" for latency
    has_unit = "ms" in response_lower or "millisecond" in response_lower

    assert has_unit, \
        f"Agent should include units when reporting latency. Response: {combined_response}"

    print("\n[Result] ✅ Test passed - Agent handled AJAX delay and extracted correct value")


@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.dashboard
async def test_dashboard_missing_metric(dashboard_runner, test_session, mock_http_server):
    """
    Test: Gracefully handle missing metrics.

    Expected behavior:
    - Navigate to dashboard
    - Search for requested metric
    - Detect metric is not available
    - Communicate clearly what WAS found
    - Do not hallucinate data
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "dashboard_missing_metric")

    dashboard_url = f"{mock_http_server}/mock_dashboard.html"
    task = f"Navigate to {dashboard_url}. {test_case['user_task']}"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    tool_calls, agent_responses = await run_agent_task(dashboard_runner, test_session, task)

    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:300]}...")

    # Assertions

    # 1. Must navigate and search
    assert "init-browser" in tool_names
    assert "get-interactive-snapshot" in tool_names or "get-text-snapshot" in tool_names

    # 2. Should communicate that metric was not found
    response_lower = combined_response.lower()

    not_found_indicators = ["could not find", "not found", "not available", "cannot find", "unable to find"]
    has_not_found = any(ind in response_lower for ind in not_found_indicators)

    assert has_not_found, \
        f"Agent should clearly communicate that metric was not found. Response: {combined_response}"

    # 3. Should mention what was searched for
    assert "database" in response_lower or "connection pool" in response_lower, \
        f"Agent should mention what it searched for. Response: {combined_response}"

    # 4. Should NOT hallucinate a value for missing metric
    # Check that response doesn't contain made-up numbers for database connections
    # The dashboard only has: 67.3, 58.9, 2.4, 245
    suspicious_numbers = ["100", "500", "1000", "10", "20", "50"]

    # If agent mentions database connection count, it's hallucinating
    if "database" in response_lower:
        for num in suspicious_numbers:
            pattern = f"{num} connection"
            assert pattern not in response_lower, \
                f"Agent may be hallucinating database connection value. Response: {combined_response}"

    # 5. Ideally, should list what IS available as alternative
    available_metrics = ["cpu", "memory", "error", "latency"]
    mentioned_available = sum(1 for metric in available_metrics if metric in response_lower)

    if mentioned_available >= 2:
        print("✅ Agent helpfully listed available metrics as alternatives")
    else:
        print("ℹ️  Agent could improve by suggesting available metrics")

    print("\n[Result] ✅ Test passed - Agent gracefully handled missing metric without hallucination")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
