"""
Individual Playwright MCP tool tests.

These tests validate that the Playwright MCP toolset exposes the expected tools.
Actual tool execution is tested in the behavioral tests where tools are invoked
through the agent.

Strategy: Structural validation of available tools

Run: pytest tests/test_tools.py -v -s
"""

import pytest


@pytest.mark.asyncio
async def test_all_tools_available(mcp_toolset):
    """
    Test that all expected Playwright MCP tools are available.

    Verifies that the MCP toolset exposes the 5 core tools we need.
    """
    tools = await mcp_toolset.get_tools()
    tool_names = [tool.name for tool in tools]

    # Core tools we expect from Microsoft's playwright-mcp
    expected_tools = [
        "init-browser",  # Initialize/navigate browser
        "get-interactive-snapshot",  # Get accessibility tree
        "get-screenshot",  # Take screenshot
        "execute-code",  # Execute actions (click, type, etc.)
    ]

    missing_tools = [tool for tool in expected_tools if tool not in tool_names]

    assert not missing_tools, (
        f"Missing expected tools: {missing_tools}. "
        f"Available tools: {tool_names}"
    )

    # Verify we have at least these 4 core tools
    assert len(tool_names) >= 4, (
        f"Expected at least 4 tools, found {len(tool_names)}: {tool_names}"
    )

    print(f"\n✅ All {len(expected_tools)} expected tools are available")
    print(f"Total tools available: {len(tool_names)}")
    print(f"Tool names: {tool_names}")


@pytest.mark.asyncio
async def test_init_browser_available(mcp_toolset):
    """Verify init-browser tool is available."""
    tools = await mcp_toolset.get_tools()
    tool_names = [tool.name for tool in tools]

    assert "init-browser" in tool_names, (
        f"init-browser tool not found. Available: {tool_names}"
    )

    # Get the tool definition
    init_tool = next((t for t in tools if t.name == "init-browser"), None)
    assert init_tool is not None
    assert init_tool.name == "init-browser"

    print(f"✅ init-browser tool available")


@pytest.mark.asyncio
async def test_interactive_snapshot_available(mcp_toolset):
    """Verify get-interactive-snapshot tool is available."""
    tools = await mcp_toolset.get_tools()
    tool_names = [tool.name for tool in tools]

    assert "get-interactive-snapshot" in tool_names, (
        f"get-interactive-snapshot tool not found. Available: {tool_names}"
    )

    print(f"✅ get-interactive-snapshot tool available")


@pytest.mark.asyncio
async def test_screenshot_available(mcp_toolset):
    """Verify get-screenshot tool is available."""
    tools = await mcp_toolset.get_tools()
    tool_names = [tool.name for tool in tools]

    assert "get-screenshot" in tool_names, (
        f"get-screenshot tool not found. Available: {tool_names}"
    )

    print(f"✅ get-screenshot tool available")


@pytest.mark.asyncio
async def test_execute_code_available(mcp_toolset):
    """Verify execute-code tool is available."""
    tools = await mcp_toolset.get_tools()
    tool_names = [tool.name for tool in tools]

    assert "execute-code" in tool_names, (
        f"execute-code tool not found. Available: {tool_names}"
    )

    print(f"✅ execute-code tool available")


@pytest.mark.asyncio
async def test_mcp_toolset_initialization(mcp_toolset):
    """Verify MCP toolset initializes correctly."""
    assert mcp_toolset is not None, "MCP toolset is None"

    # Verify it has tools
    tools = await mcp_toolset.get_tools()
    assert tools is not None, "get_tools() returned None"
    assert len(tools) > 0, "No tools available from MCP toolset"

    print(f"✅ MCP toolset initialized with {len(tools)} tools")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
