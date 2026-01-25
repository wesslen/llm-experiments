# GUI Agent (Google ADK + Playwright MCP)

Production-ready GUI automation agent using Google ADK with Microsoft's Playwright MCP server. Includes comprehensive test suite with enterprise behavioral tests for finding and mitigating failure modes.

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
├── evaluations/                        # ADK evaluation test definitions
│   ├── crm_tests.evalset.json         # CRM behavioral tests
│   └── dashboard_tests.evalset.json   # Dashboard monitoring tests
├── mvp_v1/
│   ├── agent.py                       # Agent factory (for adk web)
│   ├── run.py                         # Standalone runner
│   └── __init__.py
├── tests/
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_setup.py                  # Environment tests (10)
│   ├── test_tools.py                  # Tool availability tests (6)
│   ├── test_behavioral.py             # Basic behavioral tests (3)
│   └── behavioral_enterprise/         # Enterprise tests (6)
│       ├── test_crm_lead_entry.py     # CRM automation (3)
│       ├── test_dashboard_monitoring.py # Metric extraction (3)
│       └── mocks/                      # Mock web services
├── .env.example                       # Environment template
├── pyproject.toml                     # Project configuration
├── Claude.md                          # Full documentation
└── ENTERPRISE_TESTS_SUMMARY.md        # Test implementation summary
```

## Testing

Comprehensive test suite with **25 tests** across 4 categories:

```bash
# Run all tests (core + enterprise)
uv run pytest tests/ -v

# Core tests only (19 tests)
uv run pytest tests/ -v --ignore=tests/behavioral_enterprise

# Enterprise behavioral tests (6 tests)
uv run pytest tests/behavioral_enterprise/ -v

# By category
uv run pytest tests/test_setup.py -v       # Environment (10)
uv run pytest tests/test_tools.py -v       # Tools (6)
uv run pytest tests/test_behavioral.py -v  # Basic behavioral (3)

# By enterprise use case
uv run pytest -m crm -v                    # CRM automation (3)
uv run pytest -m dashboard -v              # Dashboard monitoring (3)
```

### Test Categories

1. **Setup Tests** (10): Python 3.12+, Node.js, API keys, dependencies
2. **Tool Tests** (6): MCP toolset initialization, tool availability
3. **Basic Behavioral Tests** (3): Navigation, search, error handling
4. **Enterprise Behavioral Tests** (6):
   - CRM Lead Entry: Form validation, modal detection, multi-step workflows
   - Dashboard Monitoring: Data extraction, AJAX handling, threshold logic

### Tracked Failure Modes

**22 failure modes** tracked (17 controlled, 5 uncontrolled):
- Core infrastructure: MCP timeouts, API quotas, resource leaks
- Enterprise scenarios: Form validation, modal perception, data extraction, wait strategies

See [Claude.md](Claude.md) for complete failure mode tracking and [ENTERPRISE_TESTS_SUMMARY.md](ENTERPRISE_TESTS_SUMMARY.md) for enterprise test details.

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

**Basic Navigation:**
- "Navigate to google.com and search for 'ADK documentation'"
- "Go to news.ycombinator.com and tell me the top 3 stories"
- "Open wikipedia.org and search for 'artificial intelligence'"

**Enterprise Automation** (tested in behavioral_enterprise/):
- "Create a CRM lead with name, email, and company"
- "Extract CPU and memory metrics from the dashboard"
- "Check if error rate exceeds 5% threshold"

## Key Features

- ✅ 100% test coverage for core functionality (19/19 passing)
- ✅ Enterprise behavioral tests for failure mode discovery
- ✅ 120-second MCP timeout for complex interactions
- ✅ 22 tracked failure modes (77% controlled)
- ✅ Mock services for reproducible testing
- ✅ ADK evaluation format for structured testing
