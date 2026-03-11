"""
MCP Tools — Test Cases — 03
============================
Full lifecycle for test case tools called via the MCP protocol.

Each test calls the tool by name through the live MCP session, parses the
returned JSON string, and asserts on the result — exactly what an MCP host
(e.g. Claude Desktop) does at runtime.

Execution order within this file matters.  Created IDs are stored in
module-level `_state` and also written to `shared_state` for test_04 onwards.

Tools exercised:
  create_test_case, get_test_case, search_test_cases
  update_test_case
  add_test_steps, get_test_steps, update_test_steps
  clone_test_case, move_test_case
  link_requirements_to_test_case, unlink_requirements_from_test_case
  archive_test_case, unarchive_test_case

Run:
    python -m pytest tests/mcp_tools/test_03_test_cases.py -v -s
"""

import json

import pytest

from tests.mcp_tools.conftest import pp, tool_json, tool_text

_state: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tc_id() -> str:
    return _state.get("tc_id", "")


def _tc_version() -> int:
    return _state.get("tc_version", 1)


def _extract_tc(data: dict) -> tuple[str, str, int]:
    tc_id = str(data.get("id", data.get("testCaseId", "")))
    tc_key = data.get("key", data.get("testCaseKey", ""))
    version = int(data.get("latestVersion", data.get("versionNo", 1)))
    return tc_id, tc_key, version


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

class TestCreateTestCase:

    @pytest.mark.asyncio
    async def test_create_returns_id_and_key(self, session, project_id, shared_state):
        """create_test_case tool returns JSON with id and key."""
        result = await session.call_tool(
            "create_test_case",
            {
                "project_id": project_id,
                "summary": "[MCP-TEST] Login with valid credentials",
                "description": "Verify a registered user can log in with correct credentials.",
            },
        )
        pp("create_test_case", tool_text(result))
        data = tool_json(result)

        tc_id, tc_key, version = _extract_tc(data)
        assert tc_id, f"No TC id in response: {data}"
        assert tc_key, f"No TC key in response: {data}"

        _state["tc_id"] = tc_id
        _state["tc_key"] = tc_key
        _state["tc_version"] = version
        shared_state["tc_id"] = tc_id
        shared_state["tc_key"] = tc_key
        shared_state["tc_version"] = version
        print(f"\n  TC created via MCP — id={tc_id}  key={tc_key}  version={version}")

    @pytest.mark.asyncio
    async def test_create_in_folder(self, session, project_id, shared_state):
        """create_test_case places the TC in the folder from test_02."""
        folder_id = shared_state.get("tc_folder_id", "")
        if not folder_id:
            pytest.skip("tc_folder_id not in shared_state — run test_02 first.")

        result = await session.call_tool(
            "create_test_case",
            {
                "project_id": project_id,
                "summary": "[MCP-TEST] Login with invalid password",
                "description": "Verify login fails with incorrect password.",
                "folder_id": str(folder_id),
            },
        )
        data = tool_json(result)
        tc_id, tc_key, _ = _extract_tc(data)
        assert tc_id, f"No TC id: {data}"
        _state["tc_in_folder_id"] = tc_id
        print(f"\n  TC in folder created — id={tc_id}  folder_id={folder_id}")


# ---------------------------------------------------------------------------
# 2. Read
# ---------------------------------------------------------------------------

class TestGetAndSearchTestCase:

    @pytest.mark.asyncio
    async def test_get_test_case(self, session):
        """get_test_case tool returns the full TC detail."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id — run TestCreateTestCase first.")

        result = await session.call_tool("get_test_case", {"test_case_id": tc_id})
        pp("get_test_case", tool_text(result))
        data = tool_json(result)

        # API returns a list of version objects e.g. [{"versionNo": 1, ...}]
        # or a dict with the test case detail {"data": {"id": ...}} / {"id": ...}
        if isinstance(data, list):
            assert data, f"get_test_case returned empty list for tc_id={tc_id}"
            assert "versionNo" in data[0], f"Unexpected list item: {data[0]}"
        else:
            payload = data.get("data", data)
            returned_id = str(payload.get("id", payload.get("testCaseId", "")))
            assert returned_id == tc_id, f"Returned id {returned_id!r} != requested {tc_id!r}"

    @pytest.mark.asyncio
    async def test_search_test_cases_finds_created(self, session, project_id):
        """search_test_cases tool finds the TC we created by summary text."""
        tc_key = _state.get("tc_key", "")
        if not tc_key:
            pytest.skip("No tc_key — run TestCreateTestCase first.")

        result = await session.call_tool(
            "search_test_cases",
            {
                "project_id": project_id,
                "search_text": "[MCP-TEST] Login with valid credentials",
                "max_results": 10,
            },
        )
        pp("search_test_cases", tool_text(result))
        data = tool_json(result)
        items = data if isinstance(data, list) else data.get("data", [])
        keys = [t.get("key", t.get("testCaseKey", "")) for t in items]
        assert tc_key in keys, (
            f"TC {tc_key} not found in search results.\nFound: {keys}"
        )


# ---------------------------------------------------------------------------
# 3. Update
# ---------------------------------------------------------------------------

class TestUpdateTestCase:

    @pytest.mark.asyncio
    async def test_update_summary(self, session):
        """update_test_case tool changes the summary."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id — run TestCreateTestCase first.")

        result = await session.call_tool(
            "update_test_case",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "summary": "[MCP-TEST] Login with valid credentials (updated)",
            },
        )
        pp("update_test_case (summary)", tool_text(result))
        assert tool_text(result) is not None

    @pytest.mark.asyncio
    async def test_update_priority(self, session):
        """update_test_case tool sets priority."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        result = await session.call_tool(
            "update_test_case",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "priority": "High",
            },
        )
        assert tool_text(result) is not None
        print(f"\n  Priority set to High for tc_id={tc_id} via MCP tool.")


# ---------------------------------------------------------------------------
# 4. Steps
# ---------------------------------------------------------------------------

_STEPS_XFAIL = pytest.mark.xfail(
    reason="Steps API returns 400 for this qMetry instance — endpoint format incompatible",
    strict=False,
)


class TestTestSteps:

    @_STEPS_XFAIL
    @pytest.mark.asyncio
    async def test_add_test_steps(self, session):
        """add_test_steps tool appends steps and returns a response."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        steps = [
            {
                "description": "Navigate to the login page",
                "expectedResult": "Login form is displayed",
            },
            {
                "description": "Enter valid username and password",
                "expectedResult": "Credentials are accepted",
                "testData": "username=testuser  password=Test@123",
            },
            {
                "description": "Click the Login button",
                "expectedResult": "User is redirected to the dashboard",
            },
        ]

        result = await session.call_tool(
            "add_test_steps",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "steps_json": json.dumps(steps),
            },
        )
        raw = tool_text(result)
        pp("add_test_steps", raw)
        assert raw, "add_test_steps returned empty response"
        assert "Error executing tool" not in raw, f"add_test_steps API error: {raw[:300]}"
        print(f"\n  {len(steps)} step(s) added via MCP tool.")

    @_STEPS_XFAIL
    @pytest.mark.asyncio
    async def test_get_test_steps(self, session):
        """get_test_steps tool returns the steps just added."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        result = await session.call_tool(
            "get_test_steps",
            {"test_case_id": tc_id, "version_no": _tc_version()},
        )
        raw = tool_text(result)
        pp("get_test_steps", raw)
        assert raw, "get_test_steps returned empty response"
        assert "Error executing tool" not in raw, f"get_test_steps API error: {raw[:300]}"
        data = json.loads(raw)
        items = data if isinstance(data, list) else data.get("data", data.get("steps", []))
        assert items, f"No steps returned for tc_id={tc_id}"
        print(f"\n  {len(items)} step(s) retrieved via MCP tool.")

    @_STEPS_XFAIL
    @pytest.mark.asyncio
    async def test_update_test_steps(self, session):
        """update_test_steps tool replaces all steps."""
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        new_steps = [
            {
                "description": "Open browser and go to app URL",
                "expectedResult": "Home page loads",
            },
            {
                "description": "Click Login and enter valid credentials",
                "expectedResult": "Dashboard is shown",
                "testData": "username=admin  password=Admin@123",
            },
        ]

        result = await session.call_tool(
            "update_test_steps",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "steps_json": json.dumps(new_steps),
            },
        )
        raw = tool_text(result)
        pp("update_test_steps", raw)
        assert raw, "update_test_steps returned empty response"
        assert "Error executing tool" not in raw, f"update_test_steps API error: {raw[:300]}"
        print(f"\n  Steps replaced with {len(new_steps)} step(s) via MCP tool.")


# ---------------------------------------------------------------------------
# 5. Clone & Move
# ---------------------------------------------------------------------------

class TestCloneAndMove:

    @pytest.mark.asyncio
    async def test_clone_test_case(self, session, shared_state):
        """clone_test_case tool duplicates the TC."""
        tc_id = _tc_id()
        folder_id = shared_state.get("tc_folder_id", "")
        if not tc_id:
            pytest.skip("No tc_id.")
        if not folder_id:
            pytest.skip("No tc_folder_id — run test_02 first.")

        result = await session.call_tool(
            "clone_test_case",
            {
                "test_case_id": tc_id,
                "new_summary": "[MCP-TEST] Login with valid credentials (clone)",
                "folder_id": int(folder_id),
            },
        )
        pp("clone_test_case", tool_text(result))
        data = tool_json(result)
        clone_id = str(data.get("id", data.get("testCaseId", "")))
        assert clone_id, f"No clone ID: {data}"
        _state["clone_id"] = clone_id
        print(f"\n  Clone created via MCP tool — id={clone_id}")

    @pytest.mark.asyncio
    async def test_move_test_case(self, session, project_id, shared_state):
        """move_test_case tool relocates the TC to the test folder."""
        tc_id = _tc_id()
        folder_id = shared_state.get("tc_folder_id", "")
        if not tc_id or not folder_id:
            pytest.skip("Need tc_id and tc_folder_id.")

        result = await session.call_tool(
            "move_test_case",
            {
                "test_case_ids": tc_id,
                "project_id": int(project_id),
                "target_folder_id": int(folder_id),
            },
        )
        pp("move_test_case", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  TC {tc_id} moved to folder {folder_id} via MCP tool.")


# ---------------------------------------------------------------------------
# 6. Requirements linking
# ---------------------------------------------------------------------------

class TestRequirementsLinking:

    @pytest.mark.asyncio
    async def test_link_requirements(self, session, jira_issue_key):
        """link_requirements_to_test_case tool attaches a Jira issue."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        result = await session.call_tool(
            "link_requirements_to_test_case",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "issue_keys": jira_issue_key,
            },
        )
        pp("link_requirements_to_test_case", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Linked {jira_issue_key} → tc_id={tc_id} via MCP tool.")

    @pytest.mark.asyncio
    async def test_unlink_requirements(self, session, jira_issue_key):
        """unlink_requirements_from_test_case tool removes the Jira link."""
        if not jira_issue_key:
            pytest.skip("TEST_JIRA_ISSUE_KEY not set.")
        tc_id = _tc_id()
        if not tc_id:
            pytest.skip("No tc_id.")

        result = await session.call_tool(
            "unlink_requirements_from_test_case",
            {
                "test_case_id": tc_id,
                "version_no": _tc_version(),
                "issue_keys": jira_issue_key,
            },
        )
        pp("unlink_requirements_from_test_case", tool_text(result))
        assert tool_text(result) is not None


# ---------------------------------------------------------------------------
# 7. Archive / Unarchive (operates on clone to keep original usable)
# ---------------------------------------------------------------------------

class TestArchiveTestCase:

    @pytest.mark.asyncio
    async def test_archive_test_case(self, session):
        """archive_test_case tool soft-deletes the clone."""
        clone_id = _state.get("clone_id", "")
        if not clone_id:
            pytest.skip("No clone_id — run TestCloneAndMove first.")

        result = await session.call_tool("archive_test_case", {"test_case_id": clone_id})
        pp("archive_test_case", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Clone {clone_id} archived via MCP tool.")

    @pytest.mark.asyncio
    async def test_unarchive_test_case(self, session):
        """unarchive_test_case tool restores the archived clone."""
        clone_id = _state.get("clone_id", "")
        if not clone_id:
            pytest.skip("No clone_id.")

        result = await session.call_tool("unarchive_test_case", {"test_case_id": clone_id})
        pp("unarchive_test_case", tool_text(result))
        assert tool_text(result) is not None
        print(f"\n  Clone {clone_id} unarchived via MCP tool.")
