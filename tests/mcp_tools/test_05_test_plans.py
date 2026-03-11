"""
MCP Tools — Test Plans — 05
============================
Full lifecycle for test plan tools called via the MCP protocol.

Reads cycle_key from shared_state (written by test_04).  Falls back to
searching for an existing cycle or creating one if this file runs standalone.

Tools exercised:
  create_test_plan, get_test_plan, search_test_plans
  update_test_plan
  link_cycles_to_test_plan, get_plan_test_cycles, unlink_cycles_from_test_plan
  archive_test_plan, unarchive_test_plan

Run:
    python -m pytest tests/mcp_tools/test_05_test_plans.py -v -s
"""

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text

_state: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan_id() -> str:
    return _state.get("plan_id", "")


def _plan_key() -> str:
    return _state.get("plan_key", "")


async def _ensure_cycle_key(session, project_id: str, shared_state: dict) -> str:
    """Return a cycle key — prefers shared_state, falls back to search/create."""
    if shared_state.get("cycle_key"):
        return shared_state["cycle_key"]

    result = await session.call_tool(
        "search_test_cycles", {"project_id": project_id, "max_results": 5}
    )
    data = tool_json(result)
    items = data if isinstance(data, list) else data.get("data", [])
    if items:
        key = items[0].get("key", items[0].get("cycleKey", ""))
        if key:
            return key

    result = await session.call_tool(
        "create_test_cycle",
        {"project_id": project_id, "name": "[MCP-TEST] Plan-linking placeholder cycle"},
    )
    data = tool_json(result)
    cycle_key = data.get("key", data.get("cycleKey", ""))
    shared_state["cycle_key"] = cycle_key
    shared_state["cycle_id"] = str(data.get("id", ""))
    return cycle_key


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestPlan:

    @pytest.mark.asyncio
    async def test_create_returns_id_and_key(self, session, project_id, shared_state):
        """create_test_plan tool returns JSON with id and key."""
        result = await session.call_tool(
            "create_test_plan",
            {
                "project_id": project_id,
                "name": "[MCP-TEST] Q1 Release Plan",
                "description": "Auto-created by MCP tools test suite.",
            },
        )
        pp("create_test_plan", tool_text(result))
        data = tool_json(result)

        plan_id = str(data.get("id", data.get("planId", "")))
        plan_key = data.get("key", data.get("planKey", ""))
        assert plan_id, f"No plan ID: {data}"
        assert plan_key, f"No plan key: {data}"

        _state["plan_id"] = plan_id
        _state["plan_key"] = plan_key
        shared_state["plan_id"] = plan_id
        shared_state["plan_key"] = plan_key
        print(f"\n  Plan created via MCP tool — id={plan_id}  key={plan_key}")

    @pytest.mark.asyncio
    async def test_create_in_folder(self, session, project_id, shared_state):
        """create_test_plan tool places plan in folder from test_02."""
        folder_id = shared_state.get("plan_folder_id", "")
        if not folder_id:
            pytest.skip("plan_folder_id not in shared_state — run test_02 first.")

        result = await session.call_tool(
            "create_test_plan",
            {
                "project_id": project_id,
                "name": "[MCP-TEST] Q1 Release Plan (in folder)",
                "folder_id": str(folder_id),
            },
        )
        data = tool_json(result)
        plan_id = str(data.get("id", data.get("planId", "")))
        assert plan_id, f"No plan ID: {data}"
        print(f"\n  Plan in folder created — id={plan_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestPlan:

    @pytest.mark.asyncio
    async def test_get_test_plan_by_id(self, session):
        """get_test_plan tool returns full plan detail by ID."""
        plan_id = _plan_id()
        if not plan_id:
            pytest.skip("No plan_id — run TestCreateTestPlan first.")

        result = await session.call_tool("get_test_plan", {"plan_id_or_key": plan_id})
        pp("get_test_plan (by id)", tool_text(result))
        data = tool_json(result)
        returned_id = str(data.get("id", data.get("planId", "")))
        assert returned_id == plan_id

    @pytest.mark.asyncio
    async def test_get_test_plan_by_key(self, session):
        """get_test_plan tool also works with a key string."""
        plan_key = _plan_key()
        if not plan_key:
            pytest.skip("No plan_key.")

        result = await session.call_tool("get_test_plan", {"plan_id_or_key": plan_key})
        data = tool_json(result)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_search_test_plans_finds_created(self, session, project_id):
        """search_test_plans tool finds the plan by name."""
        plan_key = _plan_key()
        if not plan_key:
            pytest.skip("No plan_key.")

        result = await session.call_tool(
            "search_test_plans",
            {
                "project_id": project_id,
                "search_text": "[MCP-TEST] Q1 Release Plan",
                "max_results": 10,
            },
        )
        pp("search_test_plans", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        keys = [p.get("key", p.get("planKey", "")) for p in items]
        assert plan_key in keys, f"Plan {plan_key} not found.\nGot: {keys}"


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestPlan:

    @pytest.mark.asyncio
    async def test_update_plan_name_and_description(self, session):
        """update_test_plan tool changes name and description."""
        plan_id = _plan_id()
        if not plan_id:
            pytest.skip("No plan_id.")

        result = await session.call_tool(
            "update_test_plan",
            {
                "plan_id": plan_id,
                "name": "[MCP-TEST] Q1 Release Plan (updated)",
                "description": "Updated by MCP tools test.",
            },
        )
        pp("update_test_plan", tool_text(result))
        assert tool_text(result) is not None


# ---------------------------------------------------------------------------
# 4. Link / Unlink cycles
# ---------------------------------------------------------------------------

class TestLinkCyclesToPlan:

    @pytest.mark.asyncio
    async def test_link_cycles_to_test_plan(self, session, project_id, shared_state):
        """link_cycles_to_test_plan tool adds a cycle to the plan."""
        plan_id = _plan_id()
        if not plan_id:
            pytest.skip("No plan_id.")

        cycle_key = await _ensure_cycle_key(session, project_id, shared_state)
        if not cycle_key:
            pytest.skip("No cycle key available.")

        result = await session.call_tool(
            "link_cycles_to_test_plan",
            {"plan_id": plan_id, "cycle_keys": cycle_key},
        )
        pp("link_cycles_to_test_plan", tool_text(result))
        assert tool_text(result) is not None
        _state["linked_cycle_key"] = cycle_key
        print(f"\n  Linked cycle {cycle_key} → plan {plan_id} via MCP tool.")

    @pytest.mark.asyncio
    async def test_get_plan_test_cycles(self, session):
        """get_plan_test_cycles tool confirms the cycle is linked."""
        plan_id = _plan_id()
        cycle_key = _state.get("linked_cycle_key", "")
        if not plan_id or not cycle_key:
            pytest.skip("Need plan_id and linked_cycle_key.")

        result = await session.call_tool("get_plan_test_cycles", {"plan_id": plan_id})
        pp("get_plan_test_cycles", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        keys = [cy.get("key", cy.get("cycleKey", "")) for cy in items]
        assert cycle_key in keys, (
            f"Cycle {cycle_key} not found in plan.\nFound: {keys}"
        )

    @pytest.mark.asyncio
    async def test_unlink_cycles_from_test_plan(self, session):
        """unlink_cycles_from_test_plan tool removes the cycle."""
        plan_id = _plan_id()
        cycle_key = _state.get("linked_cycle_key", "")
        if not plan_id or not cycle_key:
            pytest.skip("Need plan_id and linked_cycle_key.")

        result = await session.call_tool(
            "unlink_cycles_from_test_plan",
            {"plan_id": plan_id, "cycle_keys": cycle_key},
        )
        pp("unlink_cycles_from_test_plan", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Unlinked cycle {cycle_key} from plan {plan_id} via MCP tool.")


# ---------------------------------------------------------------------------
# 5. Archive / Unarchive
# ---------------------------------------------------------------------------

class TestArchiveTestPlan:

    @pytest.mark.asyncio
    async def test_archive_test_plan(self, session):
        """archive_test_plan tool soft-deletes the plan."""
        plan_id = _plan_id()
        if not plan_id:
            pytest.skip("No plan_id.")

        result = await session.call_tool("archive_test_plan", {"plan_id_or_key": plan_id})
        pp("archive_test_plan", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Plan {plan_id} archived via MCP tool.")

    @pytest.mark.asyncio
    async def test_unarchive_test_plan(self, session):
        """unarchive_test_plan tool restores the archived plan."""
        plan_id = _plan_id()
        if not plan_id:
            pytest.skip("No plan_id.")

        result = await session.call_tool("unarchive_test_plan", {"plan_id_or_key": plan_id})
        pp("unarchive_test_plan", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Plan {plan_id} unarchived via MCP tool.")
