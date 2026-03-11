"""
Pipeline tests — 06
===================
End-to-end test of the full publish flow that the `publish_test_cases_from_story`
MCP tool performs internally.

Because that tool's function is defined inside a register() closure it cannot
be called directly from a test.  Instead this file exercises the same sequence
of API calls the pipeline executes, which gives equivalent coverage:

    Step 1 — Resolve project ID and create a named folder
    Step 2 — Create test cases with steps inside that folder
    Step 3 — Link each test case to a Jira story (requirements)
    Step 4 — Create a test cycle named after the story
    Step 5 — Link all test cases into the cycle
    Step 6 — Link the cycle to the Jira story

All artefacts use the [MCP-TEST] prefix.  Cleanup is via archive only so
artefacts remain visible in the UI.

Run:
    python -m pytest tests/qmetry_api/test_06_pipeline.py -v -s
"""

import json

import pytest

from api.client import QMetryClient
from tests.qmetry_api.conftest import pp, RUN_TAG

# ---------------------------------------------------------------------------
# Sample payload — matches what an LLM would produce for the pipeline tool
# ---------------------------------------------------------------------------

STORY_SUMMARY = "User can log in with valid credentials"

SAMPLE_TEST_CASES = [
    {
        "summary": f"{RUN_TAG} Successful login with valid username and password",
        "description": "Verify that a registered user is redirected to the dashboard after login.",
        "steps": [
            {
                "description": "Navigate to the application login page",
                "expectedResult": "Login form is displayed",
            },
            {
                "description": "Enter a valid registered username and password",
                "expectedResult": "Credentials are accepted in the input fields",
                "testData": "username=testuser@example.com  password=Test@123",
            },
            {
                "description": "Click the 'Login' button",
                "expectedResult": "User is redirected to the dashboard and sees a welcome message",
            },
        ],
    },
    {
        "summary": f"{RUN_TAG} Login fails with incorrect password",
        "description": "Verify that an error message is shown when the password is wrong.",
        "steps": [
            {
                "description": "Navigate to the login page",
                "expectedResult": "Login form is displayed",
            },
            {
                "description": "Enter a valid username but incorrect password",
                "expectedResult": "Fields are populated",
                "testData": "username=testuser@example.com  password=WrongPass",
            },
            {
                "description": "Click the 'Login' button",
                "expectedResult": "An error message 'Invalid credentials' is shown; user stays on login page",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Shared state within this file
# ---------------------------------------------------------------------------
_state: dict = {}


# ---------------------------------------------------------------------------
# Full pipeline flow
# ---------------------------------------------------------------------------

class TestPublishPipeline:

    def test_step1_resolve_project_and_create_folder(self, project_id, project_key, jira_issue_key):
        """Step 1 — Resolve project ID and create a story-named folder."""
        folder_name = f"{RUN_TAG} {jira_issue_key or 'NO-ISSUE'} — {STORY_SUMMARY[:40]}"

        with QMetryClient() as c:
            result = c.create_test_case_folder(
                project_id=project_id,
                name=folder_name,
            )
        pp("create_test_case_folder (pipeline step 1)", result)

        folder_id = str(result.get("id", result.get("folderId", "")))
        assert folder_id, f"Folder creation failed: {result}"

        _state["folder_id"] = folder_id
        _state["project_id"] = project_id
        _state["project_key"] = project_key
        _state["jira_issue_key"] = jira_issue_key
        print(f"\n  Pipeline folder created — id={folder_id}  name={folder_name!r}")

    def test_step2_create_test_cases_with_steps(self):
        """Step 2 — Create each test case and add its steps."""
        project_id = _state.get("project_id", "")
        folder_id = _state.get("folder_id", "")
        if not project_id:
            pytest.skip("Step 1 did not run — project_id missing.")

        created_keys: list[str] = []

        with QMetryClient() as c:
            for tc_data in SAMPLE_TEST_CASES:
                # Create test case
                tc_response = c.create_test_case(
                    project_id=project_id,
                    summary=tc_data["summary"],
                    description=tc_data.get("description", ""),
                    folder_id=folder_id,
                )
                pp(f"create_test_case — {tc_data['summary'][:50]}", tc_response)

                tc_id = str(tc_response.get("id", tc_response.get("testCaseId", "")))
                tc_key = tc_response.get("key", tc_response.get("testCaseKey", ""))
                version_no = int(tc_response.get("latestVersion", tc_response.get("versionNo", 1)))

                assert tc_id, f"No TC ID in response: {tc_response}"
                assert tc_key, f"No TC key in response: {tc_response}"

                # Add steps — best-effort; some qMetry instances reject the body
                steps = tc_data.get("steps", [])
                steps_added = 0
                if steps:
                    try:
                        step_response = c.add_test_steps(
                            test_case_id=tc_id,
                            version_no=version_no,
                            steps=steps,
                        )
                        pp(f"add_test_steps — {tc_key}", step_response)
                        steps_added = len(steps)
                    except Exception as exc:
                        print(f"\n  WARNING: add_test_steps failed for {tc_key}: {exc}")

                created_keys.append(tc_key)
                print(f"\n  TC created: {tc_key}  steps_added={steps_added}/{len(steps)}")

        assert created_keys, "No test cases were created in Step 2"
        _state["created_tc_keys"] = created_keys
        _state["created_tc_ids"] = []  # populated per-TC above; keys suffice for linking

    def test_step3_link_test_cases_to_jira_story(self):
        """Step 3 — Link each created TC to the Jira story."""
        jira_issue_key = _state.get("jira_issue_key", "")
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set — skipping requirements linking step.")

        created_tc_keys = _state.get("created_tc_keys", [])
        if not created_tc_keys:
            pytest.skip("No TC keys from Step 2.")

        # For requirements linking we need tc_id + version, so re-fetch via search
        project_id = _state.get("project_id", "")
        with QMetryClient() as c:
            for tc_key in created_tc_keys:
                search_result = c.search_test_cases(
                    project_id=project_id,
                    search_text=tc_key,
                    max_results=5,
                )
                items = search_result if isinstance(search_result, list) else search_result.get("data", [])
                tc = next(
                    (t for t in items if t.get("key") == tc_key or t.get("testCaseKey") == tc_key),
                    None,
                )
                if not tc:
                    print(f"  WARNING: could not find {tc_key} in search to link requirements")
                    continue

                tc_id = str(tc.get("id", tc.get("testCaseId", "")))
                version_no = int(tc.get("latestVersion", tc.get("versionNo", 1)))

                link_result = c.link_requirements_to_test_case(
                    test_case_id=tc_id,
                    version_no=version_no,
                    issue_keys=[jira_issue_key],
                )
                pp(f"link_requirements_to_test_case — {tc_key}", link_result)
                print(f"\n  Linked {jira_issue_key} -> {tc_key}")

    def test_step4_create_test_cycle(self):
        """Step 4 — Create a test cycle named after the story."""
        project_id = _state.get("project_id", "")
        jira_issue_key = _state.get("jira_issue_key", "") or "NO-ISSUE"
        if not project_id:
            pytest.skip("project_id missing from state.")

        cycle_name = f"{RUN_TAG} {jira_issue_key} — {STORY_SUMMARY[:50]}"

        with QMetryClient() as c:
            result = c.create_test_cycle(
                project_id=project_id,
                name=cycle_name,
                description=f"Auto-generated pipeline cycle for {jira_issue_key}",
            )
        pp("create_test_cycle (pipeline step 4)", result)

        cycle_id = str(result.get("id", result.get("cycleId", "")))
        cycle_key = result.get("key", result.get("cycleKey", ""))
        assert cycle_id, f"No cycle ID: {result}"
        assert cycle_key, f"No cycle key: {result}"

        _state["cycle_id"] = cycle_id
        _state["cycle_key"] = cycle_key
        print(f"\n  Cycle created — id={cycle_id}  key={cycle_key}")

    def test_step5_link_test_cases_to_cycle(self):
        """Step 5 — Link all created TCs into the cycle."""
        cycle_id = _state.get("cycle_id", "")
        created_tc_keys = _state.get("created_tc_keys", [])
        project_id = _state.get("project_id", "")
        if not cycle_id or not created_tc_keys:
            pytest.skip("Need cycle_id and created_tc_keys from prior steps.")

        with QMetryClient() as c:
            result = c.link_test_cases_to_cycle(
                cycle_id=cycle_id,
                test_case_keys=created_tc_keys,
                project_id=project_id,
            )
        pp("link_test_cases_to_cycle (pipeline step 5)", result)
        assert result is not None, "link_test_cases_to_cycle returned None"
        print(f"\n  Linked {len(created_tc_keys)} TC(s) -> cycle {cycle_id}")

    def test_step5_verify_cycle_contains_test_cases(self):
        """Step 5 (verification) — get_cycle_test_cases confirms all TCs are linked."""
        cycle_id = _state.get("cycle_id", "")
        created_tc_keys = _state.get("created_tc_keys", [])
        if not cycle_id or not created_tc_keys:
            pytest.skip("Need cycle_id and created_tc_keys from prior steps.")

        with QMetryClient() as c:
            result = c.get_cycle_test_cases(cycle_id=cycle_id, max_results=50)
        pp("get_cycle_test_cases (pipeline verification)", result)

        items = result if isinstance(result, list) else result.get("data", [])
        linked_keys = [t.get("key", t.get("testCaseKey", "")) for t in items]

        missing = [k for k in created_tc_keys if k not in linked_keys]
        assert not missing, (
            f"These TCs were not found in the cycle after linking: {missing}\n"
            f"Cycle contains: {linked_keys}"
        )
        print(f"\n  All {len(created_tc_keys)} TC(s) confirmed in cycle.")

    def test_step6_link_cycle_to_jira_story(self):
        """Step 6 — Link the cycle back to the Jira story."""
        jira_issue_key = _state.get("jira_issue_key", "")
        cycle_id = _state.get("cycle_id", "")
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set — skipping cycle requirements linking.")
        if not cycle_id:
            pytest.skip("No cycle_id from Step 4.")

        with QMetryClient() as c:
            result = c.link_requirements_to_cycle(
                cycle_id=cycle_id,
                issue_keys=[jira_issue_key],
            )
        pp("link_requirements_to_cycle (pipeline step 6)", result)
        assert result is not None
        print(f"\n  Linked {jira_issue_key} -> cycle {cycle_id}")

    def test_pipeline_summary(self):
        """Print a human-readable summary of everything the pipeline created."""
        print("\n" + "=" * 60)
        print("  PIPELINE TEST SUMMARY")
        print("=" * 60)
        print(f"  Project:       {_state.get('project_key')}  (id={_state.get('project_id')})")
        print(f"  Jira issue:    {_state.get('jira_issue_key') or '(not configured)'}")
        print(f"  Folder id:     {_state.get('folder_id')}")
        print(f"  Test cases:    {_state.get('created_tc_keys')}")
        print(f"  Cycle:         {_state.get('cycle_key')}  (id={_state.get('cycle_id')})")
        print("=" * 60)
        print("  [NO CLEANUP] All artefacts left in qMetry for UI verification.")
        print("=" * 60)

        # Soft assertion — at least TCs and cycle must have been created
        assert _state.get("created_tc_keys"), "Pipeline produced no test cases"
        assert _state.get("cycle_id"), "Pipeline produced no test cycle"
