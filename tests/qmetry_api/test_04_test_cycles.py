"""
Test Cycle tests — 04
=====================
Full CRUD lifecycle for a test cycle, plus linking test cases and requirements.

Reads tc_key from shared_state (written by test_03).  If test_03 was not run,
a fresh test case is created on the fly so this file can run standalone.

Tools exercised:
  create_test_cycle, get_test_cycle, search_test_cycles
  update_test_cycle
  link_test_cases_to_cycle, get_cycle_test_cases, unlink_test_cases_from_cycle
  link_requirements_to_cycle, unlink_requirements_from_cycle
  archive_test_cycle, unarchive_test_cycle

Run:
    python -m pytest tests/qmetry_api/test_04_test_cycles.py -v -s
"""

import pytest

from api.client import QMetryClient
from tests.qmetry_api.conftest import pp, RUN_TAG

# ---------------------------------------------------------------------------
# Shared within-file state
# ---------------------------------------------------------------------------
_state: dict = {}


def _get_cycle_id() -> str:
    return _state.get("cycle_id", "")


def _get_cycle_key() -> str:
    return _state.get("cycle_key", "")


# ---------------------------------------------------------------------------
# Helper: get at least one TC key to link into cycles
# ---------------------------------------------------------------------------

def _ensure_tc_key(project_id: str, shared_state: dict) -> str:
    """
    Return a test case key to use in linking tests.
    Prefers shared_state['tc_key'] (from test_03); falls back to searching;
    as a last resort creates a minimal TC.
    """
    if shared_state.get("tc_key"):
        return shared_state["tc_key"]

    # Try to find an existing TC
    with QMetryClient() as c:
        result = c.search_test_cases(project_id=project_id, max_results=5)
    items = result if isinstance(result, list) else result.get("data", [])
    if items:
        key = items[0].get("key", items[0].get("testCaseKey", ""))
        if key:
            return key

    # Create a minimal TC
    with QMetryClient() as c:
        tc = c.create_test_case(
            project_id=project_id,
            summary=f"{RUN_TAG} Cycle linking placeholder TC",
        )
    tc_id = str(tc.get("id", ""))
    tc_key = tc.get("key", tc.get("testCaseKey", ""))
    shared_state["tc_id"] = tc_id
    shared_state["tc_key"] = tc_key
    return tc_key


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestCycle:

    def test_create_returns_id_and_key(self, project_id, shared_state):
        """create_test_cycle returns a dict with id and key."""
        with QMetryClient() as c:
            result = c.create_test_cycle(
                project_id=project_id,
                name=f"{RUN_TAG} Sprint 1 Regression",
                description="Auto-created by MCP integration test suite.",
            )
        pp("create_test_cycle", result)

        cycle_id = str(result.get("id", result.get("cycleId", "")))
        cycle_key = result.get("key", result.get("cycleKey", ""))
        assert cycle_id, f"No cycle ID in response: {result}"
        assert cycle_key, f"No cycle key in response: {result}"

        _state["cycle_id"] = cycle_id
        _state["cycle_key"] = cycle_key
        shared_state["cycle_id"] = cycle_id
        shared_state["cycle_key"] = cycle_key
        print(f"\n  Cycle created — id={cycle_id}  key={cycle_key}")

    def test_create_in_folder(self, project_id, shared_state):
        """create_test_cycle with a folder_id places the cycle in that folder."""
        folder_id = shared_state.get("cycle_folder_id", "")
        if not folder_id:
            pytest.skip("cycle_folder_id not in shared_state — run test_02 first.")

        with QMetryClient() as c:
            result = c.create_test_cycle(
                project_id=project_id,
                name=f"{RUN_TAG} Sprint 1 Regression (in folder)",
                description="Cycle placed inside the automation folder.",
                folder_id=str(folder_id),
            )
        pp("create_test_cycle (with folder)", result)
        cycle_id = str(result.get("id", result.get("cycleId", "")))
        assert cycle_id, f"No cycle ID: {result}"
        print(f"\n  Cycle in folder created — id={cycle_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestCycle:

    def test_get_test_cycle_by_id(self):
        """get_test_cycle returns full details."""
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state — run TestCreateTestCycle first.")

        with QMetryClient() as c:
            result = c.get_test_cycle(cycle_id_or_key=cycle_id)
        pp("get_test_cycle", result)

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        # Some qMetry instances wrap the response in a {"data": {...}} envelope
        data = result.get("data", result)
        returned_id = str(data.get("id", data.get("cycleId", "")))
        assert returned_id == cycle_id, f"Returned id {returned_id} != {cycle_id}"

    def test_get_test_cycle_by_key(self):
        """get_test_cycle also works when given a key string."""
        cycle_key = _get_cycle_key()
        if not cycle_key:
            pytest.skip("No cycle_key in state.")

        with QMetryClient() as c:
            result = c.get_test_cycle(cycle_id_or_key=cycle_key)
        pp("get_test_cycle (by key)", result)
        assert isinstance(result, dict)

    def test_search_finds_created_cycle(self, project_id):
        """search_test_cycles finds the cycle we just created."""
        cycle_key = _get_cycle_key()
        if not cycle_key:
            pytest.skip("No cycle_key in state.")

        with QMetryClient() as c:
            result = c.search_test_cycles(
                project_id=project_id,
                search_text=f"{RUN_TAG} Sprint 1 Regression",
                max_results=10,
            )
        pp("search_test_cycles", result)
        items = result if isinstance(result, list) else result.get("data", [])
        keys = [cy.get("key", cy.get("cycleKey", "")) for cy in items]
        assert cycle_key in keys, (
            f"Cycle {cycle_key} not found in search results.\nFound: {keys}"
        )


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestCycle:

    def test_update_cycle_name_and_description(self):
        """update_test_cycle changes name and description."""
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        with QMetryClient() as c:
            result = c.update_test_cycle(
                cycle_id=cycle_id,
                name=f"{RUN_TAG} Sprint 1 Regression (updated)",
                description="Updated by MCP integration test.",
            )
        pp("update_test_cycle", result)
        assert result is not None, "update_test_cycle returned None"


# ---------------------------------------------------------------------------
# 4. Link / Unlink test cases
# ---------------------------------------------------------------------------

class TestLinkTestCasesToCycle:

    def test_link_test_cases(self, project_id, shared_state):
        """link_test_cases_to_cycle adds a TC to the cycle."""
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        tc_key = _ensure_tc_key(project_id, shared_state)
        if not tc_key:
            pytest.skip("No test case key available to link.")

        with QMetryClient() as c:
            result = c.link_test_cases_to_cycle(
                cycle_id=cycle_id,
                test_case_keys=[tc_key],
                project_id=project_id,
            )
        pp("link_test_cases_to_cycle", result)
        assert result is not None, "link_test_cases_to_cycle returned None"
        _state["linked_tc_key"] = tc_key
        print(f"\n  Linked {tc_key} -> cycle {cycle_id}")

    def test_get_cycle_test_cases_shows_linked(self):
        """get_cycle_test_cases reflects the linked TC."""
        cycle_id = _get_cycle_id()
        tc_key = _state.get("linked_tc_key", "")
        if not cycle_id or not tc_key:
            pytest.skip("Need cycle_id and linked_tc_key in state.")

        with QMetryClient() as c:
            result = c.get_cycle_test_cases(cycle_id=cycle_id, max_results=20)
        pp("get_cycle_test_cases", result)

        items = result if isinstance(result, list) else result.get("data", [])
        keys = [t.get("key", t.get("testCaseKey", "")) for t in items]
        assert tc_key in keys, (
            f"TC {tc_key} not found in cycle after linking.\nFound: {keys}"
        )

    @pytest.mark.xfail(
        reason="DELETE /testcycles/{id}/testcases endpoint behaviour varies by instance",
        strict=False,
    )
    def test_unlink_test_cases_from_cycle(self):
        """unlink_test_cases_from_cycle removes the TC from the cycle."""
        cycle_id = _get_cycle_id()
        tc_key = _state.get("linked_tc_key", "")
        if not cycle_id or not tc_key:
            pytest.skip("Need cycle_id and linked_tc_key in state.")

        with QMetryClient() as c:
            result = c.unlink_test_cases_from_cycle(
                cycle_id=cycle_id,
                test_case_keys=[tc_key],
            )
        pp("unlink_test_cases_from_cycle", result)
        assert result is not None, "unlink_test_cases_from_cycle returned None"
        print(f"\n  Unlinked {tc_key} from cycle {cycle_id}")


# ---------------------------------------------------------------------------
# 5. Requirements linking
# ---------------------------------------------------------------------------

class TestCycleRequirementsLinking:

    def test_link_requirements_to_cycle(self, jira_issue_key):
        """link_requirements_to_cycle attaches a Jira issue to the cycle."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        with QMetryClient() as c:
            result = c.link_requirements_to_cycle(
                cycle_id=cycle_id,
                issue_keys=[jira_issue_key],
            )
        pp("link_requirements_to_cycle", result)
        assert result is not None
        print(f"\n  Linked {jira_issue_key} -> cycle {cycle_id}")

    def test_unlink_requirements_from_cycle(self, jira_issue_key):
        """unlink_requirements_from_cycle removes the Jira issue link."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        with QMetryClient() as c:
            result = c.unlink_requirements_from_cycle(
                cycle_id=cycle_id,
                issue_keys=[jira_issue_key],
            )
        pp("unlink_requirements_from_cycle", result)
        assert result is not None
        print(f"\n  Unlinked {jira_issue_key} from cycle {cycle_id}")


# ---------------------------------------------------------------------------
# 6. Archive / Unarchive
# ---------------------------------------------------------------------------

class TestArchiveTestCycle:

    def test_archive_test_cycle(self):
        """archive_test_cycle soft-deletes the cycle."""
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        with QMetryClient() as c:
            result = c.archive_test_cycle(cycle_id_or_key=cycle_id)
        pp("archive_test_cycle", result)
        assert result is not None, "archive_test_cycle returned None"
        print(f"\n  Cycle {cycle_id} archived.")

    def test_unarchive_test_cycle(self):
        """unarchive_test_cycle restores the archived cycle."""
        cycle_id = _get_cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id in state.")

        with QMetryClient() as c:
            result = c.unarchive_test_cycle(cycle_id_or_key=cycle_id)
        pp("unarchive_test_cycle", result)
        assert result is not None, "unarchive_test_cycle returned None"
        print(f"\n  Cycle {cycle_id} unarchived.")
