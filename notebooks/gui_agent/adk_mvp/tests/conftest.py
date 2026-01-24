"""
Shared pytest fixtures for GUI Agent tests.

This module provides fixtures that are used across multiple test files:
- mcp_toolset: Session-scoped MCP toolset for browser automation
- session_service: InMemorySessionService for stateless testing
- test_session: Individual test session
"""

import os
import pytest
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


@pytest.fixture(scope="function")
async def mcp_toolset():
    """
    Create and cleanup MCP toolset for each test.

    Note: Changed to function-scoped to work with pytest-asyncio.
    Session-scoped async fixtures have event loop issues.

    Yields:
        McpToolset: Initialized MCP toolset with Playwright tools

    Cleanup:
        Properly closes the MCP toolset to prevent resource leaks
    """
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "playwright-mcp@latest"],
            ),
        ),
    )

    yield toolset

    # Cleanup - ensure MCP process is terminated
    await toolset.close()


@pytest.fixture
async def session_service():
    """
    Provide InMemorySessionService for testing.

    This is function-scoped so each test gets a fresh session service.

    Returns:
        InMemorySessionService: Session service for stateless testing
    """
    return InMemorySessionService()


@pytest.fixture
async def test_session(session_service):
    """
    Create a test session.

    Args:
        session_service: InMemorySessionService from fixture

    Returns:
        Session: Created test session with empty state
    """
    session = await session_service.create_session(
        state={},
        app_name="gui_agent_test",
        user_id="test_user"
    )
    return session


@pytest.fixture
def sample_env_vars(monkeypatch):
    """
    Set sample environment variables for testing.

    This fixture can be used to ensure tests have required env vars set.
    Uses monkeypatch to avoid polluting the actual environment.

    Args:
        monkeypatch: pytest's monkeypatch fixture
    """
    # Only set if not already present (don't override real values)
    if not os.getenv("GEMINI_API_KEY"):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-minimum-length-requirement")

    if not os.getenv("MODEL"):
        monkeypatch.setenv("MODEL", "gemini-2.5-flash")
