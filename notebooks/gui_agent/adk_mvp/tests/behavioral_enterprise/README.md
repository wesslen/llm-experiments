# Enterprise Behavioral Tests

Comprehensive behavioral test suite for the GUI agent, focusing on enterprise automation use cases. These tests evaluate the agent's ability to handle real-world workflows with both happy paths and edge cases.

## Overview

**Purpose:** Find failure modes in the GUI agent by testing realistic enterprise scenarios
**Approach:** Mock web services + ADK evaluation format + pytest runners
**Scope:** 6 tests across 2 use cases (CRM Lead Entry + Dashboard Monitoring)

## Test Structure

```
adk_mvp/
├── evaluations/                        # ADK evaluation test definitions (project root)
│   ├── crm_tests.evalset.json         # 3 CRM test cases
│   └── dashboard_tests.evalset.json   # 3 dashboard test cases
└── tests/
    └── behavioral_enterprise/
        ├── mocks/                      # Mock web services
        │   ├── mock_crm.html          # Simulates HubSpot CRM
        │   └── mock_dashboard.html    # Simulates Grafana dashboard
        ├── test_crm_lead_entry.py     # Pytest runner for CRM tests
        ├── test_dashboard_monitoring.py # Pytest runner for dashboard tests
        └── README.md                   # This file
```

## Use Cases

### 1. CRM Lead Entry (3 tests)

Simulates enterprise sales automation - creating leads in CRM systems like HubSpot.

**Tests:**
1. **Happy Path** - Successfully create lead with all fields
2. **Form Validation** - Handle missing required field (email)
3. **Duplicate Modal** - Detect and communicate duplicate contact warning

**Failure Modes Tested:**
- Form Validation Error Detection
- Modal Dialog Perception
- Error Communication Clarity
- Multi-Step Form State Management
- Dropdown/Select Element Handling

### 2. Dashboard Monitoring (3 tests)

Simulates DevOps automation - extracting metrics and detecting anomalies from monitoring dashboards.

**Tests:**
1. **Happy Path** - Extract metrics and apply threshold logic
2. **AJAX Delay** - Handle dynamic content loading with proper wait strategies
3. **Missing Element** - Gracefully handle metric not found

**Failure Modes Tested:**
- Data Extraction Accuracy
- Threshold Logic Errors
- Dynamic Content Wait Failure
- Missing Element Graceful Failure
- Wait Strategy Selection

## Running Tests

### All Enterprise Tests

```bash
cd /Users/ryan/projects/llm-experiments/notebooks/gui_agent/adk_mvp
uv run pytest tests/behavioral_enterprise/ -v
```

### By Use Case

```bash
# CRM tests only
uv run pytest tests/behavioral_enterprise/test_crm_lead_entry.py -v

# Dashboard tests only
uv run pytest tests/behavioral_enterprise/test_dashboard_monitoring.py -v
```

### By Marker

```bash
# All enterprise tests
uv run pytest -m enterprise -v

# CRM-specific tests
uv run pytest -m crm -v

# Dashboard-specific tests
uv run pytest -m dashboard -v
```

### With Full Output

```bash
# See agent responses and tool calls
uv run pytest tests/behavioral_enterprise/ -v -s
```

### Single Test

```bash
# Run specific test function
uv run pytest tests/behavioral_enterprise/test_crm_lead_entry.py::test_crm_happy_path -v -s
```

## Test Configuration

### Prerequisites

- Python 3.12+
- Google Gemini API key (`GEMINI_API_KEY` environment variable)
- All dependencies installed (`uv sync` or `pip install -e .`)

### Environment Setup

```bash
# Ensure .env file exists with API key
echo "GEMINI_API_KEY=your-key-here" > .env

# Optional: Override model
echo "MODEL=gemini-2.5-flash" >> .env
```

### Skip Conditions

Tests automatically skip if:
- `GEMINI_API_KEY` starts with `"test-"` (prevents accidental API charges)
- MCP toolset initialization fails
- Required dependencies are missing

## Mock Services

### Mock CRM ([mock_crm.html](mocks/mock_crm.html))

**Simulates:** HubSpot contact creation interface

**Features:**
- Contact creation form with fields: firstname, lastname, email, company, phone, jobtitle
- Lead status dropdown (New, Open, In Progress, etc.)
- Form validation (email required)
- Duplicate detection (sarah.johnson@techcorp.com triggers modal)
- Success/error messages

**Pre-loaded Data:**
- Existing contact: Sarah Johnson (sarah.johnson@techcorp.com)

### Mock Dashboard ([mock_dashboard.html](mocks/mock_dashboard.html))

**Simulates:** Grafana production metrics dashboard

**Features:**
- 4 metrics: CPU Usage, Memory Usage, Error Rate, Request Latency
- AJAX loading simulation (2-second delay)
- Loading spinner → actual values
- Metric trends and health indicators

**Metrics:**
- CPU Usage: 67.3%
- Memory Usage: 58.9%
- Error Rate: 2.4%
- Request Latency: 245ms (p95)

## Evaluation Criteria

Tests use ADK-style evaluation with custom assertions:

### Tool Trajectory Matching

**Threshold:** 85% match (0.85)
**Method:** In-order matching (allows extra tools between expected calls)

Expected tool sequences are defined in `.evalset.json` files.

### Response Quality

**Threshold:** 70% semantic similarity (0.7)
**Method:** Keyword matching + content validation

Expected response content defined per test case.

### Custom Criteria

- **Error Detection Score:** 1.0 for validation/modal tests
- **Data Extraction Accuracy:** 1.0 for dashboard tests
- **Wait Strategy Score:** 1.0 for AJAX handling tests

## Expected Test Results

### Initial Run (Before Agent Improvements)

**Expected Pass Rate:** 60-80%

These tests are designed to find failure modes, so some initial failures are expected:
- Agent may not use optimal wait strategies
- Modal detection may fail
- Data extraction may be inaccurate
- Threshold logic may have errors

### After Agent Improvements

**Target Pass Rate:** 95%+

With agent improvements addressing discovered failure modes.

## Test Output

### Successful Test

```
[Test] Successfully create CRM lead with all fields
[Task] Navigate to http://localhost:PORT/mock_crm.html. Then create lead...
[Tool Calls] ['init-browser', 'get-interactive-snapshot', 'execute-code', ...]
[Response] Successfully created new lead for Sarah Martinez...
[Result] ✅ Test passed - Agent successfully created CRM lead
```

### Failed Test

```
[Test] Handle form validation error
[Task] Create lead without email...
[Tool Calls] ['init-browser', 'execute-code']
[Response] Lead created successfully
AssertionError: Agent incorrectly reported success despite validation error
```

## Failure Modes Tracked

These tests cover 12 new failure modes beyond the 10 already tracked in the main test suite:

| # | Failure Mode | Test Coverage | Severity |
|---|--------------|---------------|----------|
| 11 | Form Validation Error Detection | CRM validation test | High |
| 12 | Modal Dialog Perception | CRM duplicate test | High |
| 13 | Dynamic Content Wait Failure | Dashboard AJAX test | High |
| 14 | Missing Element Graceful Failure | Dashboard missing metric | Medium |
| 15 | Data Extraction Accuracy | Dashboard happy path | High |
| 16 | Threshold Logic Errors | Dashboard happy path | Medium |
| 17 | Multi-Step Form State Loss | CRM happy path | Medium |
| 18 | Dropdown/Select Element Handling | CRM happy path | Medium |
| 19 | Wait Strategy Selection | Dashboard AJAX test | Medium |
| 20 | Error Communication Clarity | CRM validation test | Medium |
| 21 | Success Verification | Both happy paths | Medium |
| 22 | Network Error Handling | Future expansion | Medium |

**Total Tracked:** 22 failure modes (10 existing + 12 new)
**Controlled:** 17/22 (77% coverage)

## Debugging

### View Agent Logs

```bash
# Full output with print statements
uv run pytest tests/behavioral_enterprise/ -v -s
```

### Inspect Tool Calls

Tool calls are printed during test execution:
```python
print(f"\n[Tool Calls] {tool_names}")
# Output: ['init-browser', 'get-interactive-snapshot', 'execute-code', ...]
```

### Check Agent Responses

```python
print(f"[Response] {combined_response[:200]}...")
# Output: Successfully created new lead for Sarah Martinez...
```

### Debug Single Test

```bash
# Run with Python debugger
uv run pytest tests/behavioral_enterprise/test_crm_lead_entry.py::test_crm_happy_path --pdb
```

### Manually Test Mock Services

```bash
# Start HTTP server
cd tests/behavioral_enterprise/mocks
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/mock_crm.html
open http://localhost:8000/mock_dashboard.html
```

## Adding New Tests

### 1. Add Test Case to Evalset

Edit `evaluations/crm_tests.evalset.json` or `evaluations/dashboard_tests.evalset.json`:

```json
{
  "test_id": "new_test",
  "name": "Test description",
  "user_task": "What agent should do",
  "expected_tool_trajectory": [...],
  "expected_response_contains": [...]
}
```

### 2. Add Pytest Function

Add to appropriate test file:

```python
@pytest.mark.asyncio
@pytest.mark.enterprise
@pytest.mark.crm  # or @pytest.mark.dashboard
async def test_new_scenario(crm_runner, test_session, mock_http_server):
    """Test description."""
    test_case = next(t for t in TEST_SPEC["test_cases"] if t["test_id"] == "new_test")
    # ... rest of test implementation
```

### 3. Update Mock HTML (if needed)

Modify `mocks/mock_crm.html` or `mocks/mock_dashboard.html` to add new scenarios.

## Known Limitations

1. **Mock Services:** Simplified HTML, not full CRM/Dashboard implementations
2. **API Costs:** Tests make real Gemini API calls
3. **Network Dependency:** Requires agent to be able to reach localhost
4. **Timing:** AJAX delays are fixed (2s), real systems vary
5. **Determinism:** Agent behavior may vary between runs

## Future Enhancements

### Additional Test Cases (Out of Current Scope)

1. Authentication wall handling
2. Network error scenarios
3. Browser crash recovery
4. File upload interactions
5. Multi-page workflows
6. JavaScript-heavy SPAs
7. Visual regression testing

### Real Service Integration

After mock tests prove valuable:
- Add optional real HubSpot tests (with credentials)
- Add optional real Grafana tests (with credentials)
- Gate behind environment flags

### Performance Benchmarking

- Track test execution time trends
- Detect performance regressions
- Measure API call efficiency

## Contributing

When adding tests, ensure:
1. Test spec added to appropriate `.evalset.json` file
2. Pytest function added with proper markers
3. Mock service updated if new UI elements needed
4. README updated with new test description
5. Failure modes table updated in main `Claude.md`

## References

- [ADK Evaluation Docs](https://google.github.io/adk-docs/evaluate/)
- [Main Test Suite](../README.md)
- [Project Documentation](../../Claude.md)
- [Mock CRM Service](mocks/mock_crm.html)
- [Mock Dashboard Service](mocks/mock_dashboard.html)

---

**Last Updated:** 2026-01-24
**Test Count:** 6 (3 CRM + 3 Dashboard)
**Status:** Ready for Execution
