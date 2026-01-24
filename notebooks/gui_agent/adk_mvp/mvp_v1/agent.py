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

# Agent instruction
INSTRUCTION = """You are a GUI automation agent that controls a web browser.

Available Playwright tools:
- browser_navigate: Go to a URL
- browser_snapshot: Get accessibility tree of current page  
- browser_click: Click elements (use accessibility name/role)
- browser_type: Type text into focused element
- browser_screenshot: Take a screenshot

When given a task:
1. Navigate to the relevant page
2. Use browser_snapshot to understand page structure
3. Interact with elements using their accessibility names
4. Confirm completion

Be concise. Prefer accessibility selectors over CSS."""

# Define the root agent with Playwright MCP tools
root_agent = LlmAgent(
    model=MODEL,
    name="gui_agent",
    instruction=INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@anthropic/playwright-mcp"],
                ),
            ),
            # Optional: filter to specific tools
            # tool_filter=["browser_navigate", "browser_snapshot", "browser_click", "browser_type"]
        )
    ],
)
