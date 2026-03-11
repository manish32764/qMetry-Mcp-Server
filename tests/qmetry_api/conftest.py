"""
pytest configuration and shared fixtures for the qmetry_api test suite.

All tests in this package share:
  - .env loading (QMETRY_API_KEY, QMETRY_BASE_URL, TEST_PROJECT_KEY, TEST_JIRA_ISSUE_KEY)
  - A session-scoped `shared_state` dict that lets numbered test files pass IDs
    forward (e.g. test_03 writes tc_key, test_04 reads it).
  - `project_id` / `project_key` resolved once per session from TEST_PROJECT_KEY.

Run from the qmetry_mcp/ directory:
    python -m pytest tests/qmetry_api/ -v -s
"""

import json
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: ensure qmetry_mcp/ is on sys.path so "from api.client import ..."
# works regardless of how pytest is invoked.
# ---------------------------------------------------------------------------
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

# Load .env before any imports that read env vars.
_env_file = os.path.join(_PKG_ROOT, ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from api.client import QMetryClient  # noqa: E402


# ---------------------------------------------------------------------------
# Pretty-print helper (available to all test modules via import)
# ---------------------------------------------------------------------------

def pp(label: str, data) -> None:
    """Print a labelled JSON block — useful when running with -s."""
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    print(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def shared_state() -> dict:
    """
    Mutable dict shared across ALL tests in the session.

    Test files write discovered/created IDs here so later files can reuse them
    without re-creating resources.  Keys written by each file:

        test_02_folders:
            tc_folder_id    — test-case folder ID (int)
            cycle_folder_id — test-cycle folder ID (int)
            plan_folder_id  — test-plan folder ID (int)

        test_03_test_cases:
            tc_id           — numeric test case ID (str)
            tc_key          — e.g. "PROJ-TC-42"
            tc_version      — version number (int)

        test_04_test_cycles:
            cycle_id        — numeric cycle ID (str)
            cycle_key       — e.g. "PROJ-CY-7"

        test_05_test_plans:
            plan_id         — numeric plan ID (str)
            plan_key        — e.g. "PROJ-PL-3"
    """
    return {}


@pytest.fixture(scope="session")
def project_id_and_key(shared_state) -> tuple[str, str]:
    """
    Resolve (project_id, project_key) once per session.

    Reads TEST_PROJECT_KEY from the environment.  If set, filters the project
    list to that key.  Falls back to the first available project.
    """
    target_key = os.environ.get("TEST_PROJECT_KEY", "").strip()

    with QMetryClient() as c:
        result = c.list_projects(project_name=target_key, max_results=50)

    items = result if isinstance(result, list) else result.get("data", result.get("results", []))
    assert items, (
        "list_projects returned no projects.\n"
        "Check QMETRY_API_KEY and QMETRY_BASE_URL in your .env file."
    )

    project = None
    if target_key:
        for p in items:
            if p.get("key") == target_key or p.get("projectKey") == target_key:
                project = p
                break
        if project is None:
            pytest.fail(
                f"TEST_PROJECT_KEY='{target_key}' was not found in qMetry.\n"
                f"Available keys: {[p.get('key') for p in items]}"
            )
    else:
        project = items[0]

    pid = str(project.get("id", project.get("projectId", "")))
    pkey = project.get("key", project.get("projectKey", ""))
    assert pid, f"Could not determine project ID from: {project}"

    print(f"\n[conftest] Using project: key={pkey}  id={pid}")
    shared_state["project_id"] = pid
    shared_state["project_key"] = pkey
    return pid, pkey


@pytest.fixture(scope="session")
def project_id(project_id_and_key) -> str:
    return project_id_and_key[0]


@pytest.fixture(scope="session")
def project_key(project_id_and_key) -> str:
    return project_id_and_key[1]


@pytest.fixture(scope="session")
def jira_issue_key() -> str:
    """
    A Jira issue key used to test requirements-linking calls.

    Set TEST_JIRA_ISSUE_KEY in .env.  If absent the requirements tests are
    skipped gracefully.
    """
    return os.environ.get("TEST_JIRA_ISSUE_KEY", "").strip()
