"""
pytest configuration for the mcp_tools test suite.

This suite starts server.py as a real subprocess via stdio and connects to it
using the MCP Python client SDK — the same path any MCP host (e.g. Claude
Desktop) takes when calling the tools.

Every async test receives a fully initialised `session` fixture (ClientSession)
and a `project_id` / `project_key` pair resolved once per session.

Run from the qmetry_mcp/ directory:
    python -m pytest tests/mcp_tools/ -v -s

Requirements:
    pip install pytest-asyncio>=0.23.0   (already in requirements.txt)
"""

import asyncio
import inspect
import json
import os
import sys

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Bootstrap: ensure qmetry_mcp/ is on sys.path
# ---------------------------------------------------------------------------
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

# Load .env before anything reads env vars
_env_file = os.path.join(_PKG_ROOT, ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client              # noqa: E402

# ---------------------------------------------------------------------------
# pytest-asyncio mode
# ---------------------------------------------------------------------------
pytest_plugins = ["pytest_asyncio"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pp(label: str, data) -> None:
    """Print labelled JSON — useful when running with -s."""
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            pass
    print(json.dumps(data, indent=2, default=str))


def tool_text(result) -> str:
    """Extract the text string from a CallToolResult."""
    if hasattr(result, "content") and result.content:
        return result.content[0].text
    return str(result)


def tool_json(result) -> dict | list:
    """Parse the JSON text from a CallToolResult."""
    return json.loads(tool_text(result))


# ---------------------------------------------------------------------------
# Server parameters — how to start server.py
# ---------------------------------------------------------------------------

def _server_params() -> StdioServerParameters:
    server_script = os.path.join(_PKG_ROOT, "server.py")
    return StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env={**os.environ},   # forward all env vars including QMETRY_API_KEY
    )


# ---------------------------------------------------------------------------
# MCP ClientSession — started once, shared across all tests
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def session():
    """
    Start server.py via stdio and return an initialised MCP ClientSession.

    The server process lives for the entire test session and is terminated
    when the session ends.

    The stdio_client uses anyio TaskGroups whose cancel scopes must be entered
    and exited in the same asyncio Task.  Running the entire lifecycle inside a
    dedicated task satisfies that constraint and avoids the
    "Attempted to exit cancel scope in a different task" teardown error that
    pytest-asyncio 1.x would otherwise trigger.
    """
    client_queue: asyncio.Queue = asyncio.Queue()
    shutdown_event: asyncio.Event = asyncio.Event()

    async def _run() -> None:
        params = _server_params()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                print("\n[conftest] MCP server started and session initialised.")
                await client_queue.put(client)
                await shutdown_event.wait()  # keep alive until tests finish

    task = asyncio.ensure_future(_run())
    client = await client_queue.get()
    yield client
    shutdown_event.set()
    await task


# ---------------------------------------------------------------------------
# Project resolution — same logic as qmetry_api/conftest.py but via MCP tool
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def project_id_and_key(session, shared_state):
    target_key = os.environ.get("TEST_PROJECT_KEY", "").strip()

    result = await session.call_tool("list_projects", {"max_results": 50})
    data = tool_json(result)
    items = data if isinstance(data, list) else data.get("data", data.get("results", []))

    assert items, (
        "list_projects returned no projects.\n"
        "Check QMETRY_API_KEY and QMETRY_BASE_URL in your .env file."
    )

    project = None
    if target_key:
        for p in items:
            if p.get("key") == target_key or p.get("projectKey") == target_key:
                project = p
                break
        if project is None:
            pytest.fail(
                f"TEST_PROJECT_KEY='{target_key}' not found in qMetry.\n"
                f"Available: {[p.get('key') for p in items]}"
            )
    else:
        project = items[0]

    pid = str(project.get("id", project.get("projectId", "")))
    pkey = project.get("key", project.get("projectKey", ""))
    assert pid, f"Could not determine project ID from: {project}"

    shared_state["project_id"] = pid
    shared_state["project_key"] = pkey
    print(f"\n[conftest] Using project: key={pkey}  id={pid}")
    return pid, pkey


@pytest_asyncio.fixture(scope="session")
async def project_id(project_id_and_key):
    return project_id_and_key[0]


@pytest_asyncio.fixture(scope="session")
async def project_key(project_id_and_key):
    return project_id_and_key[1]


@pytest.fixture(scope="session")
def jira_issue_key() -> str:
    return os.environ.get("TEST_JIRA_ISSUE_KEY", "").strip()


@pytest.fixture(scope="session")
def shared_state() -> dict:
    """Mutable dict passed between test files to share created resource IDs."""
    return {}


# ---------------------------------------------------------------------------
# Force all async test functions to run on the session-scoped event loop.
# Without this, pytest-asyncio 1.x gives each test a new function-scoped
# loop, which deadlocks when the test awaits session-scoped async fixtures
# (MCP ClientSession, asyncio queues) that were created on the session loop.
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(items):
    session_mark = pytest.mark.asyncio(loop_scope="session")
    for item in items:
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(item.function):
            item.add_marker(session_mark, append=False)
