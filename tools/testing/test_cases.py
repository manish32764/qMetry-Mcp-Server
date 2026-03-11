"""MCP tools — Test Cases (search, get, create, update, archive)."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ..helpers import parse_csv, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def search_test_cases(
        project_id: str,
        search_text: str = "",
        status: str = "",
        priority: str = "",
        label: str = "",
        folder_id: str = "",
        max_results: int = 50,
        start_at: int = 0,
    ) -> str:
        """Search for existing test cases in a project.

        Use this BEFORE creating test cases to avoid duplicates.

        Args:
            project_id:   Numeric project ID (get it from list_projects).
            search_text:  Full-text search across summary/description.
            status:       Filter by status name (e.g. "Draft", "Approved").
            priority:     Filter by priority name (e.g. "High", "Medium").
            label:        Filter by label name.
            folder_id:    Filter to a specific folder ID.
            max_results:  Page size (default 50).
            start_at:     Pagination offset (default 0).
        """
        with get_client() as c:
            return to_json(
                c.search_test_cases(
                    project_id=project_id,
                    search_text=search_text,
                    status=status,
                    priority=priority,
                    label=label,
                    folder_id=folder_id,
                    max_results=max_results,
                    start_at=start_at,
                )
            )

    @mcp.tool()
    def get_test_case(test_case_id: str) -> str:
        """Get full details of a single test case by its ID or key.

        Args:
            test_case_id: qMetry test case ID or key (e.g. "TC-123").
        """
        with get_client() as c:
            return to_json(c.get_test_case(test_case_id))

    @mcp.tool()
    def create_test_case(
        project_id: str,
        summary: str,
        description: str = "",
        folder_id: str = "",
    ) -> str:
        """Create a new test case in qMetry.

        Call add_test_steps immediately after to attach steps.
        Call link_requirements_to_test_case to link the originating Jira story.

        Args:
            project_id:   Numeric project ID (get it from list_projects).
            summary:      Test case title / summary.
            description:  Detailed description or objective.
            folder_id:    Target folder ID (leave blank for root).
        """
        with get_client() as c:
            return to_json(
                c.create_test_case(
                    project_id=project_id,
                    summary=summary,
                    description=description,
                    folder_id=folder_id,
                )
            )

    @mcp.tool()
    def update_test_case(
        test_case_id: str,
        version_no: int,
        summary: str = "",
        description: str = "",
        priority: str = "",
        status: str = "",
        labels: str = "",
    ) -> str:
        """Update an existing test case's metadata.

        Args:
            test_case_id: qMetry test case ID.
            version_no:   Version number to update (usually 1 for latest).
            summary:      New summary (leave blank to keep existing).
            description:  New description (leave blank to keep existing).
            priority:     New priority (leave blank to keep existing).
            status:       New status (leave blank to keep existing).
            labels:       Comma-separated labels (replaces all existing labels).
        """
        with get_client() as c:
            return to_json(
                c.update_test_case(
                    test_case_id=test_case_id,
                    version_no=version_no,
                    summary=summary,
                    description=description,
                    priority=priority,
                    status=status,
                    labels=parse_csv(labels) if labels else None,
                )
            )

    @mcp.tool()
    def move_test_case(
        test_case_ids: str,
        project_id: int,
        target_folder_id: int,
        source_folder_id: int = -1,
    ) -> str:
        """Move one or more test cases to a different folder.

        Args:
            test_case_ids:    Comma-separated test case IDs to move (e.g. "abc123,def456").
            project_id:       Numeric project ID (get it from list_projects).
            target_folder_id: Destination folder ID (get IDs from list_test_case_folders).
            source_folder_id: Current folder ID of the test cases.
                              Use -1 (default) if the test cases are not yet assigned to any folder.
        """
        with get_client() as c:
            return to_json(
                c.move_test_case(
                    test_case_ids=parse_csv(test_case_ids),
                    project_id=project_id,
                    target_folder_id=target_folder_id,
                    source_folder_id=source_folder_id,
                )
            )

    @mcp.tool()
    def clone_test_case(
        test_case_id: str,
        new_summary: str,
        folder_id: int,
        version: str = "1",
    ) -> str:
        """Clone a test case (copies all steps) into a target folder.

        Args:
            test_case_id: Source test case ID or key to clone.
            new_summary:  Summary for the cloned test case.
            folder_id:    Target folder ID for the clone (get IDs from list_test_case_folders).
            version:      '1' to clone the latest version only, '*' to clone all versions.
        """
        with get_client() as c:
            return to_json(c.clone_test_case(test_case_id, new_summary, folder_id, version))

    @mcp.tool()
    def archive_test_case(test_case_id: str) -> str:
        """Archive a test case (soft delete — reversible).

        Args:
            test_case_id: qMetry test case ID or key.
        """
        with get_client() as c:
            return to_json(c.archive_test_case(test_case_id))

    @mcp.tool()
    def unarchive_test_case(test_case_id: str) -> str:
        """Restore an archived test case.

        Args:
            test_case_id: qMetry test case ID or key.
        """
        with get_client() as c:
            return to_json(c.unarchive_test_case(test_case_id))
