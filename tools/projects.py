"""MCP tools — Projects."""

from mcp.server.fastmcp import FastMCP

from .utils import get_client, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_projects(project_name: str = "", max_results: int = 50) -> str:
        """List all qMetry-enabled Jira projects.

        Args:
            project_name: Optional name filter (partial match).
            max_results:  Maximum number of results to return (default 50).
        """
        with get_client() as c:
            return to_json(c.list_projects(project_name=project_name, max_results=max_results))
