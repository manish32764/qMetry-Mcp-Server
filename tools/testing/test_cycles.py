"""MCP tools — Test Cycles (search, get, create, update, link/unlink, archive)."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ..helpers import parse_csv, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def search_test_cycles(
        project_id: str,
        search_text: str = "",
        max_results: int = 50,
    ) -> str:
        """Search for test cycles in a project.

        Args:
            project_id:   Numeric project ID (get it from list_projects).
            search_text:  Optional name filter.
            max_results:  Page size (default 50).
        """
        with get_client() as c:
            return to_json(c.search_test_cycles(project_id, search_text, max_results))

    @mcp.tool()
    def get_test_cycle(cycle_id_or_key: str) -> str:
        """Get full details of a test cycle.

        Args:
            cycle_id_or_key: Test cycle ID or key.
        """
        with get_client() as c:
            return to_json(c.get_test_cycle(cycle_id_or_key))

    @mcp.tool()
    def create_test_cycle(
        project_id: str,
        name: str,
        description: str = "",
        status: str = "",
        folder_id: str = "",
    ) -> str:
        """Create a new test cycle.

        After creating, call link_test_cases_to_cycle and optionally
        link_requirements_to_cycle to link the originating Jira story.

        Args:
            project_id:   Numeric project ID (get it from list_projects).
            name:         Cycle name (e.g. "Sprint 12 — Login Feature").
            description:  Optional description.
            status:       Initial status (leave blank for project default).
            folder_id:    Target folder ID (leave blank for root).
        """
        with get_client() as c:
            return to_json(
                c.create_test_cycle(
                    project_id=project_id,
                    name=name,
                    description=description,
                    status=status,
                    folder_id=folder_id,
                )
            )

    @mcp.tool()
    def update_test_cycle(
        cycle_id: str, name: str = "", description: str = "", status: str = ""
    ) -> str:
        """Update a test cycle's name, description, or status.

        Args:
            cycle_id:    Test cycle ID.
            name:        New name (leave blank to keep existing).
            description: New description (leave blank to keep existing).
            status:      New status (leave blank to keep existing).
        """
        with get_client() as c:
            return to_json(
                c.update_test_cycle(cycle_id, name=name, description=description, status=status)
            )

    @mcp.tool()
    def link_test_cases_to_cycle(cycle_id: str, test_case_keys: str) -> str:
        """Add test cases to a test cycle.

        Args:
            cycle_id:        Test cycle ID (returned by create_test_cycle).
            test_case_keys:  Comma-separated test case keys (e.g. "TC-1,TC-2,TC-3").
        """
        with get_client() as c:
            return to_json(c.link_test_cases_to_cycle(cycle_id, parse_csv(test_case_keys)))

    @mcp.tool()
    def unlink_test_cases_from_cycle(cycle_id: str, test_case_keys: str) -> str:
        """Remove test cases from a test cycle.

        Args:
            cycle_id:        Test cycle ID.
            test_case_keys:  Comma-separated test case keys to remove.
        """
        with get_client() as c:
            return to_json(
                c.unlink_test_cases_from_cycle(cycle_id, parse_csv(test_case_keys))
            )

    @mcp.tool()
    def get_cycle_test_cases(
        cycle_id: str,
        search_text: str = "",
        execution_status: str = "",
        max_results: int = 50,
    ) -> str:
        """List test cases linked to a test cycle (with optional filters).

        Args:
            cycle_id:          Test cycle ID.
            search_text:       Optional text filter.
            execution_status:  Filter by execution result (e.g. "Pass", "Fail", "Not Executed").
            max_results:       Page size (default 50).
        """
        with get_client() as c:
            return to_json(
                c.get_cycle_test_cases(cycle_id, search_text, execution_status, max_results)
            )

    @mcp.tool()
    def link_requirements_to_cycle(cycle_id: str, issue_keys: str) -> str:
        """Link Jira issues (user stories) to a test cycle for traceability.

        Args:
            cycle_id:    Test cycle ID.
            issue_keys:  Comma-separated Jira issue keys (e.g. "PROJ-123").
        """
        with get_client() as c:
            return to_json(c.link_requirements_to_cycle(cycle_id, parse_csv(issue_keys)))

    @mcp.tool()
    def unlink_requirements_from_cycle(cycle_id: str, issue_keys: str) -> str:
        """Remove Jira issue links from a test cycle.

        Args:
            cycle_id:    Test cycle ID.
            issue_keys:  Comma-separated Jira issue keys to unlink.
        """
        with get_client() as c:
            return to_json(
                c.unlink_requirements_from_cycle(cycle_id, parse_csv(issue_keys))
            )

    @mcp.tool()
    def archive_test_cycle(cycle_id_or_key: str) -> str:
        """Archive a test cycle.

        Args:
            cycle_id_or_key: Test cycle ID or key.
        """
        with get_client() as c:
            return to_json(c.archive_test_cycle(cycle_id_or_key))

    @mcp.tool()
    def unarchive_test_cycle(cycle_id_or_key: str) -> str:
        """Restore an archived test cycle.

        Args:
            cycle_id_or_key: Test cycle ID or key.
        """
        with get_client() as c:
            return to_json(c.unarchive_test_cycle(cycle_id_or_key))
