"""
MCP tool registration package.

Each sub-module owns one domain and exposes a single register(mcp) function.
To add a new domain: create a new module with register(mcp), then add it here.
"""

from mcp.server.fastmcp import FastMCP

from . import (
    folders,
    metadata,
    pipeline,
    projects,
    requirements,
    test_cases,
    test_cycles,
    test_plans,
    test_steps,
)

_MODULES = [
    projects,
    test_cases,
    test_steps,
    requirements,
    test_cycles,
    test_plans,
    folders,
    metadata,
    pipeline,
]


def register_all(mcp: FastMCP) -> None:
    """Register every domain's MCP tools onto the given FastMCP instance."""
    for module in _MODULES:
        module.register(mcp)
