"""
MCP Connectivity tests — 00
============================
Verify the server starts, the session initialises, and all expected tools
are registered.  No qMetry API calls are made in these tests.

Run:
    python -m pytest tests/mcp_tools/test_00_connectivity.py -v -s
"""

import pytest
import pytest_asyncio

from tests.mcp_tools.conftest import pp

# All 29 tools that should be registered in server.py
EXPECTED_TOOLS = {
    # Projects
    "list_projects",
    # Test Cases
    "search_test_cases",
    "get_test_case",
    "create_test_case",
    "update_test_case",
    "move_test_case",
    "clone_test_case",
    "archive_test_case",
    "unarchive_test_case",
    # Test Steps
    "get_test_steps",
    "add_test_steps",
    "update_test_steps",
    # Test Cycles
    "search_test_cycles",
    "get_test_cycle",
    "create_test_cycle",
    "update_test_cycle",
    "link_test_cases_to_cycle",
    "unlink_test_cases_from_cycle",
    "get_cycle_test_cases",
    "link_requirements_to_cycle",
    "unlink_requirements_from_cycle",
    "archive_test_cycle",
    "unarchive_test_cycle",
    # Test Plans
    "search_test_plans",
    "get_test_plan",
    "create_test_plan",
    "update_test_plan",
    "link_cycles_to_test_plan",
    "unlink_cycles_from_test_plan",
    "get_plan_test_cycles",
    "archive_test_plan",
    "unarchive_test_plan",
    # Folders
    "list_test_case_folders",
    "create_test_case_folder",
    "list_test_cycle_folders",
    "create_test_cycle_folder",
    "list_test_plan_folders",
    "create_test_plan_folder",
    # Metadata
    "list_labels",
    "create_label",
    "list_priorities",
    "list_test_case_statuses",
    "list_test_cycle_statuses",
    "list_test_plan_statuses",
    # Requirements
    "link_requirements_to_test_case",
    "unlink_requirements_from_test_case",
    # Pipeline
    "publish_test_cases_from_story",
}


class TestServerConnectivity:

    @pytest.mark.asyncio
    async def test_session_is_initialised(self, session):
        """The MCP ClientSession must be connected and initialised."""
        assert session is not None
        print("\n  MCP session is active.")

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_expected(self, session):
        """list_tools must return every tool defined in server.py."""
        response = await session.list_tools()
        registered = {t.name for t in response.tools}

        pp("list_tools — registered tool names", sorted(registered))

        missing = EXPECTED_TOOLS - registered
        extra = registered - EXPECTED_TOOLS

        if missing:
            pytest.fail(
                f"These tools are expected but NOT registered ({len(missing)}):\n"
                + "\n".join(f"  - {t}" for t in sorted(missing))
            )

        if extra:
            print(
                f"\n  NOTE: {len(extra)} extra tool(s) registered beyond the known set:\n"
                + "\n".join(f"    + {t}" for t in sorted(extra))
            )

        print(f"\n  {len(registered)} tool(s) registered. All expected tools present.")

    @pytest.mark.asyncio
    async def test_each_tool_has_description(self, session):
        """Every registered tool must have a non-empty description."""
        response = await session.list_tools()
        no_description = [t.name for t in response.tools if not (t.description or "").strip()]
        assert not no_description, (
            f"These tools have no description: {no_description}\n"
            "Add a docstring to each @mcp.tool() function."
        )

    @pytest.mark.asyncio
    async def test_each_tool_has_input_schema(self, session):
        """Every registered tool must expose an inputSchema."""
        response = await session.list_tools()
        no_schema = [t.name for t in response.tools if not t.inputSchema]
        assert not no_schema, (
            f"These tools have no inputSchema: {no_schema}"
        )
        print(f"\n  All {len(response.tools)} tools have descriptions and schemas.")
