"""
MCP Tools — Folders — 02
=========================
Tests for all six folder tools (list + create for each folder type).
Created folder IDs are stored in shared_state for later test files.

Tools exercised:
  list_test_case_folders, create_test_case_folder
  list_test_cycle_folders, create_test_cycle_folder
  list_test_plan_folders,  create_test_plan_folder

Run:
    python -m pytest tests/mcp_tools/test_02_folders.py -v -s
"""

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text

_FOLDER_NAME = "[MCP-TEST] MCP Tools Suite"


def _extract_folder_id(data) -> str:
    if isinstance(data, dict):
        return str(data.get("id", data.get("folderId", "")))
    return ""


class TestTestCaseFolders:

    @pytest.mark.asyncio
    async def test_list_test_case_folders(self, session, project_id):
        """list_test_case_folders tool returns a response."""
        result = await session.call_tool("list_test_case_folders", {"project_id": project_id})
        pp("list_test_case_folders", tool_text(result))
        assert tool_text(result), "list_test_case_folders returned empty response"

    @pytest.mark.asyncio
    async def test_create_test_case_folder(self, session, project_id, shared_state):
        """create_test_case_folder creates a folder and returns its ID."""
        result = await session.call_tool(
            "create_test_case_folder",
            {"project_id": project_id, "name": _FOLDER_NAME},
        )
        pp("create_test_case_folder", tool_text(result))
        data = tool_json(result)
        folder_id = _extract_folder_id(data)
        assert folder_id, f"No folder ID in response: {data}"
        shared_state["tc_folder_id"] = int(folder_id)
        print(f"\n  TC folder created via MCP tool — id={folder_id}")


class TestTestCycleFolders:

    @pytest.mark.asyncio
    async def test_list_test_cycle_folders(self, session, project_id):
        """list_test_cycle_folders tool returns a response."""
        result = await session.call_tool("list_test_cycle_folders", {"project_id": project_id})
        assert tool_text(result)

    @pytest.mark.asyncio
    async def test_create_test_cycle_folder(self, session, project_id, shared_state):
        """create_test_cycle_folder creates a folder and returns its ID."""
        result = await session.call_tool(
            "create_test_cycle_folder",
            {"project_id": project_id, "name": _FOLDER_NAME},
        )
        data = tool_json(result)
        folder_id = _extract_folder_id(data)
        assert folder_id, f"No folder ID: {data}"
        shared_state["cycle_folder_id"] = int(folder_id)
        print(f"\n  Cycle folder created via MCP tool — id={folder_id}")


class TestTestPlanFolders:

    @pytest.mark.asyncio
    async def test_list_test_plan_folders(self, session, project_id):
        """list_test_plan_folders tool returns a response."""
        result = await session.call_tool("list_test_plan_folders", {"project_id": project_id})
        assert tool_text(result)

    @pytest.mark.asyncio
    async def test_create_test_plan_folder(self, session, project_id, shared_state):
        """create_test_plan_folder creates a folder and returns its ID."""
        result = await session.call_tool(
            "create_test_plan_folder",
            {"project_id": project_id, "name": _FOLDER_NAME},
        )
        data = tool_json(result)
        folder_id = _extract_folder_id(data)
        assert folder_id, f"No folder ID: {data}"
        shared_state["plan_folder_id"] = int(folder_id)
        print(f"\n  Plan folder created via MCP tool — id={folder_id}")
