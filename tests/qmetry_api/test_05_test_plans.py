"""
Test Plan tests — 05
====================
Full CRUD lifecycle for a test plan, plus linking test cycles.

Reads cycle_key from shared_state (written by test_04).  If test_04 was not
run, a fresh test cycle is created on the fly.

Tools exercised:
  create_test_plan, get_test_plan, search_test_plans
  update_test_plan
  link_cycles_to_test_plan, get_plan_test_cycles, unlink_cycles_from_test_plan
  archive_test_plan, unarchive_test_plan

Run:
    python -m pytest tests/qmetry_api/test_05_test_plans.py -v -s
"""

import pytest

from api.client import QMetryClient
from tests.qmetry_api.conftest import pp

# ---------------------------------------------------------------------------
# Shared within-file state
# ---------------------------------------------------------------------------
_state: dict = {}


def _get_plan_id() -> str:
    return _state.get("plan_id", "")


def _get_plan_key() -> str:
    return _state.get("plan_key", "")


# ---------------------------------------------------------------------------
# Helper: ensure we have a cycle key to link
# ---------------------------------------------------------------------------

def _ensure_cycle_key(project_id: str, shared_state: dict) -> str:
    """
    Return a cycle key for linking tests.
    Prefers shared_state['cycle_key']; falls back to search; creates if needed.
    """
    if shared_state.get("cycle_key"):
        return shared_state["cycle_key"]

    with QMetryClient() as c:
        result = c.search_test_cycles(project_id=project_id, max_results=5)
    items = result if isinstance(result, list) else result.get("data", [])
    if items:
        key = items[0].get("key", items[0].get("cycleKey", ""))
        if key:
            return key

    with QMetryClient() as c:
        cycle = c.create_test_cycle(
            project_id=project_id,
            name="[MCP-TEST] Plan-linking placeholder cycle",
        )
    cycle_id = str(cycle.get("id", ""))
    cycle_key = cycle.get("key", cycle.get("cycleKey", ""))
    shared_state["cycle_id"] = cycle_id
    shared_state["cycle_key"] = cycle_key
    return cycle_key


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestPlan:

    def test_create_returns_id_and_key(self, project_id, shared_state):
        """create_test_plan returns a dict with id and key."""
        with QMetryClient() as c:
            result = c.create_test_plan(
                project_id=project_id,
                name="[MCP-TEST] Q1 Release Plan",
                description="Auto-created by MCP integration test suite.",
            )
        pp("create_test_plan", result)

        plan_id = str(result.get("id", result.get("planId", "")))
        plan_key = result.get("key", result.get("planKey", ""))
        assert plan_id, f"No plan ID in response: {result}"
        assert plan_key, f"No plan key in response: {result}"

        _state["plan_id"] = plan_id
        _state["plan_key"] = plan_key
        shared_state["plan_id"] = plan_id
        shared_state["plan_key"] = plan_key
        print(f"\n  Plan created — id={plan_id}  key={plan_key}")

    def test_create_in_folder(self, project_id, shared_state):
        """create_test_plan with folder_id places the plan in that folder."""
        folder_id = shared_state.get("plan_folder_id", "")
        if not folder_id:
            pytest.skip("plan_folder_id not in shared_state — run test_02 first.")

        with QMetryClient() as c:
            result = c.create_test_plan(
                project_id=project_id,
                name="[MCP-TEST] Q1 Release Plan (in folder)",
                folder_id=str(folder_id),
            )
        pp("create_test_plan (with folder)", result)
        plan_id = str(result.get("id", result.get("planId", "")))
        assert plan_id, f"No plan ID: {result}"
        print(f"\n  Plan in folder created — id={plan_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestPlan:

    def test_get_test_plan_by_id(self):
        """get_test_plan returns full details."""
        plan_id = _get_plan_id()
        if not plan_id:
            pytest.skip("No plan_id in state — run TestCreateTestPlan first.")

        with QMetryClient() as c:
            result = c.get_test_plan(plan_id_or_key=plan_id)
        pp("get_test_plan", result)

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        returned_id = str(result.get("id", result.get("planId", "")))
        assert returned_id == plan_id, f"Returned id {returned_id} != {plan_id}"

    def test_get_test_plan_by_key(self):
        """get_test_plan also works when given a key string."""
        plan_key = _get_plan_key()
        if not plan_key:
            pytest.skip("No plan_key in state.")

        with QMetryClient() as c:
            result = c.get_test_plan(plan_id_or_key=plan_key)
        pp("get_test_plan (by key)", result)
        assert isinstance(result, dict)

    def test_search_finds_created_plan(self, project_id):
        """search_test_plans finds the plan we just created."""
        plan_key = _get_plan_key()
        if not plan_key:
            pytest.skip("No plan_key in state.")

        with QMetryClient() as c:
            result = c.search_test_plans(
                project_id=project_id,
                search_text="[MCP-TEST] Q1 Release Plan",
                max_results=10,
            )
        pp("search_test_plans", result)
        items = result if isinstance(result, list) else result.get("data", [])
        keys = [p.get("key", p.get("planKey", "")) for p in items]
        assert plan_key in keys, (
            f"Plan {plan_key} not found in search results.\nFound: {keys}"
        )


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestPlan:

    def test_update_plan_name_and_description(self):
        """update_test_plan changes name and description."""
        plan_id = _get_plan_id()
        if not plan_id:
            pytest.skip("No plan_id in state.")

        with QMetryClient() as c:
            result = c.update_test_plan(
                plan_id=plan_id,
                name="[MCP-TEST] Q1 Release Plan (updated)",
                description="Updated by MCP integration test.",
            )
        pp("update_test_plan", result)
        assert result is not None, "update_test_plan returned None"


# ---------------------------------------------------------------------------
# 4. Link / Unlink cycles
# ---------------------------------------------------------------------------

class TestLinkCyclesToPlan:

    def test_link_cycles_to_test_plan(self, project_id, shared_state):
        """link_cycles_to_test_plan adds a cycle to the plan."""
        plan_id = _get_plan_id()
        if not plan_id:
            pytest.skip("No plan_id in state.")

        cycle_key = _ensure_cycle_key(project_id, shared_state)
        if not cycle_key:
            pytest.skip("No cycle key available to link.")

        with QMetryClient() as c:
            result = c.link_cycles_to_test_plan(
                plan_id=plan_id,
                cycle_keys=[cycle_key],
            )
        pp("link_cycles_to_test_plan", result)
        assert result is not None, "link_cycles_to_test_plan returned None"
        _state["linked_cycle_key"] = cycle_key
        print(f"\n  Linked cycle {cycle_key} → plan {plan_id}")

    def test_get_plan_test_cycles_shows_linked(self):
        """get_plan_test_cycles reflects the linked cycle."""
        plan_id = _get_plan_id()
        cycle_key = _state.get("linked_cycle_key", "")
        if not plan_id or not cycle_key:
            pytest.skip("Need plan_id and linked_cycle_key in state.")

        with QMetryClient() as c:
            result = c.get_plan_test_cycles(plan_id=plan_id)
        pp("get_plan_test_cycles", result)

        items = result if isinstance(result, list) else result.get("data", [])
        keys = [cy.get("key", cy.get("cycleKey", "")) for cy in items]
        assert cycle_key in keys, (
            f"Cycle {cycle_key} not found in plan after linking.\nFound: {keys}"
        )

    def test_unlink_cycles_from_test_plan(self):
        """unlink_cycles_from_test_plan removes the cycle from the plan."""
        plan_id = _get_plan_id()
        cycle_key = _state.get("linked_cycle_key", "")
        if not plan_id or not cycle_key:
            pytest.skip("Need plan_id and linked_cycle_key in state.")

        with QMetryClient() as c:
            result = c.unlink_cycles_from_test_plan(
                plan_id=plan_id,
                cycle_keys=[cycle_key],
            )
        pp("unlink_cycles_from_test_plan", result)
        assert result is not None, "unlink_cycles_from_test_plan returned None"
        print(f"\n  Unlinked cycle {cycle_key} from plan {plan_id}")


# ---------------------------------------------------------------------------
# 5. Archive / Unarchive
# ---------------------------------------------------------------------------

class TestArchiveTestPlan:

    def test_archive_test_plan(self):
        """archive_test_plan soft-deletes the plan."""
        plan_id = _get_plan_id()
        if not plan_id:
            pytest.skip("No plan_id in state.")

        with QMetryClient() as c:
            result = c.archive_test_plan(plan_id_or_key=plan_id)
        pp("archive_test_plan", result)
        assert result is not None, "archive_test_plan returned None"
        print(f"\n  Plan {plan_id} archived.")

    def test_unarchive_test_plan(self):
        """unarchive_test_plan restores the archived plan."""
        plan_id = _get_plan_id()
        if not plan_id:
            pytest.skip("No plan_id in state.")

        with QMetryClient() as c:
            result = c.unarchive_test_plan(plan_id_or_key=plan_id)
        pp("unarchive_test_plan", result)
        assert result is not None, "unarchive_test_plan returned None"
        print(f"\n  Plan {plan_id} unarchived.")
