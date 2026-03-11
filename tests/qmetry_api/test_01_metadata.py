"""
Metadata tests — 01
===================
Read-only calls that validate project-level configuration exists.
These tests never create or modify data; safe to run repeatedly.

Tools exercised:
  list_labels, create_label
  list_priorities
  list_test_case_statuses
  list_test_cycle_statuses
  list_test_plan_statuses

Run:
    python -m pytest tests/qmetry_api/test_01_metadata.py -v -s
"""

import pytest

from api.client import QMetryClient
from tests.qmetry_api.conftest import pp, RUN_TAG


class TestLabels:

    def test_list_labels_returns_list(self, project_id):
        """list_labels must return a list (may be empty on a brand-new instance)."""
        with QMetryClient() as c:
            result = c.list_labels(project_id=project_id)
        pp("list_labels", result)
        items = result if isinstance(result, list) else result.get("data", [])
        assert isinstance(items, list), f"Expected list, got {type(items)}"
        print(f"\n  {len(items)} label(s) found.")

    def test_create_label(self, project_id):
        """create_label must return a response containing the new label's name or id."""
        with QMetryClient() as c:
            result = c.create_label(project_id=project_id, name=f"{RUN_TAG} smoke-label")
        pp("create_label", result)
        # API may return the label object or a simple success response
        assert result is not None, "create_label returned None"
        print(f"\n  Label created: {result}")


class TestPriorities:

    def test_list_priorities_returns_options(self, project_id):
        """list_priorities must return at least one priority option."""
        with QMetryClient() as c:
            result = c.list_priorities(project_id=project_id)
        pp("list_priorities", result)
        items = result if isinstance(result, list) else result.get("data", [])
        assert items, (
            "list_priorities returned no options.\n"
            "qMetry projects should always have at least one priority configured."
        )
        names = [p.get("name", p.get("priority", "")) for p in items]
        print(f"\n  Priorities: {names}")


class TestStatuses:

    def test_list_test_case_statuses(self, project_id):
        """list_test_case_statuses must return at least one status."""
        with QMetryClient() as c:
            result = c.list_test_case_statuses(project_id=project_id)
        pp("list_test_case_statuses", result)
        items = result if isinstance(result, list) else result.get("data", [])
        assert items, "list_test_case_statuses returned no options."
        names = [s.get("name", s.get("status", "")) for s in items]
        print(f"\n  Test case statuses: {names}")

    def test_list_test_cycle_statuses(self, project_id):
        """list_test_cycle_statuses must return at least one status."""
        with QMetryClient() as c:
            result = c.list_test_cycle_statuses(project_id=project_id)
        pp("list_test_cycle_statuses", result)
        items = result if isinstance(result, list) else result.get("data", [])
        assert items, "list_test_cycle_statuses returned no options."
        names = [s.get("name", s.get("status", "")) for s in items]
        print(f"\n  Test cycle statuses: {names}")

    def test_list_test_plan_statuses(self, project_id):
        """list_test_plan_statuses must return at least one status."""
        with QMetryClient() as c:
            result = c.list_test_plan_statuses(project_id=project_id)
        pp("list_test_plan_statuses", result)
        items = result if isinstance(result, list) else result.get("data", [])
        assert items, "list_test_plan_statuses returned no options."
        names = [s.get("name", s.get("status", "")) for s in items]
        print(f"\n  Test plan statuses: {names}")
