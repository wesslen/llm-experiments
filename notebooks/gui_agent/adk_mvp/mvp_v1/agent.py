"""
Minimal GUI Agent using Google ADK + Playwright MCP
Default model: Gemini Flash 2.5
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Model configuration - defaults to Gemini Flash 2.5
MODEL = os.getenv("MODEL", "gemini-2.5-flash")


def validate_environment():
    """Validate required environment variables and configuration."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it with your Google API key. "
            "Get your key from: https://makersuite.google.com/app/apikey"
        )

    # Basic format validation
    if len(api_key.strip()) < 10:
        raise ValueError(
            "GEMINI_API_KEY appears to be invalid (too short). "
            "Please check your API key."
        )

# Agent instruction
INSTRUCTION = """You are a GUI automation agent that controls a web browser using Microsoft's Playwright MCP.

Available tools:
- init-browser: Initialize/navigate to a URL (required first step)
- get-interactive-snapshot: Get accessibility tree of current page with interactive elements
- get-screenshot: Take a screenshot of the page
- execute-code: Execute Playwright code for interactions (click, type, etc.)
- get-full-dom: Get full DOM snapshot
- get-text-snapshot: Get text content snapshot
- get-full-snapshot: Get complete page snapshot

Workflow:
1. Always start with init-browser to navigate to the target URL
2. Use get-interactive-snapshot to understand page structure and find elements
3. Use execute-code to interact with elements (clicks, typing, etc.)
4. Use get-screenshot when visual confirmation is needed
5. Confirm completion

Be concise and efficient."""


def create_gui_agent():
    """
    Create GUI agent with MCP toolset.

    This factory function validates the environment before creating the agent,
    ensuring all required configuration is present.

    Returns:
        LlmAgent: Configured GUI automation agent with Playwright MCP tools

    Raises:
        ValueError: If GEMINI_API_KEY is not set or invalid
    """
    validate_environment()

    return LlmAgent(
        model=MODEL,
        name="gui_agent",
        instruction=INSTRUCTION,
        tools=[
            McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="npx",
                        args=["-y", "playwright-mcp@latest"],
                    ),
                ),
                # Optional: filter to specific tools
                # tool_filter=["browser_navigate", "browser_snapshot", "browser_click", "browser_type", "browser_screenshot"]
            )
        ],
    )


# Create root agent for backwards compatibility with adk web
# Note: This will validate environment at import time
root_agent = create_gui_agent()
