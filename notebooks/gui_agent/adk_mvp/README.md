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
export GEMINI_API_KEY="your-key-here"

# Optional: change model (default: gemini-2.5-flash)
export MODEL="gemini-2.0-flash"
```

## Usage

### Option 1: ADK Web UI

```bash
cd notebooks/gui_agent/adk_mvp
adk web
```

Then select `gui_agent` in the browser UI.

### Option 2: Programmatic (Standalone)

```bash
cd notebooks/gui_agent/adk_mvp
python mvp_v1/run.py
```

Or use the virtual environment:
```bash
.venv/bin/python mvp_v1/run.py
```

## Structure

```
notebooks/gui_agent/adk_mvp/
├── mvp_v1/
│   ├── agent.py           # Agent factory (for adk web)
│   ├── run.py             # Standalone runner with timeout config
│   └── __init__.py        # Package exports
├── tests/
│   ├── conftest.py        # Pytest fixtures (MCP toolset, sessions)
│   ├── test_setup.py      # Environment validation tests (10 tests)
│   ├── test_tools.py      # MCP tool availability tests (6 tests)
│   └── test_behavioral.py # Agent behavioral tests (3 tests)
├── .env                   # Environment variables
├── pyproject.toml         # Project configuration
└── Claude.md              # Full project documentation
```

## Testing

The project includes comprehensive test coverage (19 tests total):

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_setup.py -v      # Environment/setup tests
pytest tests/test_tools.py -v      # MCP tool tests
pytest tests/test_behavioral.py -v # Agent behavioral tests

# Run a specific test
pytest tests/test_behavioral.py::test_search_wikipedia -v
```

Test categories:
- **Setup Tests** (10): Python version, imports, Node.js/npx, Playwright MCP, API keys
- **Tool Tests** (6): MCP toolset initialization, individual tool availability
- **Behavioral Tests** (3): Navigation, search interactions, error handling

See [Claude.md](Claude.md) for detailed test results and known issues.

## Available Tools

The Playwright MCP server provides 7 tools:

- `init-browser` - Initialize/navigate browser to URL
- `get-interactive-snapshot` - Get accessibility tree with interactive elements
- `get-screenshot` - Take visual screenshot of page
- `execute-code` - Execute Playwright code (click, type, etc.)
- `get-full-snapshot` - Get complete page snapshot
- `get-full-dom` - Get full DOM structure
- `get-text-snapshot` - Get text content snapshot

**Note:** MCP request timeout is configured to 120 seconds (2 minutes) to support complex multi-step interactions.

## Example Tasks

- "Navigate to google.com and search for 'ADK documentation'"
- "Go to news.ycombinator.com and tell me the top 3 stories"
- "Open wikipedia.org and search for 'artificial intelligence'"
