"""
MCP Tools — Pipeline — 06
==========================
Tests the `publish_test_cases_from_story` composite tool via the MCP protocol.

This is the most end-to-end test in the suite: a single tool call triggers
folder creation, TC creation, step addition, requirements linking, cycle
creation, TC-to-cycle linking, and cycle-to-story linking — all inside the
server process, exactly as an MCP host would invoke it.

Tools exercised:
  publish_test_cases_from_story

Run:
    python -m pytest tests/mcp_tools/test_06_pipeline.py -v -s
"""

import json

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text

# ---------------------------------------------------------------------------
# Payload — matches what an LLM would pass to the pipeline tool
# ---------------------------------------------------------------------------

STORY_SUMMARY = "User can log in with valid credentials"

PIPELINE_TEST_CASES = [
    {
        "summary": "[MCP-TEST] Successful login with valid credentials",
        "description": "Verify the user is redirected to the dashboard after login.",
        "steps": [
            {
                "description": "Navigate to the login page",
                "expectedResult": "Login form is displayed",
            },
            {
                "description": "Enter valid username and password",
                "expectedResult": "Credentials accepted",
                "testData": "username=testuser@example.com  password=Test@123",
            },
            {
                "description": "Click the Login button",
                "expectedResult": "User is redirected to the dashboard",
            },
        ],
    },
    {
        "summary": "[MCP-TEST] Login fails with incorrect password",
        "description": "Verify an error message appears when the password is wrong.",
        "steps": [
            {
                "description": "Navigate to the login page",
                "expectedResult": "Login form is displayed",
            },
            {
                "description": "Enter valid username but wrong password",
                "expectedResult": "Fields populated",
                "testData": "username=testuser@example.com  password=WrongPass",
            },
            {
                "description": "Click the Login button",
                "expectedResult": "'Invalid credentials' error shown; user stays on login page",
            },
        ],
    },
]


class TestPublishPipeline:

    @pytest.mark.asyncio
    async def test_pipeline_requires_jira_issue(self, jira_issue_key):
        """Skip the pipeline test if TEST_JIRA_ISSUE_KEY is not configured."""
        if not jira_issue_key:
            pytest.skip(
                "TEST_JIRA_ISSUE_KEY not set — pipeline test requires a valid Jira issue key.\n"
                "Add TEST_JIRA_ISSUE_KEY=PROJ-1 to your .env and re-run."
            )

    @pytest.mark.asyncio
    async def test_publish_test_cases_from_story(
        self, session, project_key, jira_issue_key, shared_state
    ):
        """
        publish_test_cases_from_story executes the full 6-step pipeline in one
        tool call and returns a JSON summary with published TC keys and a cycle key.
        """
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")

        folder_name = f"[MCP-TEST] {jira_issue_key} — {STORY_SUMMARY[:40]}"

        result = await session.call_tool(
            "publish_test_cases_from_story",
            {
                "project_key": project_key,
                "story_key": jira_issue_key,
                "story_summary": STORY_SUMMARY,
                "test_cases_json": json.dumps(PIPELINE_TEST_CASES),
                "folder_name": folder_name,
                "create_cycle": True,
            },
        )

        raw = tool_text(result)
        pp("publish_test_cases_from_story", raw)

        data = tool_json(result)

        # --- Assertions ---
        errors = data.get("errors", [])
        assert not errors, (
            f"Pipeline reported errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )

        published = data.get("published", [])
        assert len(published) == len(PIPELINE_TEST_CASES), (
            f"Expected {len(PIPELINE_TEST_CASES)} TCs published, got {len(published)}.\n"
            f"Published: {published}"
        )

        cycle_key = data.get("cycle_key")
        assert cycle_key, f"No cycle_key in pipeline response: {data}"

        # Store for summary
        shared_state["pipeline_published"] = published
        shared_state["pipeline_cycle_key"] = cycle_key

        print("\n" + "=" * 60)
        print("  PIPELINE TOOL RESULT")
        print("=" * 60)
        print(f"  story_key  : {jira_issue_key}")
        print(f"  folder     : {data.get('folder_name')}")
        print(f"  TCs created: {[tc['key'] for tc in published]}")
        print(f"  cycle_key  : {cycle_key}")
        print("=" * 60)
        print("  [NO CLEANUP] Artefacts left in qMetry for UI verification.")
        print("=" * 60)

    @pytest.mark.asyncio
    async def test_pipeline_published_keys_are_non_empty(self, shared_state):
        """Each published entry must have a non-empty key and step count."""
        published = shared_state.get("pipeline_published")
        if published is None:
            pytest.skip("Pipeline test did not run — skipping verification.")

        for entry in published:
            assert entry.get("key"), f"Published TC has no key: {entry}"
            assert entry.get("summary"), f"Published TC has no summary: {entry}"
            assert isinstance(entry.get("steps_count"), int), (
                f"steps_count missing or not int: {entry}"
            )

        print(f"\n  All {len(published)} published TC(s) have valid keys and step counts.")

    @pytest.mark.asyncio
    async def test_pipeline_without_cycle(self, session, project_key, jira_issue_key):
        """publish_test_cases_from_story with create_cycle=False creates TCs but no cycle."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")

        result = await session.call_tool(
            "publish_test_cases_from_story",
            {
                "project_key": project_key,
                "story_key": jira_issue_key,
                "story_summary": STORY_SUMMARY,
                "test_cases_json": json.dumps([PIPELINE_TEST_CASES[0]]),
                "create_cycle": False,
            },
        )
        pp("publish_test_cases_from_story (no cycle)", tool_text(result))
        data = tool_json(result)

        errors = data.get("errors", [])
        assert not errors, f"Pipeline errors: {errors}"

        published = data.get("published", [])
        assert published, "No TCs published."

        cycle_key = data.get("cycle_key")
        assert cycle_key is None, (
            f"Expected no cycle when create_cycle=False, but got: {cycle_key}"
        )
        print(f"\n  TC created without cycle — key={published[0].get('key')}")
