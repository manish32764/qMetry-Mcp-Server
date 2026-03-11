"""
Folder tests — 02
=================
Create one folder of each type (test-case, test-cycle, test-plan) and write
their IDs into shared_state so later test files can place their artifacts
inside organised folders.

Tools exercised:
  list_test_case_folders, create_test_case_folder
  list_test_cycle_folders, create_test_cycle_folder
  list_test_plan_folders,  create_test_plan_folder

Run:
    python -m pytest tests/integration/test_02_folders.py -v -s
"""

import pytest

from api.client import QMetryClient
from tests.integration.conftest import pp

_FOLDER_NAME = "[MCP-TEST] Automation Suite"


def _extract_id(response: dict | list) -> str:
    """Pull the folder ID from whatever shape the API returns."""
    if isinstance(response, dict):
        return str(response.get("id", response.get("folderId", "")))
    return ""


class TestTestCaseFolders:

    def test_list_test_case_folders(self, project_id):
        """list_test_case_folders returns a structure (may be empty on new instance)."""
        with QMetryClient() as c:
            result = c.list_test_case_folders(project_id=project_id)
        pp("list_test_case_folders", result)
        assert result is not None, "list_test_case_folders returned None"

    def test_create_test_case_folder(self, project_id, shared_state):
        """create_test_case_folder creates a folder and returns its ID."""
        with QMetryClient() as c:
            result = c.create_test_case_folder(
                project_id=project_id,
                name=_FOLDER_NAME,
            )
        pp("create_test_case_folder", result)

        folder_id = _extract_id(result)
        assert folder_id, f"No folder ID in response: {result}"

        shared_state["tc_folder_id"] = int(folder_id)
        print(f"\n  Test-case folder created — id={folder_id}")
        print(f"  Shared state updated: tc_folder_id={folder_id}")


class TestTestCycleFolders:

    def test_list_test_cycle_folders(self, project_id):
        """list_test_cycle_folders returns a structure."""
        with QMetryClient() as c:
            result = c.list_test_cycle_folders(project_id=project_id)
        pp("list_test_cycle_folders", result)
        assert result is not None, "list_test_cycle_folders returned None"

    def test_create_test_cycle_folder(self, project_id, shared_state):
        """create_test_cycle_folder creates a folder and returns its ID."""
        with QMetryClient() as c:
            result = c.create_test_cycle_folder(
                project_id=project_id,
                name=_FOLDER_NAME,
            )
        pp("create_test_cycle_folder", result)

        folder_id = _extract_id(result)
        assert folder_id, f"No folder ID in response: {result}"

        shared_state["cycle_folder_id"] = int(folder_id)
        print(f"\n  Test-cycle folder created — id={folder_id}")


class TestTestPlanFolders:

    def test_list_test_plan_folders(self, project_id):
        """list_test_plan_folders returns a structure."""
        with QMetryClient() as c:
            result = c.list_test_plan_folders(project_id=project_id)
        pp("list_test_plan_folders", result)
        assert result is not None, "list_test_plan_folders returned None"

    def test_create_test_plan_folder(self, project_id, shared_state):
        """create_test_plan_folder creates a folder and returns its ID."""
        with QMetryClient() as c:
            result = c.create_test_plan_folder(
                project_id=project_id,
                name=_FOLDER_NAME,
            )
        pp("create_test_plan_folder", result)

        folder_id = _extract_id(result)
        assert folder_id, f"No folder ID in response: {result}"

        shared_state["plan_folder_id"] = int(folder_id)
        print(f"\n  Test-plan folder created — id={folder_id}")
