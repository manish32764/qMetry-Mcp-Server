"""
qMetry Test Management MCP Server
===================================
Exposes qMetry REST API (https://qtmcloud.qmetry.com/rest/api/latest/) as MCP tools.

Environment variables required:
  QMETRY_API_KEY   — your qMetry API key (Jira → QMetry → Configuration → Open API → Generate)
  QMETRY_BASE_URL  — (optional) override base URL, default: https://qtmcloud.qmetry.com/rest/api/latest/

Run (stdio — for any MCP client):
  python server.py

Run (HTTP — for direct programmatic access):
  python server.py --http --port 8000
"""

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from tools import register_all

mcp = FastMCP(
    "qmetry-test-manager",
    description=(
        "Test Management tools for qMetry: create and manage test cases, "
        "test steps, test cycles, test plans, folders, and Jira requirement links."
    ),
)

register_all(mcp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="qMetry Test Management MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server (Streamable HTTP)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.http:
        print(f"Starting qMetry MCP server (HTTP) on {args.host}:{args.port}", file=sys.stderr)
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
