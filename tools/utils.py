"""
Shared utilities for MCP tool modules.

This is the single import point for qmetry.client — no tool module should
import QMetryClient directly, keeping tool code decoupled from the client layer.
"""

import json
from typing import Any

from qmetry.client import QMetryClient


def get_client() -> QMetryClient:
    """Create a fresh client per call (stateless — reads env vars each time)."""
    return QMetryClient()


def to_json(data: Any) -> str:
    """Serialise an API response dict to a formatted JSON string for MCP content."""
    return json.dumps(data, indent=2, default=str)


def parse_csv(value: str) -> list[str]:
    """Parse a comma-separated string into a stripped, non-empty list.

    Example: "TC-1, TC-2, TC-3" → ["TC-1", "TC-2", "TC-3"]
    """
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_json(raw: str, field_name: str) -> tuple[Any, str | None]:
    """Parse a JSON string, returning (parsed_value, None) or (None, error_json).

    Usage:
        steps, err = parse_json(steps_json, "steps_json")
        if err:
            return err
    """
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, json.dumps({"error": f"Invalid JSON in {field_name}: {exc}"})
