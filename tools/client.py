"""
QMetryClient factory for MCP tool modules.

This is the single import point for api.client — no tool module should
import QMetryClient directly, keeping tool code decoupled from the client layer.
"""

from api.client import QMetryClient


def get_client() -> QMetryClient:
    """Create a fresh client per call (stateless — reads env vars each time)."""
    return QMetryClient()
