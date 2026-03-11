# MCP Tools — Test Suite (`tests/mcp_tools`)

Tests that call every qMetry MCP tool through the **live MCP protocol** —
the same path any MCP host (Claude Desktop, a custom agent, etc.) takes at
runtime.

> **Scope:** This suite tests the MCP server and its tools end-to-end.
> To test the `QMetryClient` REST wrapper directly, see `tests/qmetry_api/`.

---

## How It Works

```
pytest
  └── conftest.py spawns server.py as a subprocess (stdio transport)
        └── MCP ClientSession connects and initialises
              └── each test calls session.call_tool("tool_name", params)
                    └── server.py executes the tool → qMetry REST API → response
```

This exercises the **full stack**: tool name resolution, parameter
deserialisation, API call, JSON serialisation, and the MCP response envelope.

---

## Prerequisites

| Requirement | Detail |
|---|---|
| Python 3.11+ | https://python.org |
| All dependencies | `pip install -r requirements.txt` from `qmetry_mcp/` |
| `.env` configured | See below |

`requirements.txt` already includes `pytest-asyncio>=0.23.0` which is needed
for async test support.

---

## Quick Start (new instance)

### 1 — Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` — the only values you need to change per instance:

```env
QMETRY_API_KEY=your-actual-api-key
QMETRY_BASE_URL=https://qtmcloud.qmetry.com/rest/api/latest/

TEST_PROJECT_KEY=MYPROJECT       # Jira project key to test against
TEST_JIRA_ISSUE_KEY=MYPROJECT-1  # Any existing Jira issue (for requirements & pipeline tests)
```

### 2 — Run the full suite

```bash
# From the qmetry_mcp/ directory
python -m pytest tests/mcp_tools/ -v -s
```

### 3 — Verify in the qMetry UI

All artefacts created by these tests are prefixed `[MCP-TEST]` and can be
filtered in the qMetry interface.  Tests clean up via **archive** (soft-
delete) so artefacts stay visible for manual verification.

---

## Test File Overview

Tests are numbered so pytest runs them in dependency order.  Each file can
also run standalone — if a prerequisite ID is missing the test creates what it
needs or skips gracefully.

| File | Tools tested | What it creates |
|---|---|---|
| `test_00_connectivity.py` | `list_tools` (MCP meta) | Nothing |
| `test_01_projects_metadata.py` | `list_projects`, `list_labels`, `create_label`, `list_priorities`, `list_*_statuses` | 1 label |
| `test_02_folders.py` | `list_*_folders`, `create_*_folder` | 3 folders |
| `test_03_test_cases.py` | `create_test_case`, `get_test_case`, `search_test_cases`, `update_test_case`, `add_test_steps`, `get_test_steps`, `update_test_steps`, `clone_test_case`, `move_test_case`, `link/unlink_requirements_to_test_case`, `archive/unarchive_test_case` | 2 TCs |
| `test_04_test_cycles.py` | `create_test_cycle`, `get_test_cycle`, `search_test_cycles`, `update_test_cycle`, `link/unlink_test_cases_to_cycle`, `get_cycle_test_cases`, `link/unlink_requirements_to_cycle`, `archive/unarchive_test_cycle` | 2 cycles |
| `test_05_test_plans.py` | `create_test_plan`, `get_test_plan`, `search_test_plans`, `update_test_plan`, `link/unlink_cycles_to_test_plan`, `get_plan_test_cycles`, `archive/unarchive_test_plan` | 2 plans |
| `test_06_pipeline.py` | `publish_test_cases_from_story` | 2–3 TCs + 1 cycle |

**Total tools covered: all 47 registered tools** (29 domain tools + pipeline).

---

## Running Individual Files

```bash
# Connectivity only (no API calls — fastest check)
python -m pytest tests/mcp_tools/test_00_connectivity.py -v -s

# Test case tools only
python -m pytest tests/mcp_tools/test_03_test_cases.py -v -s

# Cycle + plan tools together
python -m pytest tests/mcp_tools/test_04_test_cycles.py tests/mcp_tools/test_05_test_plans.py -v -s

# Pipeline end-to-end (requires TEST_JIRA_ISSUE_KEY)
python -m pytest tests/mcp_tools/test_06_pipeline.py -v -s
```

## Running a Single Test

```bash
python -m pytest "tests/mcp_tools/test_03_test_cases.py::TestCreateTestCase::test_create_returns_id_and_key" -v -s
```

---

## What `test_00_connectivity.py` Validates

Before any API calls are made this file confirms:

| Check | Why it matters |
|---|---|
| `list_tools` returns all expected tool names | Catches a missing `register()` call in a new tools module |
| Every tool has a description | Ensures the MCP host (LLM) receives useful context for each tool |
| Every tool has an `inputSchema` | Required for the host to know what parameters to pass |

---

## Cross-File State

When the full suite runs together, later files reuse artefacts created by
earlier ones via a session-scoped `shared_state` dict (defined in
`conftest.py`):

```
test_02 creates folders
    └── test_03 creates TCs inside those folders
            └── test_04 links those TCs into a new cycle
                    └── test_05 links that cycle into a new plan
                            └── test_06 runs publish_test_cases_from_story
```

---

## Difference from `tests/qmetry_api/`

| | `tests/qmetry_api/` | `tests/mcp_tools/` |
|---|---|---|
| What is called | `QMetryClient` Python methods | `session.call_tool("name", params)` |
| Transport | Direct Python import | MCP stdio protocol (subprocess) |
| Validates tool names | No | Yes (`test_00_connectivity.py`) |
| Validates parameter names | No | Yes (wrong param → tool error) |
| Validates JSON string output | No | Yes (parses tool response) |
| Server startup tested | No | Yes |
| Test type | REST API layer | Full MCP stack |

---

## Switching to a Different Jira Instance

Update two values in `.env`:

```env
TEST_PROJECT_KEY=OTHERPROJECT
TEST_JIRA_ISSUE_KEY=OTHERPROJECT-5
```

Re-run the suite — everything else is discovered dynamically.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: server` | Not running from `qmetry_mcp/` | Run `python -m pytest` from the `qmetry_mcp/` directory |
| Server process exits immediately | Missing `QMETRY_API_KEY` | Check `.env` is present and loaded |
| `list_tools` missing a tool | `register()` not called in `tools/__init__.py` | Add the missing module to `register_all()` |
| Pipeline tests skipped | `TEST_JIRA_ISSUE_KEY` not set | Add a valid issue key to `.env` |
| `401 Unauthorized` on tool call | Expired API key | Regenerate from qMetry → Configuration → Open API |
| Async fixture errors | Wrong `pytest-asyncio` version | Ensure `pytest-asyncio>=0.23.0` is installed |
