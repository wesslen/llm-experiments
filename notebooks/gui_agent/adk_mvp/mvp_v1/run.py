"""
Standalone runner for GUI agent (outside adk web)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Import types from google.genai
# Note: This should work with google-adk's internal type system
try:
    from google.genai import types
except ImportError:
    print("Error: google.genai types not available. Ensure google-adk is installed.")
    sys.exit(1)

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Configuration
MAX_ITERATIONS = 50  # Prevent infinite loops
TASK_TIMEOUT = 300  # 5 minutes timeout for task completion

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


async def create_agent():
    """
    Create agent with MCP toolset.

    Returns:
        tuple: (agent, toolset) where agent is the LlmAgent and toolset is the McpToolset

    Raises:
        ValueError: If GEMINI_API_KEY is not set
        RuntimeError: If MCP toolset initialization fails
    """
    # Validate environment (same validation as agent.py)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it with your Google API key. "
            "Get your key from: https://makersuite.google.com/app/apikey"
        )

    if len(api_key.strip()) < 10:
        raise ValueError(
            "GEMINI_API_KEY appears to be invalid (too short). "
            "Please check your API key."
        )

    try:
        toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "playwright-mcp@latest"],
                ),
                timeout=120,  # 2 minutes for complex interactions
            ),
        )

        agent = LlmAgent(
            model=MODEL,
            name="gui_agent",
            instruction=INSTRUCTION,
            tools=[toolset],
        )
        return agent, toolset
    except Exception as e:
        raise RuntimeError(f"Failed to initialize MCP toolset: {e}") from e


async def run_task(task: str):
    """
    Run a single task with the GUI agent.

    Args:
        task: The task description to execute

    Raises:
        ValueError: If task is empty or invalid
        RuntimeError: If agent initialization fails
        asyncio.TimeoutError: If task exceeds timeout
    """
    if not task or not task.strip():
        raise ValueError("Task cannot be empty")

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

    iteration_count = 0
    try:
        # Apply timeout to the entire task
        async for event in asyncio.wait_for(
            runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content,
            ),
            timeout=TASK_TIMEOUT
        ):
            iteration_count += 1
            if iteration_count > MAX_ITERATIONS:
                print(f"\n⚠️  Warning: Reached maximum iterations ({MAX_ITERATIONS}). Stopping.")
                break

            # Print agent responses
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"Agent: {part.text}")
                    elif hasattr(part, "function_call"):
                        func_name = part.function_call.name
                        func_args = part.function_call.args
                        print(f"Tool: {func_name}({func_args})")

    except asyncio.TimeoutError:
        print(f"\n❌ Error: Task timed out after {TASK_TIMEOUT} seconds")
        raise
    except KeyboardInterrupt:
        print("\n\n⚠️  Task interrupted by user")
        raise
    except Exception as e:
        print(f"\n❌ Error during task execution: {e}")
        raise
    finally:
        try:
            await toolset.close()
            print("\n✅ Cleaned up MCP toolset")
        except Exception as e:
            print(f"\n⚠️  Warning: Error closing toolset: {e}")


async def main():
    """Main entry point for standalone runner."""
    try:
        task = input("Enter task (or press Enter for demo): ").strip()
        if not task:
            task = "Navigate to example.com and tell me what you see"
            print(f"Using demo task: {task}\n")

        await run_task(task)
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file or environment variables.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
