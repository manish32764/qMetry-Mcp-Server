"""
Integration tests: Test Cycle Management
  - create_test_cycle
  - link_test_cases_to_cycle

NO cleanup performed — artifacts remain in qMetry for UI verification.

Run from qmetry_mcp/ directory:
    python -m pytest tests/integration/test_cycle_management.py -v -s
or directly:
    python tests/integration/test_cycle_management.py
"""

import json
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Path / env bootstrap (works both as pytest and as a direct script)
# ---------------------------------------------------------------------------
_pkg_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # qmetry_mcp/
sys.path.insert(0, _pkg_root)

_env_file = os.path.join(_pkg_root, ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from api.client import QMetryClient  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pp(label: str, data) -> None:
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    print(json.dumps(data, indent=2, default=str))


def _get_project() -> tuple[str, str]:
    """Return (project_id, project_key) for the first available project."""
    with QMetryClient() as c:
        result = c.list_projects(max_results=5)
    _pp("list_projects", result)
    items = result if isinstance(result, list) else result.get("data", [])
    assert items, "No projects returned — check QMETRY_API_KEY / QMETRY_BASE_URL"
    p = items[0]
    return str(p.get("id", p.get("projectId", ""))), p.get("key", "")


def _get_tc_keys(project_id: str, limit: int = 3) -> list[str]:
    """Return up to `limit` test case keys from the project."""
    with QMetryClient() as c:
        result = c.search_test_cases(project_id=project_id, max_results=limit)
    _pp(f"search_test_cases (project={project_id})", result)
    items = result if isinstance(result, list) else result.get("data", [])
    return [
        t.get("key") or t.get("testCaseKey", "")
        for t in items[:limit]
        if t.get("key") or t.get("testCaseKey")
    ]


# ---------------------------------------------------------------------------
# Test 1 — Create Test Cycle
# ---------------------------------------------------------------------------

class TestCreateTestCycle:

    def test_creates_cycle_and_returns_id(self):
        """create_test_cycle returns a response with a non-empty cycle ID."""
        project_id, project_key = _get_project()
        print(f"\nUsing project: key={project_key}  id={project_id}")

        with QMetryClient() as c:
            response = c.create_test_cycle(
                project_id=project_id,
                name="[MCP-TEST] Create Test Cycle Tool",
                description="Auto-created by MCP integration test. Verify in UI.",
            )

        _pp("create_test_cycle response", response)

        # Basic assertions
        assert isinstance(response, dict), f"Expected dict, got {type(response)}"
        cycle_id = str(response.get("id", response.get("cycleId", "")))
        assert cycle_id, f"No 'id'/'cycleId' in response: {response}"

        print(f"\n  Cycle created — id={cycle_id}  key={response.get('key', response.get('cycleKey', 'N/A'))}")
        print("  [NO CLEANUP] Artifact left in qMetry for UI verification.")

    def test_creates_cycle_with_description(self):
        """create_test_cycle stores description when provided."""
        project_id, project_key = _get_project()

        with QMetryClient() as c:
            response = c.create_test_cycle(
                project_id=project_id,
                name="[MCP-TEST] Cycle With Description",
                description="Description set by MCP test — should appear in UI.",
            )

        _pp("create_test_cycle (with description) response", response)

        assert isinstance(response, dict)
        cycle_id = str(response.get("id", response.get("cycleId", "")))
        assert cycle_id, f"No cycle ID in response: {response}"
        print(f"\n  Cycle with description created — id={cycle_id}")
        print("  [NO CLEANUP] Artifact left in qMetry for UI verification.")


# ---------------------------------------------------------------------------
# Test 2 — Add Test Cases to Cycle
# ---------------------------------------------------------------------------

class TestLinkTestCasesToCycle:

    def test_link_test_cases_bulk(self):
        """link_test_cases_to_cycle bulk-assigns test cases into a new cycle."""
        project_id, project_key = _get_project()

        tc_keys = _get_tc_keys(project_id, limit=3)
        if not tc_keys:
            pytest.skip(f"No test cases found in project {project_key} — cannot test linking.")

        print(f"\n  Test cases to link: {tc_keys}")

        # Create a fresh cycle for this test
        with QMetryClient() as c:
            cycle = c.create_test_cycle(
                project_id=project_id,
                name="[MCP-TEST] Cycle For Linking Test Cases",
                description="Cycle created to test bulk add of test cases. Verify in UI.",
            )
        _pp("create_test_cycle (for link test)", cycle)

        cycle_id = str(cycle.get("id", cycle.get("cycleId", "")))
        assert cycle_id, f"Cycle creation failed: {cycle}"

        # Link test cases
        with QMetryClient() as c:
            link_response = c.link_test_cases_to_cycle(
                cycle_id=cycle_id,
                test_case_keys=tc_keys,
                project_id=project_id,
            )
        _pp("link_test_cases_to_cycle response", link_response)

        assert link_response is not None, "link_test_cases_to_cycle returned None"

        # Verify linkage via get_cycle_test_cases
        with QMetryClient() as c:
            linked = c.get_cycle_test_cases(cycle_id=cycle_id, max_results=10)
        _pp("get_cycle_test_cases (verification)", linked)

        linked_items = linked if isinstance(linked, list) else linked.get("data", [])
        linked_keys = [
            t.get("key") or t.get("testCaseKey", "")
            for t in linked_items
        ]
        print(f"\n  Keys found in cycle after linking: {linked_keys}")
        for k in tc_keys:
            assert k in linked_keys, f"Test case {k} was not found in cycle after linking"

        print(f"\n  cycle_id={cycle_id}  linked={tc_keys}")
        print("  [NO CLEANUP] Artifact left in qMetry for UI verification.")

    def test_link_single_test_case(self):
        """link_test_cases_to_cycle works with a single test case key."""
        project_id, project_key = _get_project()

        tc_keys = _get_tc_keys(project_id, limit=1)
        if not tc_keys:
            pytest.skip(f"No test cases found in project {project_key}.")

        with QMetryClient() as c:
            cycle = c.create_test_cycle(
                project_id=project_id,
                name="[MCP-TEST] Cycle For Single TC Link",
                description="Single test case link test. Verify in UI.",
            )
        cycle_id = str(cycle.get("id", cycle.get("cycleId", "")))
        assert cycle_id

        with QMetryClient() as c:
            link_response = c.link_test_cases_to_cycle(
                cycle_id=cycle_id,
                test_case_keys=tc_keys,
                project_id=project_id,
            )
        _pp("link_test_cases_to_cycle (single TC) response", link_response)

        assert link_response is not None
        print(f"\n  cycle_id={cycle_id}  tc={tc_keys[0]}")
        print("  [NO CLEANUP] Artifact left in qMetry for UI verification.")


# ---------------------------------------------------------------------------
# Direct-run entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    failures = []

    def run(name, fn):
        print(f"\n{'#'*60}\nRUNNING: {name}\n{'#'*60}")
        try:
            fn()
            print(f"  PASSED: {name}")
        except Exception as e:
            print(f"  FAILED: {name} — {e}")
            traceback.print_exc()
            failures.append(name)

    t1 = TestCreateTestCycle()
    t2 = TestLinkTestCasesToCycle()

    run("TestCreateTestCycle::test_creates_cycle_and_returns_id", t1.test_creates_cycle_and_returns_id)
    run("TestCreateTestCycle::test_creates_cycle_with_description", t1.test_creates_cycle_with_description)
    run("TestLinkTestCasesToCycle::test_link_test_cases_bulk", t2.test_link_test_cases_bulk)
    run("TestLinkTestCasesToCycle::test_link_single_test_case", t2.test_link_single_test_case)

    print(f"\n{'='*60}")
    if failures:
        print(f"FAILED ({len(failures)}): {failures}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
    print("="*60)
