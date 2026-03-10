"""MCP tools — Test Plans (search, get, create, update, link/unlink, archive)."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ..helpers import parse_csv, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def search_test_plans(
        project_key: str, search_text: str = "", max_results: int = 50
    ) -> str:
        """Search for test plans in a project.

        Args:
            project_key:  Jira project key.
            search_text:  Optional name filter.
            max_results:  Page size (default 50).
        """
        with get_client() as c:
            return to_json(c.search_test_plans(project_key, search_text, max_results))

    @mcp.tool()
    def get_test_plan(plan_id_or_key: str) -> str:
        """Get full details of a test plan.

        Args:
            plan_id_or_key: Test plan ID or key.
        """
        with get_client() as c:
            return to_json(c.get_test_plan(plan_id_or_key))

    @mcp.tool()
    def create_test_plan(
        project_key: str,
        name: str,
        description: str = "",
        status: str = "",
        folder_id: str = "",
    ) -> str:
        """Create a new test plan (groups multiple test cycles into a release plan).

        Args:
            project_key:  Jira project key.
            name:         Plan name (e.g. "Release 2.0 Test Plan").
            description:  Optional description.
            status:       Initial status (leave blank for project default).
            folder_id:    Target folder ID (leave blank for root).
        """
        with get_client() as c:
            return to_json(
                c.create_test_plan(
                    project_key=project_key,
                    name=name,
                    description=description,
                    status=status,
                    folder_id=folder_id,
                )
            )

    @mcp.tool()
    def update_test_plan(
        plan_id: str, name: str = "", description: str = "", status: str = ""
    ) -> str:
        """Update a test plan's name, description, or status.

        Args:
            plan_id:     Test plan ID.
            name:        New name (leave blank to keep existing).
            description: New description (leave blank to keep existing).
            status:      New status (leave blank to keep existing).
        """
        with get_client() as c:
            return to_json(
                c.update_test_plan(plan_id, name=name, description=description, status=status)
            )

    @mcp.tool()
    def link_cycles_to_test_plan(plan_id: str, cycle_keys: str) -> str:
        """Add test cycles to a test plan.

        Args:
            plan_id:     Test plan ID.
            cycle_keys:  Comma-separated test cycle keys (e.g. "CY-1,CY-2").
        """
        with get_client() as c:
            return to_json(c.link_cycles_to_test_plan(plan_id, parse_csv(cycle_keys)))

    @mcp.tool()
    def unlink_cycles_from_test_plan(plan_id: str, cycle_keys: str) -> str:
        """Remove test cycles from a test plan.

        Args:
            plan_id:    Test plan ID.
            cycle_keys: Comma-separated test cycle keys to remove.
        """
        with get_client() as c:
            return to_json(c.unlink_cycles_from_test_plan(plan_id, parse_csv(cycle_keys)))

    @mcp.tool()
    def get_plan_test_cycles(plan_id: str) -> str:
        """List all test cycles linked to a test plan.

        Args:
            plan_id: Test plan ID.
        """
        with get_client() as c:
            return to_json(c.get_plan_test_cycles(plan_id))

    @mcp.tool()
    def archive_test_plan(plan_id_or_key: str) -> str:
        """Archive a test plan.

        Args:
            plan_id_or_key: Test plan ID or key.
        """
        with get_client() as c:
            return to_json(c.archive_test_plan(plan_id_or_key))

    @mcp.tool()
    def unarchive_test_plan(plan_id_or_key: str) -> str:
        """Restore an archived test plan.

        Args:
            plan_id_or_key: Test plan ID or key.
        """
        with get_client() as c:
            return to_json(c.unarchive_test_plan(plan_id_or_key))
