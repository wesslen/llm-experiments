"""
Enterprise behavioral tests for CRM Lead Entry use case.

Tests GUI agent's ability to:
- Navigate and interact with CRM forms
- Handle form validation errors
- Detect and communicate modal dialogs
- Complete multi-step workflows

Uses mock CRM HTML to simulate HubSpot-like interface.
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
TEST_SPEC_FILE = Path(__file__).parent.parent.parent / "evaluations" / "crm_tests.evalset.json"
with open(TEST_SPEC_FILE) as f:
    TEST_SPEC = json.load(f)


@pytest.fixture(scope="module")
def mock_http_server():
    """
    Start HTTP server to serve mock HTML files.

    Serves files from the mocks directory on localhost.
    """
    mocks_dir = Path(__file__).parent / "mocks"

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(mocks_dir), **kwargs)

        def log_message(self, format, *args):
            # Suppress HTTP server logs during tests
            pass

    # Find available port
    server = HTTPServer(("localhost", 0), Handler)
    port = server.server_address[1]

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://localhost:{port}"

    yield base_url

    # Cleanup
    server.shutdown()


@pytest.fixture
async def crm_runner(mcp_toolset, session_service, test_session):
    """Create configured runner for CRM tests."""
    agent = LlmAgent(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        name="gui_agent_crm_test",
        instruction="""You are a GUI automation agent that helps automate web tasks.

You have access to browser automation tools via Playwright MCP:
- init-browser: Navigate to a URL (required first step)
- get-interactive-snapshot: Get page structure with interactive elements
- execute-code: Execute Playwright code (clicks, typing, etc.)
- get-screenshot: Capture screenshots
- get-text-snapshot: Extract text content

IMPORTANT:
1. Always start with init-browser to navigate to the URL
2. Use get-interactive-snapshot to understand page structure
3. Wait for elements to be ready before interacting
4. Detect and communicate errors clearly to the user
5. When you encounter validation errors, modals, or unexpected UI, explain what you see
6. Do not hallucinate - only report what you actually observe
""",
        tools=[mcp_toolset],
    )

    runner = Runner(
        app_name="gui_agent_crm_test",
        agent=agent,
        session_service=session_service,
    )

    return runner


def extract_events_data(events):
    """
    Extract tool calls and agent responses from runner events.

    Returns:
        tuple: (tool_calls list, agent_responses list, events list)
    """
    tool_calls = []
    agent_responses = []

    for event in events:
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                # Extract tool calls
                if hasattr(part, "function_call") and part.function_call:
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {}
                    })

                # Extract agent text responses
                if hasattr(part, "text") and part.text:
                    agent_responses.append(part.text)

    return tool_calls, agent_responses, events


async def run_agent_task(runner, session, task_text):
    """
    Execute agent task and collect results.

    Args:
        runner: ADK Runner instance
        session: Test session
        task_text: User task string

    Returns:
        tuple: (tool_calls, agent_responses, events)
    """
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
@pytest.mark.crm
async def test_crm_happy_path(crm_runner, test_session, mock_http_server):
    """
    Test: Successfully create CRM lead with all fields.

    Expected behavior:
    - Navigate to CRM
    - Click create contact button
    - Fill all form fields
    - Submit successfully
    - Confirm creation
    """
    # Skip if using test API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    # Load test spec
    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "crm_happy_path")

    # Modify task to include mock CRM URL
    crm_url = f"{mock_http_server}/mock_crm.html"
    task = f"Navigate to {crm_url}. Then {test_case['user_task']}"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    # Execute agent
    tool_calls, agent_responses, events = await run_agent_task(crm_runner, test_session, task)

    # Extract tool names for easier checking
    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:200]}...")

    # Assertions

    # 1. Must use init-browser
    assert "init-browser" in tool_names, f"Expected init-browser in tool calls. Got: {tool_names}"

    # 2. Should use get-interactive-snapshot to understand page
    assert "get-interactive-snapshot" in tool_names, "Expected get-interactive-snapshot to analyze page"

    # 3. Should use execute-code to interact with form
    assert "execute-code" in tool_names, "Expected execute-code to interact with form elements"

    # 4. Check response quality
    assert len(combined_response) > 20, f"Response too short: {combined_response}"

    # 5. Check expected response keywords
    response_lower = combined_response.lower()
    assert any(keyword in response_lower for keyword in test_case["expected_response_contains"]), \
        f"Expected response to contain one of {test_case['expected_response_contains']}, got: {combined_response}"

    # 6. Verify multiple execute-code calls (form has multiple fields)
    execute_code_count = tool_names.count("execute-code")
    assert execute_code_count >= 3, \
        f"Expected at least 3 execute-code calls for form interaction, got {execute_code_count}"

    print("\n[Result] ✅ Test passed - Agent successfully created CRM lead")


@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.crm
async def test_crm_validation_error(crm_runner, test_session, mock_http_server):
    """
    Test: Handle form validation error when required field is missing.

    Expected behavior:
    - Navigate to CRM
    - Attempt to submit form without email
    - Detect validation error
    - Communicate error clearly to user
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "crm_validation_error")

    crm_url = f"{mock_http_server}/mock_crm.html"
    task = f"Navigate to {crm_url}. Then {test_case['user_task']}"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    tool_calls, agent_responses, events = await run_agent_task(crm_runner, test_session, task)

    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:200]}...")

    # Assertions

    # 1. Must navigate
    assert "init-browser" in tool_names

    # 2. Should attempt form interaction
    assert "execute-code" in tool_names

    # 3. Check for error detection in response
    response_lower = combined_response.lower()

    error_keywords_found = sum(1 for kw in test_case["expected_response_contains"] if kw in response_lower)

    assert error_keywords_found >= 2, \
        f"Expected at least 2 error keywords {test_case['expected_response_contains']} in response. " \
        f"Found {error_keywords_found}. Response: {combined_response}"

    # 4. Should NOT report success
    success_keywords = ["successfully", "created lead", "saved"]
    assert not any(kw in response_lower for kw in success_keywords), \
        f"Agent incorrectly reported success despite validation error: {combined_response}"

    # 5. Should have detected the issue (likely via snapshot after submit attempt)
    assert "get-interactive-snapshot" in tool_names or "get-screenshot" in tool_names, \
        "Agent should inspect page after form submission to detect error"

    print("\n[Result] ✅ Test passed - Agent correctly detected and communicated validation error")


@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.crm
async def test_crm_duplicate_modal(crm_runner, test_session, mock_http_server):
    """
    Test: Detect and communicate duplicate contact modal dialog.

    Expected behavior:
    - Navigate to CRM
    - Attempt to create contact with existing email
    - Detect modal overlay
    - Communicate options to user
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "crm_duplicate_modal")

    crm_url = f"{mock_http_server}/mock_crm.html"
    # Use the known duplicate email
    task = f"Navigate to {crm_url}. Create a new lead: First Name: Sarah, Last Name: Johnson, Email: sarah.johnson@techcorp.com, Company: TechCorp Industries"

    print(f"\n[Test] {test_case['name']}")
    print(f"[Task] {task}")

    tool_calls, agent_responses, events = await run_agent_task(crm_runner, test_session, task)

    tool_names = [tc["name"] for tc in tool_calls]
    combined_response = " ".join(agent_responses)

    print(f"\n[Tool Calls] {tool_names}")
    print(f"[Response] {combined_response[:200]}...")

    # Assertions

    # 1. Must navigate and interact
    assert "init-browser" in tool_names
    assert "execute-code" in tool_names

    # 2. Should take snapshot after modal appears
    assert "get-interactive-snapshot" in tool_names, \
        "Agent should take snapshot to detect modal"

    # 3. Check for modal/duplicate detection in response
    response_lower = combined_response.lower()

    duplicate_keywords_found = sum(1 for kw in test_case["expected_response_contains"] if kw in response_lower)

    assert duplicate_keywords_found >= 2, \
        f"Expected agent to communicate duplicate detection with keywords {test_case['expected_response_contains']}. " \
        f"Found {duplicate_keywords_found}. Response: {combined_response}"

    # 4. Agent should ask for user clarification or present options
    clarification_indicators = ["would you like", "what would", "should i", "options:", "you can"]
    has_clarification = any(ind in response_lower for ind in clarification_indicators)

    # Alternatively, agent may explicitly list the modal options
    modal_option_mentioned = any(opt in response_lower for opt in ["view existing", "create anyway", "cancel"])

    assert has_clarification or modal_option_mentioned, \
        f"Agent should ask for clarification or mention modal options. Response: {combined_response}"

    print("\n[Result] ✅ Test passed - Agent detected duplicate modal and communicated options")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
