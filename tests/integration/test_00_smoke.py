"""
Smoke tests — 00
================
Verify basic connectivity before any write operations run.

Checks:
  - QMETRY_API_KEY is set
  - list_projects returns at least one project
  - TEST_PROJECT_KEY resolves to a real project
  - TEST_JIRA_ISSUE_KEY is configured (warns if missing)

Run:
    python -m pytest tests/integration/test_00_smoke.py -v -s
"""

import os

import pytest

from api.client import QMetryClient
from tests.integration.conftest import pp


class TestSmoke:

    def test_api_key_is_configured(self):
        """QMETRY_API_KEY must be present in the environment."""
        key = os.environ.get("QMETRY_API_KEY", "")
        assert key, (
            "QMETRY_API_KEY is not set.\n"
            "Add it to your .env file: QMETRY_API_KEY=your-key-here"
        )
        assert key != "your-qmetry-api-key-here", (
            "QMETRY_API_KEY still has the placeholder value from .env.example.\n"
            "Replace it with your real API key."
        )
        print(f"\n  QMETRY_API_KEY is set (length={len(key)})")

    def test_base_url_is_configured(self):
        """QMETRY_BASE_URL should be set (has a default, but log what's in use)."""
        url = os.environ.get("QMETRY_BASE_URL", "https://qtmcloud.qmetry.com/rest/api/latest/")
        print(f"\n  QMETRY_BASE_URL = {url}")
        assert url.startswith("http"), f"QMETRY_BASE_URL looks invalid: {url}"

    def test_list_projects_returns_results(self):
        """list_projects must return at least one qMetry-enabled project."""
        with QMetryClient() as c:
            result = c.list_projects(max_results=10)

        pp("list_projects", result)
        items = result if isinstance(result, list) else result.get("data", result.get("results", []))
        assert items, (
            "list_projects returned an empty list.\n"
            "Ensure your API key has access to at least one qMetry project."
        )
        print(f"\n  Found {len(items)} project(s).")

    def test_target_project_is_accessible(self, project_id, project_key):
        """The project specified by TEST_PROJECT_KEY must be reachable."""
        print(f"\n  Target project: key={project_key}  id={project_id}")
        assert project_id, "Could not resolve a numeric project ID"
        assert project_key, "Could not resolve a project key"

    def test_jira_issue_key_is_configured(self, jira_issue_key, project_key):
        """Warn (but do not fail) if TEST_JIRA_ISSUE_KEY is missing."""
        if not jira_issue_key:
            pytest.skip(
                "TEST_JIRA_ISSUE_KEY is not set in .env.\n"
                f"Add any existing Jira issue key from project {project_key}, "
                f"e.g.  TEST_JIRA_ISSUE_KEY={project_key}-1\n"
                "Requirements-linking tests will be skipped."
            )
        print(f"\n  TEST_JIRA_ISSUE_KEY = {jira_issue_key}")
