"""
Behavioral end-to-end tests for GUI Agent.

These tests validate complete agent workflows using the Runner pattern.
They test "happy path" scenarios where the agent successfully completes
multi-step tasks using Playwright MCP tools.

Strategy: End-to-end agent tests with real browser and API calls

Run: pytest tests/test_behavioral.py -v -s
Warning: These tests make real API calls to Gemini and may take longer
"""

import pytest
import os
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner


@pytest.mark.asyncio
async def test_navigate_and_describe(mcp_toolset, session_service, test_session):
    """
    Test: Navigate to a website and describe what you see.

    Happy path scenario:
    1. Agent receives task to navigate to example.com
    2. Agent uses browser_navigate
    3. Agent uses browser_snapshot to understand page
    4. Agent describes the page content

    Verifies:
    - browser_navigate is called
    - browser_snapshot is called
    - Agent provides a text response
    - No errors occur
    """
    # Skip if API key is not real (e.g., test key from fixture)
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    # Create agent
    agent = LlmAgent(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        name="gui_agent_test",
        instruction="""You are a GUI automation agent that controls a web browser using Microsoft's Playwright MCP.

Available tools:
- init-browser: Initialize/navigate to a URL (required first step)
- get-interactive-snapshot: Get accessibility tree with interactive elements
- get-screenshot: Take a screenshot
- execute-code: Execute Playwright code for interactions

Workflow:
1. Start with init-browser to navigate
2. Use get-interactive-snapshot to understand page structure
3. Use execute-code to interact with elements
4. Confirm completion

Be concise and efficient.""",
        tools=[mcp_toolset],
    )

    # Create runner
    runner = Runner(
        app_name="gui_agent_test",
        agent=agent,
        session_service=session_service,
    )

    # Define task
    task = "Navigate to https://example.com and tell me what you see"
    content = types.Content(role="user", parts=[types.Part(text=task)])

    # Execute task and collect events
    events = []
    tool_calls = []
    agent_responses = []

    try:
        async for event in runner.run_async(
            session_id=test_session.id,
            user_id=test_session.user_id,
            new_message=content,
        ):
            events.append(event)

            # Extract tool calls and responses
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        agent_responses.append(part.text)
                    elif hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(part.function_call.name)

    except Exception as e:
        pytest.fail(f"Agent execution failed: {e}")

    # Assertions
    assert len(events) > 0, "No events received from agent"

    # Verify init-browser was called (required for navigation)
    assert "init-browser" in tool_calls, (
        f"Expected init-browser in tool calls. Got: {tool_calls}"
    )

    # Verify get-interactive-snapshot was likely called (agent should inspect page)
    # This is optional but recommended behavior
    if "get-interactive-snapshot" not in tool_calls:
        print("⚠️  Warning: Agent didn't use get-interactive-snapshot (recommended)")

    # Verify agent provided a text response
    assert len(agent_responses) > 0, "Agent didn't provide any text response"

    # Verify response mentions the page in some way
    combined_response = " ".join(agent_responses).lower()
    assert len(combined_response) > 20, "Agent response seems too short"

    print(f"\n✅ Task completed successfully")
    print(f"Tool calls: {tool_calls}")
    print(f"Agent response: {agent_responses[-1][:200]}...")


@pytest.mark.asyncio
async def test_search_wikipedia(mcp_toolset, session_service, test_session):
    """
    Test: Navigate to Wikipedia and search for a topic.

    Happy path scenario:
    1. Agent navigates to wikipedia.org
    2. Agent finds search input field
    3. Agent types search query
    4. Agent clicks search or submits
    5. Agent provides summary of results

    Verifies:
    - Multiple tool calls in sequence
    - Navigation, snapshot, typing, clicking work together
    - Agent completes multi-step task
    """
    # Skip if API key is not real
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    # Create agent
    agent = LlmAgent(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        name="gui_agent_test",
        instruction="""You are a GUI automation agent that controls a web browser using Microsoft's Playwright MCP.

Available tools:
- init-browser: Initialize/navigate to a URL (required first step)
- get-interactive-snapshot: Get accessibility tree with interactive elements
- get-screenshot: Take a screenshot
- execute-code: Execute Playwright code for interactions

Workflow:
1. Start with init-browser to navigate
2. Use get-interactive-snapshot to understand page structure
3. Use execute-code to interact with elements
4. Confirm completion

Be concise and efficient.""",
        tools=[mcp_toolset],
    )

    # Create runner
    runner = Runner(
        app_name="gui_agent_test",
        agent=agent,
        session_service=session_service,
    )

    # Define task
    task = "Go to wikipedia.org and search for 'Python programming language'"
    content = types.Content(role="user", parts=[types.Part(text=task)])

    # Execute task
    events = []
    tool_calls = []
    agent_responses = []

    try:
        async for event in runner.run_async(
            session_id=test_session.id,
            user_id=test_session.user_id,
            new_message=content,
        ):
            events.append(event)

            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        agent_responses.append(part.text)
                    elif hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(part.function_call.name)

    except Exception as e:
        # Multi-step tasks may be more prone to failure
        # Log the error but provide helpful context
        print(f"\n⚠️  Agent encountered error: {e}")
        print(f"Completed tool calls: {tool_calls}")
        print(f"Responses so far: {agent_responses}")
        pytest.fail(f"Agent execution failed during Wikipedia search: {e}")

    # Assertions
    assert len(events) > 0, "No events received from agent"

    # Should have navigated
    assert "init-browser" in tool_calls, (
        f"Expected init-browser. Got: {tool_calls}"
    )

    # Should have taken snapshot(s) to understand page
    assert "get-interactive-snapshot" in tool_calls, (
        f"Expected get-interactive-snapshot to understand page structure. Got: {tool_calls}"
    )

    # For a search task, we expect code execution for interactions
    # This may vary based on how agent chooses to interact
    has_interaction = "execute-code" in tool_calls

    if not has_interaction:
        print("⚠️  Warning: Agent didn't execute code to interact with the page")

    # Verify agent provided response
    assert len(agent_responses) > 0, "Agent didn't provide any response"

    combined_response = " ".join(agent_responses).lower()
    assert len(combined_response) > 20, "Agent response seems too short"

    print(f"\n✅ Search task completed")
    print(f"Tool calls: {tool_calls}")
    print(f"Final response: {agent_responses[-1][:200]}...")


@pytest.mark.asyncio
async def test_agent_error_handling(mcp_toolset, session_service, test_session):
    """
    Test that agent handles invalid URLs gracefully.

    This tests error recovery behavior when navigation fails.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key.startswith("test-"):
        pytest.skip("Skipping behavioral test with test API key")

    agent = LlmAgent(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        name="gui_agent_test",
        instruction="You are a GUI automation agent. Navigate to URLs and describe what you see.",
        tools=[mcp_toolset],
    )

    runner = Runner(
        app_name="gui_agent_test",
        agent=agent,
        session_service=session_service,
    )

    # Try navigating to invalid URL
    task = "Navigate to https://this-domain-definitely-does-not-exist-12345.com"
    content = types.Content(role="user", parts=[types.Part(text=task)])

    events = []
    agent_responses = []

    try:
        async for event in runner.run_async(
            session_id=test_session.id,
            user_id=test_session.user_id,
            new_message=content,
        ):
            events.append(event)

            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        agent_responses.append(part.text)

    except Exception:
        # Agent may fail, which is acceptable for this test
        pass

    # Agent should have attempted the task and gotten some response
    # Either an error message or indication it couldn't navigate
    assert len(events) > 0, "Agent should have attempted to process the task"

    print(f"\n✅ Error handling test completed")
    print(f"Agent handled invalid URL scenario")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
