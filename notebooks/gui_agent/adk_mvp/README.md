# GUI Agent (Google ADK + Playwright MCP)

Minimal GUI automation agent using Google ADK with Playwright MCP server.

## Setup

```bash
# Install dependencies
pip install google-adk mcp python-dotenv

# Or with uv
uv pip install google-adk mcp python-dotenv

# Ensure Node.js/npx is available for Playwright MCP
node --version
npx --version
```

## Configuration

```bash
# Set your Google API key
export GOOGLE_API_KEY="your-key-here"

# Optional: change model (default: gemini-2.5-flash)
export MODEL="gemini-2.0-flash"
```

## Usage

### Option 1: ADK Web UI

```bash
cd gui_agent_adk
adk web
```

Then select `gui_agent` in the browser UI.

### Option 2: Programmatic

```bash
python run.py
```

## Structure

```
gui_agent_adk/
├── agent.py      # Agent definition (for adk web)
├── run.py        # Standalone runner
├── __init__.py   # Package init
└── pyproject.toml
```

## Available Tools

The Playwright MCP server provides:

- `browser_navigate` - Go to URL
- `browser_snapshot` - Get accessibility tree
- `browser_click` - Click elements
- `browser_type` - Type text
- `browser_screenshot` - Take screenshot

## Example Tasks

- "Navigate to google.com and search for 'ADK documentation'"
- "Go to news.ycombinator.com and tell me the top 3 stories"
- "Open wikipedia.org and search for 'artificial intelligence'"
