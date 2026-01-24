"""
Standalone runner for GUI agent (outside adk web)
"""

import asyncio
import os
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

INSTRUCTION = """You are a GUI automation agent that controls a web browser.
Use browser_snapshot to understand page structure, then interact with elements.
Be concise."""


async def create_agent():
    """Create agent with MCP toolset."""
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@anthropic/playwright-mcp"],
            ),
        ),
    )
    
    agent = LlmAgent(
        model=MODEL,
        name="gui_agent",
        instruction=INSTRUCTION,
        tools=[toolset],
    )
    return agent, toolset


async def run_task(task: str):
    """Run a single task."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="gui_agent", user_id="user"
    )
    
    agent, toolset = await create_agent()
    
    runner = Runner(
        app_name="gui_agent",
        agent=agent,
        session_service=session_service,
    )
    
    print(f"Task: {task}\n")
    content = types.Content(role="user", parts=[types.Part(text=task)])
    
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=content,
        ):
            # Print agent responses
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"Agent: {part.text}")
                    elif hasattr(part, "function_call"):
                        print(f"Tool: {part.function_call.name}({part.function_call.args})")
    finally:
        await toolset.close()


async def main():
    task = input("Enter task (or press Enter for demo): ").strip()
    if not task:
        task = "Navigate to google.com and tell me what you see"
    await run_task(task)


if __name__ == "__main__":
    asyncio.run(main())
