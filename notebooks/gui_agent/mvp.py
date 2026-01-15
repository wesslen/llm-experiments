“””
Minimal GUI Agent using Playwright MCP + OpenAI client (Gemini Flash 2.5)
“””

import os
import json
import asyncio
from openai import OpenAI

# Initialize OpenAI client pointing to Gemini

client = OpenAI(
api_key=os.getenv(“GEMINI_API_KEY”, os.getenv(“GOOGLE_API_KEY”)),
base_url=“https://generativelanguage.googleapis.com/v1beta/openai/”
)

MODEL = os.getenv(“MODEL”, “gemini-2.5-flash-preview-05-20”)

# Playwright MCP tools schema

TOOLS = [
{
“type”: “function”,
“function”: {
“name”: “playwright_navigate”,
“description”: “Navigate to a URL”,
“parameters”: {
“type”: “object”,
“properties”: {“url”: {“type”: “string”, “description”: “URL to navigate to”}},
“required”: [“url”]
}
}
},
{
“type”: “function”,
“function”: {
“name”: “playwright_screenshot”,
“description”: “Take a screenshot of the current page”,
“parameters”: {“type”: “object”, “properties”: {}}
}
},
{
“type”: “function”,
“function”: {
“name”: “playwright_click”,
“description”: “Click an element on the page”,
“parameters”: {
“type”: “object”,
“properties”: {“selector”: {“type”: “string”, “description”: “CSS selector”}},
“required”: [“selector”]
}
}
},
{
“type”: “function”,
“function”: {
“name”: “playwright_fill”,
“description”: “Fill out an input field”,
“parameters”: {
“type”: “object”,
“properties”: {
“selector”: {“type”: “string”, “description”: “CSS selector”},
“value”: {“type”: “string”, “description”: “Value to fill”}
},
“required”: [“selector”, “value”]
}
}
},
{
“type”: “function”,
“function”: {
“name”: “playwright_evaluate”,
“description”: “Execute JavaScript in the browser”,
“parameters”: {
“type”: “object”,
“properties”: {“script”: {“type”: “string”, “description”: “JavaScript to execute”}},
“required”: [“script”]
}
}
}
]

SYSTEM_PROMPT = “”“You are a GUI automation agent. You can control a web browser using these tools:

- playwright_navigate: Go to a URL
- playwright_screenshot: Take a screenshot
- playwright_click: Click elements (use CSS selectors)
- playwright_fill: Type into input fields
- playwright_evaluate: Run JavaScript

When given a task:

1. Navigate to the relevant page
1. Take screenshots to understand the current state
1. Interact with elements to complete the task
1. Confirm completion

Be concise. Use selectors like: button, input[type=“text”], #id, .class, [aria-label=“X”]”””

class GUIAgent:
def **init**(self, mcp_client=None):
self.mcp = mcp_client  # Playwright MCP client
self.messages = [{“role”: “system”, “content”: SYSTEM_PROMPT}]

```
async def execute_tool(self, name: str, args: dict) -> str:
    """Execute a Playwright MCP tool"""
    if self.mcp:
        # Real MCP call
        result = await self.mcp.call_tool(name, args)
        return json.dumps(result)
    else:
        # Stub for testing without MCP
        return json.dumps({"status": "ok", "tool": name, "args": args})

async def step(self) -> tuple[str, bool]:
    """Run one agent step. Returns (response_text, is_done)"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=self.messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    self.messages.append(msg)
    
    # No tool calls = agent is done
    if not msg.tool_calls:
        return msg.content or "", True
    
    # Execute tool calls
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        result = await self.execute_tool(tc.function.name, args)
        self.messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result
        })
        print(f"  → {tc.function.name}({args}) = {result[:100]}...")
    
    return msg.content or "", False

async def run(self, task: str, max_steps: int = 10) -> str:
    """Run the agent on a task"""
    print(f"Task: {task}")
    self.messages.append({"role": "user", "content": task})
    
    for i in range(max_steps):
        print(f"\n[Step {i+1}]")
        text, done = await self.step()
        if text:
            print(f"  Agent: {text}")
        if done:
            return text
    
    return "Max steps reached"
```

async def main():
agent = GUIAgent()

```
# Example task
task = input("Enter task (or press Enter for demo): ").strip()
if not task:
    task = "Navigate to google.com and tell me what you see"

result = await agent.run(task)
print(f"\n=== Result ===\n{result}")
```

if **name** == “**main**”:
asyncio.run(main())
