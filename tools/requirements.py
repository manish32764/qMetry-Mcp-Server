"""MCP tools — Requirements linking (Jira issues ↔ Test Cases)."""

from mcp.server.fastmcp import FastMCP

from .utils import get_client, parse_csv, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def link_requirements_to_test_case(
        test_case_id: str, version_no: int, issue_keys: str
    ) -> str:
        """Link one or more Jira issues (user stories, bugs) to a test case.

        This creates traceability: Jira story → test case.
        Call this after create_test_case and add_test_steps.

        Args:
            test_case_id: qMetry test case ID.
            version_no:   Version number (use 1 for newly created test cases).
            issue_keys:   Comma-separated Jira issue keys (e.g. "PROJ-123,PROJ-124").
        """
        with get_client() as c:
            return to_json(
                c.link_requirements_to_test_case(
                    test_case_id, version_no, parse_csv(issue_keys)
                )
            )

    @mcp.tool()
    def unlink_requirements_from_test_case(
        test_case_id: str, version_no: int, issue_keys: str
    ) -> str:
        """Remove Jira issue links from a test case.

        Args:
            test_case_id: qMetry test case ID.
            version_no:   Version number.
            issue_keys:   Comma-separated Jira issue keys to unlink.
        """
        with get_client() as c:
            return to_json(
                c.unlink_requirements_from_test_case(
                    test_case_id, version_no, parse_csv(issue_keys)
                )
            )
