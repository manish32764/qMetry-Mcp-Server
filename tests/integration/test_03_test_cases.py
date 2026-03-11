"""
Test Case tests — 03
====================
Full CRUD lifecycle for a test case, plus steps and requirements linking.

Execution order within the file matters — each test builds on the previous one
using class-level state.  The created test case's ID/key is also written into
shared_state so test_04 can link it into a cycle without re-creating it.

Tools exercised:
  create_test_case, get_test_case, search_test_cases
  update_test_case
  add_test_steps, get_test_steps, update_test_steps
  clone_test_case, move_test_case
  link_requirements_to_test_case, unlink_requirements_from_test_case
  archive_test_case, unarchive_test_case

Run:
    python -m pytest tests/integration/test_03_test_cases.py -v -s
"""

import pytest

from api.client import QMetryClient
from tests.integration.conftest import pp

# ---------------------------------------------------------------------------
# Shared within-file state — populated by tests in order
# ---------------------------------------------------------------------------
_state: dict = {}


def _get_tc_id() -> str:
    return _state.get("tc_id", "")


def _get_tc_version() -> int:
    return _state.get("tc_version", 1)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _extract_tc(response: dict) -> tuple[str, str, int]:
    """Return (tc_id, tc_key, version_no) from a create/get response."""
    tc_id = str(response.get("id", response.get("testCaseId", "")))
    tc_key = response.get("key", response.get("testCaseKey", ""))
    version_no = int(response.get("latestVersion", response.get("versionNo", 1)))
    return tc_id, tc_key, version_no


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestCase:

    def test_create_returns_id_and_key(self, project_id, shared_state):
        """create_test_case returns a response with id and key."""
        with QMetryClient() as c:
            result = c.create_test_case(
                project_id=project_id,
                summary="[MCP-TEST] Login with valid credentials",
                description="Verify that a registered user can log in using correct username and password.",
            )
        pp("create_test_case", result)

        tc_id, tc_key, version_no = _extract_tc(result)
        assert tc_id, f"No test case ID in response: {result}"
        assert tc_key, f"No test case key in response: {result}"

        # Save for subsequent tests in this file and in shared_state for test_04
        _state["tc_id"] = tc_id
        _state["tc_key"] = tc_key
        _state["tc_version"] = version_no
        shared_state["tc_id"] = tc_id
        shared_state["tc_key"] = tc_key
        shared_state["tc_version"] = version_no

        print(f"\n  Test case created — id={tc_id}  key={tc_key}  version={version_no}")

    def test_create_in_folder(self, project_id, shared_state):
        """create_test_case places the TC in the folder created by test_02."""
        folder_id = shared_state.get("tc_folder_id", "")
        if not folder_id:
            pytest.skip("tc_folder_id not in shared_state — run test_02 first (or run the full suite).")

        with QMetryClient() as c:
            result = c.create_test_case(
                project_id=project_id,
                summary="[MCP-TEST] Login with invalid password",
                description="Verify that login fails with incorrect password.",
                folder_id=str(folder_id),
            )
        pp("create_test_case (with folder)", result)

        tc_id, tc_key, _ = _extract_tc(result)
        assert tc_id, f"No test case ID: {result}"
        _state["tc_in_folder_id"] = tc_id
        _state["tc_in_folder_key"] = tc_key
        print(f"\n  Test case in folder created — id={tc_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestCase:

    def test_get_test_case_by_id(self):
        """get_test_case returns full details of the created test case."""
        tc_id = _get_tc_id()
        if not tc_id:
            pytest.skip("No tc_id in state — run TestCreateTestCase first.")

        with QMetryClient() as c:
            result = c.get_test_case(test_case_id=tc_id)
        pp("get_test_case", result)

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        returned_id = str(result.get("id", result.get("testCaseId", "")))
        assert returned_id == tc_id, f"Returned id {returned_id} != requested {tc_id}"

    def test_search_finds_created_test_case(self, project_id):
        """search_test_cases with the TC summary finds the created test case."""
        tc_key = _state.get("tc_key", "")
        if not tc_key:
            pytest.skip("No tc_key in state — run TestCreateTestCase first.")

        with QMetryClient() as c:
            result = c.search_test_cases(
                project_id=project_id,
                search_text="[MCP-TEST] Login with valid credentials",
                max_results=10,
            )
        pp("search_test_cases", result)

        items = result if isinstance(result, list) else result.get("data", [])
        keys = [t.get("key", t.get("testCaseKey", "")) for t in items]
        assert tc_key in keys, (
            f"Created test case {tc_key} not found in search results.\n"
            f"Found keys: {keys}"
        )


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestCase:

    def test_update_summary_and_description(self):
        """update_test_case changes summary and description."""
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state — run TestCreateTestCase first.")

        with QMetryClient() as c:
            result = c.update_test_case(
                test_case_id=tc_id,
                version_no=version_no,
                summary="[MCP-TEST] Login with valid credentials (updated)",
                description="Updated: Verify successful login with correct credentials.",
            )
        pp("update_test_case (summary + description)", result)
        assert result is not None, "update_test_case returned None"

    def test_update_priority(self):
        """update_test_case can set priority."""
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        with QMetryClient() as c:
            result = c.update_test_case(
                test_case_id=tc_id,
                version_no=version_no,
                priority="High",
            )
        pp("update_test_case (priority=High)", result)
        assert result is not None


# ---------------------------------------------------------------------------
# 4. Steps
# ---------------------------------------------------------------------------

class TestTestSteps:

    def test_add_test_steps(self):
        """add_test_steps appends steps to the test case."""
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        steps = [
            {
                "description": "Navigate to the login page",
                "expectedResult": "Login page is displayed with username and password fields",
            },
            {
                "description": "Enter valid username and password",
                "expectedResult": "Credentials are accepted",
                "testData": "username=testuser, password=Test@123",
            },
            {
                "description": "Click the Login button",
                "expectedResult": "User is redirected to the dashboard",
            },
        ]

        with QMetryClient() as c:
            result = c.add_test_steps(
                test_case_id=tc_id,
                version_no=version_no,
                steps=steps,
            )
        pp("add_test_steps", result)
        assert result is not None, "add_test_steps returned None"
        print(f"\n  {len(steps)} step(s) added to tc_id={tc_id}")

    def test_get_test_steps_returns_added_steps(self):
        """get_test_steps returns the steps just added."""
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        with QMetryClient() as c:
            result = c.get_test_steps(test_case_id=tc_id, version_no=version_no)
        pp("get_test_steps", result)

        items = result if isinstance(result, list) else result.get("data", result.get("steps", []))
        assert items, f"No steps returned for tc_id={tc_id}, version={version_no}"
        print(f"\n  {len(items)} step(s) retrieved.")

    def test_update_test_steps_replaces_all(self):
        """update_test_steps replaces all existing steps."""
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        new_steps = [
            {
                "description": "Open browser and navigate to application URL",
                "expectedResult": "Application home page loads",
            },
            {
                "description": "Click Login and enter valid credentials",
                "expectedResult": "Dashboard is shown",
                "testData": "username=admin, password=Admin@123",
            },
        ]

        with QMetryClient() as c:
            result = c.update_test_steps(
                test_case_id=tc_id,
                version_no=version_no,
                steps=new_steps,
            )
        pp("update_test_steps", result)
        assert result is not None, "update_test_steps returned None"
        print(f"\n  Steps replaced with {len(new_steps)} new step(s).")


# ---------------------------------------------------------------------------
# 5. Clone & Move
# ---------------------------------------------------------------------------

class TestCloneAndMove:

    def test_clone_test_case(self, project_id, shared_state):
        """clone_test_case creates a duplicate of the original TC."""
        tc_id = _get_tc_id()
        folder_id = shared_state.get("tc_folder_id", "")
        if not tc_id:
            pytest.skip("No tc_id in state.")
        if not folder_id:
            pytest.skip("No tc_folder_id in shared_state — run test_02 first.")

        with QMetryClient() as c:
            result = c.clone_test_case(
                test_case_id=tc_id,
                new_summary="[MCP-TEST] Login with valid credentials (clone)",
                folder_id=int(folder_id),
            )
        pp("clone_test_case", result)

        clone_id = str(result.get("id", result.get("testCaseId", "")))
        assert clone_id, f"No clone ID in response: {result}"
        _state["clone_id"] = clone_id
        _state["clone_key"] = result.get("key", result.get("testCaseKey", ""))
        print(f"\n  Clone created — id={clone_id}")

    def test_move_test_case_to_folder(self, project_id, shared_state):
        """move_test_case relocates the original TC to the test folder."""
        tc_id = _get_tc_id()
        folder_id = shared_state.get("tc_folder_id", "")
        if not tc_id or not folder_id:
            pytest.skip("Need tc_id and tc_folder_id — run prior tests first.")

        with QMetryClient() as c:
            result = c.move_test_case(
                test_case_ids=[tc_id],
                project_id=int(project_id),
                target_folder_id=int(folder_id),
            )
        pp("move_test_case", result)
        assert result is not None, "move_test_case returned None"
        print(f"\n  Test case {tc_id} moved to folder {folder_id}.")


# ---------------------------------------------------------------------------
# 6. Requirements linking
# ---------------------------------------------------------------------------

class TestRequirementsLinking:

    def test_link_requirements_to_test_case(self, jira_issue_key):
        """link_requirements_to_test_case attaches a Jira issue to the TC."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set — skipping requirements linking.")
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        with QMetryClient() as c:
            result = c.link_requirements_to_test_case(
                test_case_id=tc_id,
                version_no=version_no,
                issue_keys=[jira_issue_key],
            )
        pp("link_requirements_to_test_case", result)
        assert result is not None, "link_requirements_to_test_case returned None"
        print(f"\n  Linked {jira_issue_key} → tc_id={tc_id}")

    def test_unlink_requirements_from_test_case(self, jira_issue_key):
        """unlink_requirements_from_test_case removes the Jira issue link."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set — skipping.")
        tc_id = _get_tc_id()
        version_no = _get_tc_version()
        if not tc_id:
            pytest.skip("No tc_id in state.")

        with QMetryClient() as c:
            result = c.unlink_requirements_from_test_case(
                test_case_id=tc_id,
                version_no=version_no,
                issue_keys=[jira_issue_key],
            )
        pp("unlink_requirements_from_test_case", result)
        assert result is not None, "unlink_requirements_from_test_case returned None"
        print(f"\n  Unlinked {jira_issue_key} from tc_id={tc_id}")


# ---------------------------------------------------------------------------
# 7. Archive / Unarchive (uses clone so the original stays usable)
# ---------------------------------------------------------------------------

class TestArchiveTestCase:

    def test_archive_test_case(self):
        """archive_test_case soft-deletes the clone."""
        clone_id = _state.get("clone_id", "")
        if not clone_id:
            pytest.skip("No clone_id in state — run TestCloneAndMove first.")

        with QMetryClient() as c:
            result = c.archive_test_case(test_case_id=clone_id)
        pp("archive_test_case (clone)", result)
        assert result is not None, "archive_test_case returned None"
        print(f"\n  Clone {clone_id} archived.")

    def test_unarchive_test_case(self):
        """unarchive_test_case restores the archived clone."""
        clone_id = _state.get("clone_id", "")
        if not clone_id:
            pytest.skip("No clone_id in state.")

        with QMetryClient() as c:
            result = c.unarchive_test_case(test_case_id=clone_id)
        pp("unarchive_test_case (clone)", result)
        assert result is not None, "unarchive_test_case returned None"
        print(f"\n  Clone {clone_id} unarchived.")
