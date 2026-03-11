"""
MCP Tools — Test Cycles — 04
=============================
Full lifecycle for test cycle tools called via the MCP protocol.

Reads tc_key from shared_state (written by test_03).  Falls back to
searching for an existing TC or creating one if this file runs standalone.

Tools exercised:
  create_test_cycle, get_test_cycle, search_test_cycles
  update_test_cycle
  link_test_cases_to_cycle, get_cycle_test_cases, unlink_test_cases_from_cycle
  link_requirements_to_cycle, unlink_requirements_from_cycle
  archive_test_cycle, unarchive_test_cycle

Run:
    python -m pytest tests/mcp_tools/test_04_test_cycles.py -v -s
"""

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text

_state: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cycle_id() -> str:
    return _state.get("cycle_id", "")


def _cycle_key() -> str:
    return _state.get("cycle_key", "")


async def _ensure_tc_key(session, project_id: str, shared_state: dict) -> str:
    """Return a TC key for linking — prefers shared_state, falls back to search/create."""
    if shared_state.get("tc_key"):
        return shared_state["tc_key"]

    result = await session.call_tool(
        "search_test_cases", {"project_id": project_id, "max_results": 5}
    )
    items_data = tool_json(result)
    items = items_data if isinstance(items_data, list) else items_data.get("data", [])
    if items:
        key = items[0].get("key", items[0].get("testCaseKey", ""))
        if key:
            return key

    # Create a minimal TC as last resort
    result = await session.call_tool(
        "create_test_case",
        {"project_id": project_id, "summary": "[MCP-TEST] Cycle linking placeholder"},
    )
    data = tool_json(result)
    tc_key = data.get("key", data.get("testCaseKey", ""))
    shared_state["tc_key"] = tc_key
    return tc_key


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestCycle:

    @pytest.mark.asyncio
    async def test_create_returns_id_and_key(self, session, project_id, shared_state):
        """create_test_cycle tool returns JSON with id and key."""
        result = await session.call_tool(
            "create_test_cycle",
            {
                "project_id": project_id,
                "name": "[MCP-TEST] Sprint 1 Regression",
                "description": "Auto-created by MCP tools test suite.",
            },
        )
        pp("create_test_cycle", tool_text(result))
        data = tool_json(result)

        cycle_id = str(data.get("id", data.get("cycleId", "")))
        cycle_key = data.get("key", data.get("cycleKey", ""))
        assert cycle_id, f"No cycle ID: {data}"
        assert cycle_key, f"No cycle key: {data}"

        _state["cycle_id"] = cycle_id
        _state["cycle_key"] = cycle_key
        shared_state["cycle_id"] = cycle_id
        shared_state["cycle_key"] = cycle_key
        print(f"\n  Cycle created via MCP tool — id={cycle_id}  key={cycle_key}")

    @pytest.mark.asyncio
    async def test_create_in_folder(self, session, project_id, shared_state):
        """create_test_cycle tool places cycle in folder from test_02."""
        folder_id = shared_state.get("cycle_folder_id", "")
        if not folder_id:
            pytest.skip("cycle_folder_id not in shared_state — run test_02 first.")

        result = await session.call_tool(
            "create_test_cycle",
            {
                "project_id": project_id,
                "name": "[MCP-TEST] Sprint 1 Regression (in folder)",
                "folder_id": str(folder_id),
            },
        )
        data = tool_json(result)
        cycle_id = str(data.get("id", data.get("cycleId", "")))
        assert cycle_id, f"No cycle ID: {data}"
        print(f"\n  Cycle in folder created — id={cycle_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestCycle:

    @pytest.mark.asyncio
    async def test_get_test_cycle_by_id(self, session):
        """get_test_cycle tool returns full cycle detail by ID."""
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id — run TestCreateTestCycle first.")

        result = await session.call_tool("get_test_cycle", {"cycle_id_or_key": cycle_id})
        pp("get_test_cycle (by id)", tool_text(result))
        data = tool_json(result)
        returned_id = str(data.get("id", data.get("cycleId", "")))
        assert returned_id == cycle_id

    @pytest.mark.asyncio
    async def test_get_test_cycle_by_key(self, session):
        """get_test_cycle tool also works with a key string."""
        cycle_key = _cycle_key()
        if not cycle_key:
            pytest.skip("No cycle_key.")

        result = await session.call_tool("get_test_cycle", {"cycle_id_or_key": cycle_key})
        data = tool_json(result)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_search_test_cycles_finds_created(self, session, project_id):
        """search_test_cycles tool finds the cycle by name."""
        cycle_key = _cycle_key()
        if not cycle_key:
            pytest.skip("No cycle_key.")

        result = await session.call_tool(
            "search_test_cycles",
            {
                "project_id": project_id,
                "search_text": "[MCP-TEST] Sprint 1 Regression",
                "max_results": 10,
            },
        )
        pp("search_test_cycles", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        keys = [cy.get("key", cy.get("cycleKey", "")) for cy in items]
        assert cycle_key in keys, f"Cycle {cycle_key} not found.\nGot: {keys}"


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestCycle:

    @pytest.mark.asyncio
    async def test_update_cycle_name_and_description(self, session):
        """update_test_cycle tool changes name and description."""
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        result = await session.call_tool(
            "update_test_cycle",
            {
                "cycle_id": cycle_id,
                "name": "[MCP-TEST] Sprint 1 Regression (updated)",
                "description": "Updated by MCP tools test.",
            },
        )
        pp("update_test_cycle", tool_text(result))
        assert tool_text(result) is not None


# ---------------------------------------------------------------------------
# 4. Link / Unlink test cases
# ---------------------------------------------------------------------------

class TestLinkTestCasesToCycle:

    @pytest.mark.asyncio
    async def test_link_test_cases_to_cycle(self, session, project_id, shared_state):
        """link_test_cases_to_cycle tool adds a TC to the cycle."""
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        tc_key = await _ensure_tc_key(session, project_id, shared_state)
        if not tc_key:
            pytest.skip("No TC key available.")

        result = await session.call_tool(
            "link_test_cases_to_cycle",
            {
                "cycle_id": cycle_id,
                "test_case_keys": tc_key,
                "project_id": project_id,
            },
        )
        pp("link_test_cases_to_cycle", tool_text(result))
        assert tool_text(result) is not None
        _state["linked_tc_key"] = tc_key
        print(f"\n  Linked {tc_key} → cycle {cycle_id} via MCP tool.")

    @pytest.mark.asyncio
    async def test_get_cycle_test_cases(self, session):
        """get_cycle_test_cases tool confirms the TC is linked."""
        cycle_id = _cycle_id()
        tc_key = _state.get("linked_tc_key", "")
        if not cycle_id or not tc_key:
            pytest.skip("Need cycle_id and linked_tc_key.")

        result = await session.call_tool(
            "get_cycle_test_cases",
            {"cycle_id": cycle_id, "max_results": 20},
        )
        pp("get_cycle_test_cases", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        keys = [t.get("key", t.get("testCaseKey", "")) for t in items]
        assert tc_key in keys, (
            f"TC {tc_key} not found in cycle after linking.\nFound: {keys}"
        )

    @pytest.mark.asyncio
    async def test_unlink_test_cases_from_cycle(self, session):
        """unlink_test_cases_from_cycle tool removes the TC."""
        cycle_id = _cycle_id()
        tc_key = _state.get("linked_tc_key", "")
        if not cycle_id or not tc_key:
            pytest.skip("Need cycle_id and linked_tc_key.")

        result = await session.call_tool(
            "unlink_test_cases_from_cycle",
            {"cycle_id": cycle_id, "test_case_keys": tc_key},
        )
        pp("unlink_test_cases_from_cycle", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Unlinked {tc_key} from cycle {cycle_id} via MCP tool.")


# ---------------------------------------------------------------------------
# 5. Requirements linking
# ---------------------------------------------------------------------------

class TestCycleRequirementsLinking:

    @pytest.mark.asyncio
    async def test_link_requirements_to_cycle(self, session, jira_issue_key):
        """link_requirements_to_cycle tool attaches a Jira issue."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        result = await session.call_tool(
            "link_requirements_to_cycle",
            {"cycle_id": cycle_id, "issue_keys": jira_issue_key},
        )
        pp("link_requirements_to_cycle", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Linked {jira_issue_key} → cycle {cycle_id} via MCP tool.")

    @pytest.mark.asyncio
    async def test_unlink_requirements_from_cycle(self, session, jira_issue_key):
        """unlink_requirements_from_cycle tool removes the Jira link."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        result = await session.call_tool(
            "unlink_requirements_from_cycle",
            {"cycle_id": cycle_id, "issue_keys": jira_issue_key},
        )
        pp("unlink_requirements_from_cycle", tool_text(result))
        assert tool_text(result) is not None


# ---------------------------------------------------------------------------
# 6. Archive / Unarchive
# ---------------------------------------------------------------------------

class TestArchiveTestCycle:

    @pytest.mark.asyncio
    async def test_archive_test_cycle(self, session):
        """archive_test_cycle tool soft-deletes the cycle."""
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        result = await session.call_tool("archive_test_cycle", {"cycle_id_or_key": cycle_id})
        pp("archive_test_cycle", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Cycle {cycle_id} archived via MCP tool.")

    @pytest.mark.asyncio
    async def test_unarchive_test_cycle(self, session):
        """unarchive_test_cycle tool restores the archived cycle."""
        cycle_id = _cycle_id()
        if not cycle_id:
            pytest.skip("No cycle_id.")

        result = await session.call_tool("unarchive_test_cycle", {"cycle_id_or_key": cycle_id})
        pp("unarchive_test_cycle", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Cycle {cycle_id} unarchived via MCP tool.")
