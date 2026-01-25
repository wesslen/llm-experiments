# GUI Agent - Google ADK + Microsoft Playwright MCP

## Project Overview

Minimal viable Google ADK GUI Agent using Microsoft's Playwright MCP server for browser automation. This project provides a foundation for building GUI automation agents with test-driven development.

**Status:** ✅ MVP v1 Complete + Enterprise Tests (25 total tests: 19 core + 6 enterprise)

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
   - Complex interactions: Wikipedia search with multi-step workflow ✅
   - Error handling for invalid URLs ✅
   - 3/3 behavioral tests passing

4. **Code Quality**
   - Resource leak fixes (proper MCP toolset cleanup)
   - 22 tracked failure modes (17 controlled, 5 uncontrolled)
   - Timeout controls (5 min task timeout, 50 iteration max)
   - Environment validation on startup
   - Type safety improvements
   - Enterprise behavioral tests with mock services

### Active Challenges

See [Unmitigated Failure Modes](#unmitigated-failure-modes--priorities) section for detailed prioritization.

**High Priority Uncontrolled Failures:**
1. **API Quota Exhausted** - No retry/backoff, blocks functionality
2. **Authentication Wall Handling** - No detection/guidance when login required
3. **Enterprise Behavioral Gaps** - Need agent improvements based on new test results

**Recently Resolved:**
- ✅ MCP Request Timeout (2026-01-24) - Added 120s timeout for complex interactions
- ✅ Basic behavioral test coverage - All 19 core tests passing
- ✅ Enterprise test framework - 6 behavioral tests with mock services created

## Quick Start

```bash
# 1. Navigate to project
cd notebooks/gui_agent/adk_mvp

# 2. Install dependencies
uv sync

# 3. Configure API key
echo "GEMINI_API_KEY=your-key-here" > .env

# 4. Run tests to verify setup
uv run pytest tests/test_setup.py -v

# 5. Try the agent
python mvp_v1/run.py
# or
adk web
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (for Playwright MCP)
- Google Gemini API key

### Installation

```bash
cd notebooks/gui_agent/adk_mvp

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Add your API key to .env
GEMINI_API_KEY=your-actual-api-key-here

# Optional: Override model (default: gemini-2.5-flash)
MODEL=gemini-2.0-flash
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
# Core tests (19/19 passing - 100%)
uv run pytest tests/ -v --ignore=tests/behavioral_enterprise

# All tests including enterprise (25 total)
uv run pytest tests/ -v

# Total: 25 tests
# - Setup: 10/10 ✅
# - Tools: 6/6 ✅
# - Behavioral (basic): 3/3 ✅
# - Behavioral (enterprise): 6 (3 CRM + 3 Dashboard)
```

### Test Categories

```bash
# Environment validation (10 tests)
uv run pytest tests/test_setup.py -v

# Tool availability (6 tests)
uv run pytest tests/test_tools.py -v

# Basic behavioral tests (3 tests)
uv run pytest tests/test_behavioral.py -v

# Enterprise behavioral tests (6 tests)
uv run pytest tests/behavioral_enterprise/ -v

# By enterprise use case
uv run pytest -m crm -v              # CRM Lead Entry (3 tests)
uv run pytest -m dashboard -v        # Dashboard Monitoring (3 tests)
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
- ✅ `test_search_wikipedia` - Wikipedia search (timeout after 60s)
- ✅ `test_agent_error_handling` - Invalid URL handling

**Enterprise Behavioral Tests** (`behavioral_enterprise/`):
- CRM Lead Entry (3 tests):
  - `test_crm_happy_path` - Create lead with all fields
  - `test_crm_validation_error` - Handle missing required field
  - `test_crm_duplicate_modal` - Detect duplicate contact modal
- Dashboard Monitoring (3 tests):
  - `test_dashboard_happy_path` - Extract metrics and apply thresholds
  - `test_dashboard_ajax_delay` - Handle AJAX loading with wait strategies
  - `test_dashboard_missing_metric` - Gracefully handle missing elements

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
├── evaluations/                # ADK evaluation test definitions
│   ├── crm_tests.evalset.json # CRM behavioral tests (3 cases)
│   └── dashboard_tests.evalset.json # Dashboard tests (3 cases)
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
    ├── test_behavioral.py      # Happy path scenarios (3 tests)
    └── behavioral_enterprise/  # Enterprise behavioral tests (6 tests)
        ├── __init__.py
        ├── README.md           # Enterprise test documentation
        ├── test_crm_lead_entry.py # CRM tests (3)
        ├── test_dashboard_monitoring.py # Dashboard tests (3)
        └── mocks/              # Mock web services
            ├── mock_crm.html   # HubSpot simulator
            └── mock_dashboard.html # Grafana simulator
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

### Failure Modes

Tracked failure modes for monitoring and prioritization during updates:

#### Core Failure Modes (Original 10)

| # | Failure Mode | Description | Controlled | Severity |
|---|--------------|-------------|------------|----------|
| 1 | MCP Request Timeout | MCP calls timeout on complex interactions | Controlled (test + 120s config) | High |
| 2 | API Quota Exhausted | Gemini API rate limit exceeded | Uncontrolled | High |
| 3 | Missing API Key | GEMINI_API_KEY not set or invalid | Controlled (test + validation) | High |
| 4 | MCP Toolset Init Failure | Playwright MCP server fails to start | Controlled (test) | High |
| 5 | Invalid URL Navigation | Agent navigates to non-existent domain | Controlled (test) | Medium |
| 6 | Task Timeout | Agent exceeds 5 min execution limit | Controlled (300s config) | Medium |
| 7 | Resource Leak | MCP process not terminated properly | Controlled (finally blocks) | Medium |
| 8 | Max Iterations Exceeded | Agent hits 50 iteration loop limit | Controlled (config) | Medium |
| 9 | ADK Deprecation | Using deprecated MCPTool class | Uncontrolled (warnings) | Low |
| 10 | Keyboard Interrupt | User cancels during execution | Controlled (handler) | Low |

#### Enterprise Failure Modes (New - 12 additional)

| # | Failure Mode | Description | Test Coverage | Severity |
|---|--------------|-------------|---------------|----------|
| 11 | Form Validation Error Detection | Agent fails to detect inline validation errors | CRM validation test | High |
| 12 | Modal Dialog Perception | Agent doesn't recognize modal overlays | CRM duplicate test | High |
| 13 | Dynamic Content Wait Failure | Agent interacts before AJAX content loads | Dashboard AJAX test | High |
| 14 | Missing Element Graceful Failure | Agent crashes instead of reporting missing elements | Dashboard missing metric test | Medium |
| 15 | Data Extraction Accuracy | Agent misreads/misinterprets displayed values | Dashboard happy path | High |
| 16 | Threshold Logic Errors | Agent fails to correctly apply comparison logic | Dashboard happy path | Medium |
| 17 | Multi-Step Form State Loss | Agent loses context between form pages | CRM happy path | Medium |
| 18 | Dropdown/Select Element Handling | Agent can't interact with custom dropdowns | CRM happy path | Medium |
| 19 | Wait Strategy Selection | Agent uses fixed delays instead of smart waits | Dashboard AJAX test | Medium |
| 20 | Error Communication Clarity | Agent doesn't clearly communicate blockers to user | CRM validation test | Medium |
| 21 | Success Verification | Agent reports success without verifying completion | Both happy paths | Medium |
| 22 | Authentication Wall Handling | Agent doesn't detect/communicate auth requirements | Uncontrolled (future test) | High |

**Summary:**
- **Total Tracked:** 22 failure modes
- **Controlled:** 17 (77%)
- **Uncontrolled:** 5 (23%)
- **High Severity:** 9
- **Medium Severity:** 12
- **Low Severity:** 1

**Legend:**
- **Controlled**: Failure mode has automated test coverage or explicit handling
- **Uncontrolled**: Failure mode occurs but not explicitly tested or handled
- **Severity**: High (blocks core functionality), Medium (degrades experience), Low (minor impact)

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

## Unmitigated Failure Modes & Priorities

### High Priority (Uncontrolled High-Severity Failures)

1. **API Quota Exhausted** (Failure Mode #2)
   - **Status:** Uncontrolled
   - **Impact:** Blocks all agent functionality when Gemini API rate limit exceeded
   - **Next Steps:**
     - Implement exponential backoff retry logic
     - Add quota monitoring and alerting
     - Graceful degradation with clear user messaging

2. **Authentication Wall Handling** (Failure Mode #22)
   - **Status:** Uncontrolled (no test coverage)
   - **Impact:** Agent cannot proceed with tasks requiring login
   - **Next Steps:**
     - Add enterprise test for auth wall detection
     - Implement auth wall recognition patterns
     - Provide clear guidance to user (credentials needed, session required)

3. **Enterprise Failure Modes** (11-21)
   - **Status:** Tests created but agent improvements needed
   - **Impact:** Form validation, modal detection, data extraction may fail
   - **Next Steps:**
     - Run enterprise tests to establish baseline
     - Analyze failure patterns
     - Improve agent instructions for wait strategies, error detection

### Medium Priority

1. **ADK Deprecation Warnings** (Failure Mode #9)
   - **Status:** Uncontrolled, Low Severity
   - **Impact:** May break in future ADK versions
   - **Next Steps:** Migrate from `MCPTool` to `McpTool` when convenient

## Future Enhancements

### v2: Enterprise Readiness

1. **Address Uncontrolled Failure Modes**
   - Implement API quota retry/backoff logic (Failure Mode #2)
   - Add authentication wall detection and handling (Failure Mode #22)
   - Improve agent instructions based on enterprise test results

2. **Advanced Interactions** (Based on Enterprise Test Insights)
   - Smart wait strategies for AJAX/dynamic content (not fixed delays)
   - Modal and overlay detection improvements
   - Form validation error parsing and recovery
   - Multi-page workflow state management
   - File upload/download support

3. **Enhanced Error Recovery**
   - Better error message communication to users
   - Graceful degradation when elements missing
   - Success verification before reporting completion
   - Retry logic for transient failures

4. **Testing Expansion**
   - Add 7 more enterprise edge cases (auth wall, network errors, file uploads)
   - Real service integration tests (HubSpot, Grafana with credentials)
   - Visual regression testing (screenshot comparisons)
   - Performance benchmarking suite

5. **Observability & Debugging**
   - Structured logging with trace IDs
   - Screenshot artifacts on test failures
   - Tool call execution metrics
   - Cost tracking per task

### v3: Production Scale

1. **Robustness**
   - Circuit breakers for API failures
   - Health checks and self-healing
   - Comprehensive retry mechanisms
   - Fallback strategies

2. **Scalability**
   - Parallel browser session management
   - Task queuing and scheduling
   - Resource pooling
   - Horizontal scaling support

3. **Monitoring**
   - Real-time metrics dashboard
   - Error tracking (Sentry integration)
   - API cost monitoring
   - Usage analytics and reporting

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

- [README.md](README.md) - Quick start guide
- [ENTERPRISE_TESTS_SUMMARY.md](ENTERPRISE_TESTS_SUMMARY.md) - Enterprise test implementation details
- [tests/behavioral_enterprise/README.md](tests/behavioral_enterprise/README.md) - Enterprise test usage guide
- [.env.example](.env.example) - Environment template
- [pyproject.toml](pyproject.toml) - Dependencies and config

## Change Log

### 2026-01-24 (Update) - Enterprise Behavioral Tests

**Added:**
- Enterprise behavioral test suite (6 tests across 2 use cases)
- CRM Lead Entry tests (3): form validation, modal detection, multi-step workflows
- Dashboard Monitoring tests (3): data extraction, AJAX handling, threshold logic
- Mock web services (mock_crm.html, mock_dashboard.html)
- ADK evaluation definitions (crm_tests.evalset.json, dashboard_tests.evalset.json)
- Pytest markers for enterprise tests (enterprise, crm, dashboard)
- 12 new tracked failure modes (total: 22, 77% controlled)

**Changed:**
- Reorganized documentation to focus on unmitigated failures and future work
- Removed completed "Fix Wikipedia timeout" from Next Steps
- Updated README.md with enterprise test information
- Updated file structure to include evaluations/ folder

**Documentation:**
- Added ENTERPRISE_TESTS_SUMMARY.md
- Added behavioral_enterprise/README.md
- Updated failure mode tracking (22 total, 17 controlled, 5 uncontrolled)
- Reorganized Next Steps to "Unmitigated Failure Modes & Priorities"

### 2026-01-24 - MCP Timeout Fix & Failure Modes

**Fixed:**
- MCP request timeout (added `timeout=120` to all `McpToolset` instances)
- All 19 core tests now passing (100%)

**Changed:**
- Added 10 tracked failure modes (7 controlled, 3 uncontrolled)
- Reframed error handling to failure mode tracking

### 2026-01-24 - MVP v1 Complete

**Added:**
- Complete test suite (19 tests)
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
- ADK deprecation warnings (MCPTool → McpTool)

---

**Last Updated:** 2026-01-24
**Version:** v1.0
**Status:** MVP Complete - Ready for Development
