"""MCP tools — Test Steps (get, add, update)."""

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ..helpers import parse_json, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_test_steps(test_case_id: str, version_no: int = 1) -> str:
        """Get all test steps for a test case version.

        Args:
            test_case_id: qMetry test case ID.
            version_no:   Version number (default 1).
        """
        with get_client() as c:
            return to_json(c.get_test_steps(test_case_id, version_no))

    @mcp.tool()
    def add_test_steps(test_case_id: str, version_no: int, steps_json: str) -> str:
        """Add test steps to a test case.

        Call this immediately after create_test_case.

        Args:
            test_case_id: qMetry test case ID (returned by create_test_case).
            version_no:   Version number (use 1 for newly created test cases).
            steps_json:   JSON array of step objects. Each object must have:
                            - "description"    : string — the action to perform
                            - "expectedResult" : string — the expected outcome
                            - "testData"       : string (optional) — test data

                          Example:
                            [
                              {"description": "Open login page", "expectedResult": "Page loads"},
                              {"description": "Enter credentials", "expectedResult": "Fields accept input"},
                              {"description": "Click Login", "expectedResult": "Dashboard is shown"}
                            ]
        """
        steps, err = parse_json(steps_json, "steps_json")
        if err:
            return err
        with get_client() as c:
            return to_json(c.add_test_steps(test_case_id, version_no, steps))

    @mcp.tool()
    def update_test_steps(test_case_id: str, version_no: int, steps_json: str) -> str:
        """Replace ALL test steps for a test case version.

        Args:
            test_case_id: qMetry test case ID.
            version_no:   Version number.
            steps_json:   JSON array of step objects (same format as add_test_steps).
                          This REPLACES all existing steps.
        """
        steps, err = parse_json(steps_json, "steps_json")
        if err:
            return err
        with get_client() as c:
            return to_json(c.update_test_steps(test_case_id, version_no, steps))
