"""MCP tools — Metadata lookups (labels, priorities, statuses)."""

from mcp.server.fastmcp import FastMCP

from .client import get_client
from .helpers import to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_labels(project_id: str) -> str:
        """List all labels configured in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_labels(project_id))

    @mcp.tool()
    def create_label(project_id: str, name: str) -> str:
        """Create a new label in a project.

        Args:
            project_id: qMetry project ID.
            name:       Label name (e.g. "regression", "smoke", "sprint-12").
        """
        with get_client() as c:
            return to_json(c.create_label(project_id, name))

    @mcp.tool()
    def list_priorities(project_id: str) -> str:
        """List all priority options in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_priorities(project_id))

    @mcp.tool()
    def list_test_case_statuses(project_id: str) -> str:
        """List all test case status options in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_test_case_statuses(project_id))

    @mcp.tool()
    def list_test_cycle_statuses(project_id: str) -> str:
        """List all test cycle status options in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_test_cycle_statuses(project_id))

    @mcp.tool()
    def list_test_plan_statuses(project_id: str) -> str:
        """List all test plan status options in a project.

        Args:
            project_id: qMetry project ID.
        """
        with get_client() as c:
            return to_json(c.list_test_plan_statuses(project_id))
