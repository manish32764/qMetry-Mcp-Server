"""MCP tools — Folders (list and create for test cases, cycles, and plans)."""

from mcp.server.fastmcp import FastMCP

from .client import get_client
from .helpers import to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_test_case_folders(project_id: str) -> str:
        """List all test case folders in a project.

        Args:
            project_id: qMetry project ID (numeric, from list_projects).
        """
        with get_client() as c:
            return to_json(c.list_test_case_folders(project_id))

    @mcp.tool()
    def create_test_case_folder(
        project_id: str, name: str, parent_id: str = ""
    ) -> str:
        """Create a test case folder (optionally nested under a parent).

        Args:
            project_id: qMetry project ID.
            name:       Folder name (e.g. "Sprint 12" or "PROJ-123 Login").
            parent_id:  Parent folder ID for nesting (leave blank for root).
        """
        with get_client() as c:
            return to_json(c.create_test_case_folder(project_id, name, parent_id))

    @mcp.tool()
    def list_test_cycle_folders(project_id: str) -> str:
        """List all test cycle folders in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_test_cycle_folders(project_id))

    @mcp.tool()
    def create_test_cycle_folder(
        project_id: str, name: str, parent_id: str = ""
    ) -> str:
        """Create a test cycle folder.

        Args:
            project_id: qMetry project ID.
            name:       Folder name.
            parent_id:  Parent folder ID (leave blank for root).
        """
        with get_client() as c:
            return to_json(c.create_test_cycle_folder(project_id, name, parent_id))

    @mcp.tool()
    def list_test_plan_folders(project_id: str) -> str:
        """List all test plan folders in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_test_plan_folders(project_id))

    @mcp.tool()
    def create_test_plan_folder(
        project_id: str, name: str, parent_id: str = ""
    ) -> str:
        """Create a test plan folder.

        Args:
            project_id: qMetry project ID.
            name:       Folder name.
            parent_id:  Parent folder ID (leave blank for root).
        """
        with get_client() as c:
            return to_json(c.create_test_plan_folder(project_id, name, parent_id))
