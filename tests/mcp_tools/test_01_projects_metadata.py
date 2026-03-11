"""
MCP Tools — Projects & Metadata — 01
======================================
Tests for read-only tools that query project-level data.

Tools exercised:
  list_projects
  list_labels, create_label
  list_priorities
  list_test_case_statuses, list_test_cycle_statuses, list_test_plan_statuses

Run:
    python -m pytest tests/mcp_tools/test_01_projects_metadata.py -v -s
"""

import json

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text


class TestListProjects:

    @pytest.mark.asyncio
    async def test_list_projects_returns_json(self, session):
        """list_projects tool returns a valid JSON string."""
        result = await session.call_tool("list_projects", {"max_results": 10})
        raw = tool_text(result)
        pp("list_projects", raw)

        data = json.loads(raw)
        items = data if isinstance(data, list) else data.get("data", data.get("results", []))
        assert items, "list_projects returned an empty list — check API key."
        print(f"\n  {len(items)} project(s) returned via MCP tool.")

    @pytest.mark.asyncio
    async def test_list_projects_filtered_by_key(self, session, project_key):
        """list_projects with project_name filter narrows results."""
        result = await session.call_tool(
            "list_projects", {"project_name": project_key, "max_results": 10}
        )
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", data.get("results", []))
        keys = [p.get("key", p.get("projectKey", "")) for p in items]
        assert project_key in keys, (
            f"Project {project_key} not returned when filtering by name.\nGot: {keys}"
        )


class TestMetadataTools:

    @pytest.mark.asyncio
    async def test_list_labels(self, session, project_id):
        """list_labels returns a JSON list (may be empty on fresh instance)."""
        result = await session.call_tool("list_labels", {"project_id": project_id})
        pp("list_labels", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        assert isinstance(items, list)
        print(f"\n  {len(items)} label(s) found via MCP tool.")

    @pytest.mark.asyncio
    async def test_create_label(self, session, project_id):
        """create_label returns a response confirming the label was created."""
        result = await session.call_tool(
            "create_label",
            {"project_id": project_id, "name": "[MCP-TEST] mcp-tool-label"},
        )
        pp("create_label", tool_text(result))
        assert tool_text(result), "create_label returned empty response"

    @pytest.mark.asyncio
    async def test_list_priorities(self, session, project_id):
        """list_priorities returns at least one priority option."""
        result = await session.call_tool("list_priorities", {"project_id": project_id})
        pp("list_priorities", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        assert items, "list_priorities returned no options."
        print(f"\n  Priorities: {[p.get('name', '') for p in items]}")

    @pytest.mark.asyncio
    async def test_list_test_case_statuses(self, session, project_id):
        """list_test_case_statuses returns at least one status."""
        result = await session.call_tool("list_test_case_statuses", {"project_id": project_id})
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        assert items, "list_test_case_statuses returned no options."

    @pytest.mark.asyncio
    async def test_list_test_cycle_statuses(self, session, project_id):
        """list_test_cycle_statuses returns at least one status."""
        result = await session.call_tool("list_test_cycle_statuses", {"project_id": project_id})
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        assert items, "list_test_cycle_statuses returned no options."

    @pytest.mark.asyncio
    async def test_list_test_plan_statuses(self, session, project_id):
        """list_test_plan_statuses returns at least one status."""
        result = await session.call_tool("list_test_plan_statuses", {"project_id": project_id})
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        assert items, "list_test_plan_statuses returned no options."
        print("\n  All status tools returned results via MCP protocol.")
