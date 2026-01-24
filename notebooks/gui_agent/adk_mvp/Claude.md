# GUI Agent - Google ADK + Microsoft Playwright MCP

## Project Overview

Minimal viable Google ADK GUI Agent using Microsoft's Playwright MCP server for browser automation. This project provides a foundation for building GUI automation agents with test-driven development.

**Status:** ✅ MVP v1 Complete (18/19 tests passing - 94.7%)

**Production Constraint:** Microsoft's `playwright-mcp` is the only approved MCP server for production use.

## Architecture

```
┌─────────────────────┐
│  Google ADK Agent   │
│  (Gemini 2.5 Flash) │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   McpToolset        │
│  (ADK Integration)  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  playwright-mcp     │
│  (Microsoft MCP)    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│    Playwright       │
│  (Browser Control)  │
└─────────────────────┘
```

## Current State

### Working Features ✅

1. **Environment Validation**
   - Python 3.12+ verification
   - Node.js/npx availability checks
   - GEMINI_API_KEY validation
   - Package dependency verification
   - 10/10 setup tests passing

2. **Tool Integration**
   - Microsoft playwright-mcp package integration
   - All 7 MCP tools available and verified:
     - `init-browser` - Navigate to URLs
     - `get-interactive-snapshot` - Accessibility tree
     - `get-full-snapshot` - Complete page snapshot
     - `get-full-dom` - Full DOM
     - `get-text-snapshot` - Text content
     - `get-screenshot` - Screenshots
     - `execute-code` - Playwright code execution
   - 6/6 tool availability tests passing

3. **Agent Capabilities**
   - Navigation to websites
   - Page structure understanding via accessibility trees
   - Screenshot capture
   - Code execution for interactions (clicks, typing, etc.)
   - Basic happy path: Navigate and describe pages ✅
   - Error handling for invalid URLs ✅

4. **Code Quality**
   - Resource leak fixes (proper MCP toolset cleanup)
   - Comprehensive error handling
   - Timeout controls (5 min task timeout, 50 iteration max)
   - Environment validation on startup
   - Type safety improvements

### Known Issues ⚠️

1. **Complex Interaction Timeout** (1 test failing)
   - `test_search_wikipedia` times out during execute-code operations
   - MCP request timeout after 5 seconds during complex interactions
   - Agent successfully completes: init-browser → get-interactive-snapshot → execute-code → get-interactive-snapshot
   - Timeout occurs on subsequent MCP tool call
   - **Impact:** Complex multi-step interactions may fail
   - **Workaround:** Break complex tasks into simpler steps

2. **ADK Deprecation Warnings**
   - `MCPTool` class deprecated (use `McpTool` instead)
   - Experimental feature warnings for `BASE_AUTHENTICATED_TOOL`
   - **Impact:** None currently, but may break in future ADK versions

## Setup

### Prerequisites

```bash
# System requirements
- Python 3.12+
- Node.js 18+
- npm/npx
- Google Gemini API key
```

### Installation

```bash
cd notebooks/gui_agent/adk_mvp

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
GEMINI_API_KEY=your-actual-api-key-here

# Optional: Override model (default: gemini-2.5-flash)
# MODEL=gemini-2.0-flash
```

## Usage

### Option 1: Standalone Runner

```bash
cd notebooks/gui_agent/adk_mvp
python mvp_v1/run.py

# Interactive prompt appears:
# Enter task (or press Enter for demo):
```

**Example tasks:**
- "Navigate to example.com and tell me what you see"
- "Go to wikipedia.org and find information about Python"
- "Visit github.com and describe the homepage"

### Option 2: ADK Web UI

```bash
cd notebooks/gui_agent/adk_mvp
adk web

# Browser opens - select "gui_agent" from the agent list
```

### Programmatic Usage

```python
import asyncio
from mvp_v1.agent import create_gui_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def run_automation():
    # Create agent
    agent = create_gui_agent()

    # Setup session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="my_app", user_id="user"
    )

    # Create runner
    runner = Runner(
        app_name="my_app",
        agent=agent,
        session_service=session_service
    )

    # Execute task
    task = "Navigate to example.com and describe what you see"
    content = types.Content(role="user", parts=[types.Part(text=task)])

    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"Agent: {part.text}")

asyncio.run(run_automation())
```

## Testing

### Run All Tests

```bash
# All tests (18/19 passing)
uv run pytest tests/ -v

# Total: 19 tests
# - Setup: 10/10 ✅
# - Tools: 6/6 ✅
# - Behavioral: 2/3 ✅ (1 timeout)
```

### Test Categories

```bash
# Environment validation (10 tests)
uv run pytest tests/test_setup.py -v

# Tool availability (6 tests)
uv run pytest tests/test_tools.py -v

# End-to-end behavioral (3 tests)
uv run pytest tests/test_behavioral.py -v
```

### Test Details

**Setup Tests** (`test_setup.py`):
- ✅ `test_python_version` - Python 3.12+
- ✅ `test_required_imports` - google-adk, mcp, python-dotenv
- ✅ `test_dev_imports` - pytest, pytest-asyncio
- ✅ `test_nodejs_available` - Node.js 18+
- ✅ `test_npx_available` - npx command
- ✅ `test_playwright_mcp_package` - playwright-mcp@latest
- ✅ `test_gemini_api_key_set` - GEMINI_API_KEY exists
- ✅ `test_gemini_api_key_format` - API key format validation
- ✅ `test_adk_basic_init` - LlmAgent instantiation
- ✅ `test_model_env_var` - MODEL env var validation

**Tool Tests** (`test_tools.py`):
- ✅ `test_all_tools_available` - 7 tools from Microsoft's playwright-mcp
- ✅ `test_init_browser_available` - init-browser tool
- ✅ `test_interactive_snapshot_available` - get-interactive-snapshot tool
- ✅ `test_screenshot_available` - get-screenshot tool
- ✅ `test_execute_code_available` - execute-code tool
- ✅ `test_mcp_toolset_initialization` - MCP toolset creation

**Behavioral Tests** (`test_behavioral.py`):
- ✅ `test_navigate_and_describe` - Navigate to example.com and describe (12.8s)
- ⚠️ `test_search_wikipedia` - Wikipedia search (timeout after 60s)
- ✅ `test_agent_error_handling` - Invalid URL handling

## File Structure

```
notebooks/gui_agent/adk_mvp/
├── .env.example                 # Environment template
├── .python-version              # Python 3.12
├── pyproject.toml              # Project dependencies + pytest config
├── uv.lock                     # Dependency lock file
├── README.md                   # Project README
├── Claude.md                   # This file
├── main.py                     # Entry point (placeholder)
│
├── mvp_v1/                     # Version 1 implementation
│   ├── __init__.py
│   ├── agent.py                # Agent definition (for adk web)
│   │                           # - validate_environment()
│   │                           # - create_gui_agent()
│   │                           # - root_agent (for adk web)
│   └── run.py                  # Standalone runner
│                               # - create_agent()
│                               # - run_task()
│                               # - main()
│
└── tests/                      # Test suite (pytest)
    ├── __init__.py
    ├── conftest.py             # Shared fixtures
    │                           # - mcp_toolset
    │                           # - session_service
    │                           # - test_session
    ├── test_setup.py           # Environment validation (10 tests)
    ├── test_tools.py           # Tool availability (6 tests)
    └── test_behavioral.py      # Happy path scenarios (3 tests)
```

## Key Implementation Details

### Microsoft Playwright MCP Tools

The agent uses Microsoft's `playwright-mcp@latest` package which provides 7 tools:

1. **init-browser** (required first step)
   - Initializes browser and navigates to URL
   - Parameters: `{ url: string }`
   - Returns: Page state with accessibility snapshot

2. **get-interactive-snapshot**
   - Returns accessibility tree with interactive elements
   - Best for understanding page structure
   - Parameters: `{}`

3. **get-full-snapshot**
   - Complete page snapshot
   - Parameters: `{}`

4. **get-full-dom**
   - Full DOM structure
   - Parameters: `{}`

5. **get-text-snapshot**
   - Text content only
   - Parameters: `{}`

6. **get-screenshot**
   - Visual screenshot of page
   - Parameters: `{ name?: string, fullPage?: boolean }`

7. **execute-code**
   - Execute Playwright code for interactions
   - Parameters: `{ code: string }` (Playwright JavaScript)
   - Used for: clicks, typing, form submission, navigation

### Agent Workflow

1. **init-browser** - Navigate to target URL (required)
2. **get-interactive-snapshot** - Understand page structure
3. **execute-code** - Perform interactions (optional)
4. **get-screenshot** - Visual confirmation (optional)
5. Return completion status

### Resource Management

```python
# MCP toolset is properly cleaned up
async def create_agent():
    toolset = McpToolset(...)
    agent = LlmAgent(..., tools=[toolset])
    return agent, toolset

async def run_task(task: str):
    agent, toolset = await create_agent()
    try:
        # Run agent
        ...
    finally:
        await toolset.close()  # Critical: prevents resource leaks
```

### Error Handling

- **GEMINI_API_KEY validation** on startup
- **Timeout controls**: 5 min task timeout, 50 iteration max
- **MCP connection errors** caught and reported
- **Invalid URLs** handled gracefully
- **Keyboard interrupts** handled cleanly

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-key-here

# Optional
MODEL=gemini-2.5-flash  # Default model
```

### Pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

## Next Steps / Future Work

### Immediate (v1 fixes)

1. **Fix Wikipedia test timeout**
   - Increase MCP request timeout from 5s
   - Add retry logic for execute-code operations
   - Better error messages for MCP timeouts

2. **Address deprecation warnings**
   - Migrate from `MCPTool` to `McpTool`
   - Handle experimental feature flags properly

### v2 Enhancements

1. **Advanced Interactions**
   - Form filling helpers
   - Multi-page workflows
   - Authentication handling
   - File uploads/downloads

2. **Improved Observability**
   - Structured logging
   - Tool call tracing
   - Screenshot artifacts on failure
   - Performance metrics

3. **Testing Improvements**
   - Mock MCP responses for faster unit tests
   - More complex interaction scenarios
   - Visual regression testing
   - Performance benchmarks

4. **Agent Improvements**
   - Better error recovery
   - State persistence between tasks
   - Multi-tab management
   - Wait strategies for dynamic content

5. **Tool Filtering**
   - Enable optional tool_filter in McpToolset
   - Reduce API calls by limiting available tools
   - Tool-specific configurations

### v3+ (Production Ready)

1. **Robustness**
   - Retry mechanisms
   - Circuit breakers
   - Rate limiting
   - Health checks

2. **Scalability**
   - Parallel browser sessions
   - Task queuing
   - Resource pooling
   - Horizontal scaling

3. **Monitoring**
   - Metrics dashboard
   - Error tracking (Sentry, etc.)
   - Cost tracking
   - Usage analytics

## Troubleshooting

### Common Issues

**Issue:** `GEMINI_API_KEY environment variable is not set`
```bash
# Solution: Create .env file with API key
echo "GEMINI_API_KEY=your-key-here" > .env
```

**Issue:** `npx command not found`
```bash
# Solution: Install Node.js
brew install node  # macOS
# or download from https://nodejs.org
```

**Issue:** `playwright-mcp package not found`
```bash
# Solution: Package will auto-install on first run
# Or manually install: npm install -g playwright-mcp
```

**Issue:** `MCP Server started. Port 5174 is in use`
```bash
# This is normal - playwright-mcp manages its own port
# The warning can be ignored
```

**Issue:** Tests timeout
```bash
# Solution: Increase timeout or skip slow tests
uv run pytest tests/ -v --timeout=180
uv run pytest tests/ -v -m "not slow"
```

### Debug Mode

```bash
# Run tests with verbose output
uv run pytest tests/ -v -s

# Run single test with full output
uv run pytest tests/test_behavioral.py::test_navigate_and_describe -v -s

# Run with Python debugger
uv run pytest tests/ --pdb
```

## References

### Documentation

- [Google ADK Docs](https://github.com/google/adk)
- [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Gemini API](https://ai.google.dev/)

### Related Files

- [README.md](README.md) - Project README
- [.env.example](.env.example) - Environment template
- [pyproject.toml](pyproject.toml) - Dependencies and config

## Change Log

### 2026-01-24 - MVP v1 Complete

**Added:**
- Complete test suite (19 tests, 18 passing)
- Environment validation (10 tests)
- Tool availability tests (6 tests)
- Behavioral tests (3 tests)
- Comprehensive error handling
- Resource leak fixes
- Timeout controls
- GEMINI_API_KEY validation

**Fixed:**
- MCP toolset resource leak
- Package name (playwright-mcp vs @anthropic/playwright-mcp)
- Tool names for Microsoft's implementation
- Async/sync fixture scoping issues
- Type import compatibility
- Function call attribute access

**Changed:**
- Migrated to Microsoft's playwright-mcp (production approved)
- Updated all tool names to Microsoft's API
- Agent instructions updated for new tool workflow
- Test strategy: structural validation + behavioral integration

**Known Issues:**
- Complex interaction timeout (test_search_wikipedia)
- ADK deprecation warnings (MCPTool → McpTool)

---

**Last Updated:** 2026-01-24
**Version:** v1.0
**Status:** MVP Complete - Ready for Development
