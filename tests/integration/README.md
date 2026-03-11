# qMetry MCP — Integration Test Suite

End-to-end integration tests that call the qMetry REST API directly through
`QMetryClient`.  Every test in this suite hits a **live** qMetry + Jira
instance, so you need valid credentials before running.

---

## Prerequisites

| Requirement | Where to get it |
|---|---|
| Python 3.11+ | https://python.org |
| pip dependencies | `pip install -r requirements.txt` from the `qmetry_mcp/` root |
| qMetry API key | Jira → **QMetry** → **Configuration** → **Open API** → **Generate** |
| A qMetry-enabled Jira project | Any project with qMetry activated |
| At least one Jira issue in that project | Any existing issue (used to test requirements linking) |

---

## Quick Start (new instance)

### 1 — Copy and fill in the environment file

```bash
cp .env.example .env
```

Open `.env` and set these values:

```
# Your qMetry API key
QMETRY_API_KEY=your-actual-api-key

# Base URL — keep the default for qMetry Cloud; change for self-hosted
QMETRY_BASE_URL=https://qtmcloud.qmetry.com/rest/api/latest/

# ── Test configuration (the only two things to change per instance) ────────
TEST_PROJECT_KEY=MYPROJECT        # Jira project key to run tests against
TEST_JIRA_ISSUE_KEY=MYPROJECT-1   # Any existing Jira issue in that project
```

> `TEST_JIRA_ISSUE_KEY` is used only for requirements-linking tests.
> If you leave it blank those specific tests are **skipped** (not failed);
> everything else still runs.

### 2 — Run the full suite

```bash
# From the qmetry_mcp/ directory
python -m pytest tests/integration/ -v -s
```

### 3 — Check the results in qMetry UI

All artefacts created by the tests are prefixed `[MCP-TEST]` so they are
easy to find and filter in the qMetry interface.  Tests clean up via
**archive** (soft-delete) rather than hard-delete, so the artefacts remain
visible in the UI for manual verification.

---

## Test File Overview

Tests are numbered so pytest runs them in dependency order.  Each file can
also be run standalone — if a prerequisite ID is missing the test either
creates what it needs on the fly or skips gracefully.

| File | What it tests | Creates |
|---|---|---|
| `test_00_smoke.py` | Connectivity, API key, project access | Nothing |
| `test_01_metadata.py` | `list_labels`, `create_label`, priorities, statuses | 1 label |
| `test_02_folders.py` | Folder list + create for TC / cycle / plan | 3 folders |
| `test_03_test_cases.py` | TC create → get → search → update → steps → clone → move → requirements → archive | 2 TCs |
| `test_04_test_cycles.py` | Cycle create → get → search → update → link TCs → requirements → archive | 2 cycles |
| `test_05_test_plans.py` | Plan create → get → search → update → link cycles → archive | 2 plans |
| `test_06_pipeline.py` | End-to-end flow: folder → TCs → steps → requirements → cycle → all linked | 2 TCs + 1 cycle |

---

## Running Individual Files

```bash
# Smoke check only
python -m pytest tests/integration/test_00_smoke.py -v -s

# Test cases only
python -m pytest tests/integration/test_03_test_cases.py -v -s

# Cycles + plans together
python -m pytest tests/integration/test_04_test_cycles.py tests/integration/test_05_test_plans.py -v -s

# Pipeline end-to-end
python -m pytest tests/integration/test_06_pipeline.py -v -s
```

## Running a Single Test

```bash
python -m pytest tests/integration/test_03_test_cases.py::TestCreateTestCase::test_create_returns_id_and_key -v -s
```

---

## How Cross-File State Works

When the **full suite** runs together, later test files reuse artefacts
created by earlier ones — no duplicate resources are created:

```
test_02 creates folders
    └── test_03 creates TCs inside those folders
            └── test_04 links those TCs into a new cycle
                    └── test_05 links that cycle into a new plan
                            └── test_06 runs the full pipeline end-to-end
```

This is implemented via a session-scoped `shared_state` dict in `conftest.py`.
Keys written/read between files:

| Key | Written by | Read by |
|---|---|---|
| `tc_folder_id` | test_02 | test_03, test_06 |
| `cycle_folder_id` | test_02 | test_04 |
| `plan_folder_id` | test_02 | test_05 |
| `tc_id`, `tc_key`, `tc_version` | test_03 | test_04 |
| `cycle_id`, `cycle_key` | test_04 | test_05 |

---

## Switching to a Different Jira Instance

1. Update **two values** in `.env`:
   ```
   TEST_PROJECT_KEY=OTHERPROJECT
   TEST_JIRA_ISSUE_KEY=OTHERPROJECT-5
   ```
2. Re-run the suite.  Everything else is discovered dynamically.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `No projects returned` | Wrong API key or base URL | Check `QMETRY_API_KEY` and `QMETRY_BASE_URL` in `.env` |
| `TEST_PROJECT_KEY 'X' not found` | Key doesn't exist or not qMetry-enabled | Use the exact key from Jira project settings |
| Requirements tests skipped | `TEST_JIRA_ISSUE_KEY` not set | Add any valid issue key to `.env` |
| `401 Unauthorized` | Expired or invalid API key | Regenerate key from qMetry → Configuration → Open API |
| `Connection refused` | Wrong base URL for self-hosted | Set `QMETRY_BASE_URL` to your Jira server URL |
| A test class skips all methods | A prior `_state` key is missing | Run the full file, not just the class; or run the full suite |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `QMETRY_API_KEY` | **Yes** | — | qMetry REST API key |
| `QMETRY_BASE_URL` | No | `https://qtmcloud.qmetry.com/rest/api/latest/` | API base URL |
| `TEST_PROJECT_KEY` | **Yes** | first available project | Jira project key to test against |
| `TEST_JIRA_ISSUE_KEY` | No | — | Jira issue key for requirements-linking tests |
