# Getting Started Guide — qMetry MCP Server

> You have a Python app that reads Jira user stories → generates test cases with an LLM → and now needs to publish them into qMetry.
> This server is the bridge. It wraps the qMetry REST API as MCP tools that any LLM agent or Python app can call.

---

## What this project actually does

```
Your App / any MCP client
           │
           │  calls MCP tools (e.g. "create_test_case")
           ▼
      [ server.py ]          ← entry point: registers tools, runs server
           │
           │  calls register(mcp) per domain
           ▼
      [ tools/ ]             ← MCP layer: one file per domain
           │
           │  calls QMetryClient methods
           ▼
   [ qmetry/client.py ]      ← REST facade composing domain mixins
           │
           │  HTTP requests (httpx)
           ▼
  qMetry REST API (cloud)    ← qMetry's servers
```

You never touch the REST API directly. You call MCP tools, and the server handles everything.

---

## Step 1 — Get your API key

In Jira, go to:
```
QMetry → Configuration → Open API → Generate
```

Copy that key. You'll need it in the next step.

---

## Step 2 — Install and configure

```bash
# From the qmetry_mcp/ directory:

pip install -r requirements.txt

# Create your .env file from the template
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux
```

Open `.env` and fill in your key:

```env
QMETRY_API_KEY=paste-your-key-here
QMETRY_BASE_URL=https://qtmcloud.qmetry.com/rest/api/latest/
```

> **Self-hosted Jira?** Change `QMETRY_BASE_URL` to:
> `https://your-jira.company.com/rest/qtm4j/v2/`

---

## Step 3 — Run the server

### Option A — stdio (for Claude Desktop or any MCP client)

```bash
python server.py
```

That's it. The server speaks MCP over stdin/stdout.

### Option B — HTTP (for your own Python app to call directly)

```bash
python server.py --http --port 8000
```

Server is now at `http://localhost:8000/mcp`.

---

## Step 4 — Connect an MCP client (optional)

If you want to use any MCP-compatible desktop app to talk to qMetry naturally, add this to its MCP server config:

```json
{
  "mcpServers": {
    "qmetry": {
      "command": "python",
      "args": ["C:/full/path/to/qmetry_mcp/server.py"],
      "env": {
        "QMETRY_API_KEY": "your-key-here",
        "QMETRY_BASE_URL": "https://qtmcloud.qmetry.com/rest/api/latest/"
      }
    }
  }
}
```

Once connected, you can issue natural language instructions like:
> *"Create a test case in project MYPROJ for the login feature with these 3 steps..."*

The MCP client will call the right tools automatically.

---

## The one tool you need for your pipeline

If you're building the **Jira story → LLM → qMetry** pipeline, there is a single composite tool that does everything in one call:

### `publish_test_cases_from_story`

It does all of this automatically:
1. Creates a folder named after the Jira story
2. Creates each test case
3. Adds steps to each test case
4. Links each test case back to the Jira story (traceability)
5. Creates a test cycle
6. Adds all test cases to the cycle
7. Links the cycle to the Jira story

**What you pass in:**

```python
publish_test_cases_from_story(
    project_key   = "MYPROJ",          # your Jira project key
    story_key     = "MYPROJ-42",       # the user story being tested
    story_summary = "User can log in securely",
    test_cases_json = """[
      {
        "summary": "Login with valid credentials",
        "description": "Verify authenticated users reach the dashboard",
        "priority": "High",
        "labels": ["regression", "smoke"],
        "steps": [
          {"description": "Go to /login",            "expectedResult": "Login page loads"},
          {"description": "Enter valid credentials",  "expectedResult": "Fields accept input"},
          {"description": "Click Login",              "expectedResult": "Dashboard is shown"}
        ]
      },
      {
        "summary": "Login fails with wrong password",
        "description": "Verify error message shown on bad credentials",
        "priority": "Medium",
        "labels": ["regression"],
        "steps": [
          {"description": "Go to /login",             "expectedResult": "Login page loads"},
          {"description": "Enter wrong password",     "expectedResult": "Fields accept input"},
          {"description": "Click Login",              "expectedResult": "Error message shown"}
        ]
      }
    ]""",
    create_cycle = True    # also create a test cycle grouping all TCs
)
```

**What you get back:**

```json
{
  "story_key": "MYPROJ-42",
  "folder_name": "MYPROJ-42 — User can log in securely",
  "published": [
    {"key": "TC-101", "summary": "Login with valid credentials",   "steps_count": 3},
    {"key": "TC-102", "summary": "Login fails with wrong password", "steps_count": 3}
  ],
  "cycle_key": "CY-15",
  "errors": []
}
```

---

## All available tools (40 total)

### Projects
| Tool | What it does |
|------|-------------|
| `list_projects` | List all qMetry-enabled Jira projects |

### Test Cases
| Tool | What it does |
|------|-------------|
| `search_test_cases` | Search by keyword, status, priority, label, folder |
| `get_test_case` | Get a single test case by ID or key |
| `create_test_case` | Create a new test case (no steps yet) |
| `update_test_case` | Change summary, description, priority, status, labels |
| `archive_test_case` | Soft-delete (reversible) |
| `unarchive_test_case` | Restore a soft-deleted test case |

### Test Steps
| Tool | What it does |
|------|-------------|
| `get_test_steps` | Get all steps for a test case |
| `add_test_steps` | Add steps to a test case |
| `update_test_steps` | Replace all steps on a test case |

### Jira Links (Requirements)
| Tool | What it does |
|------|-------------|
| `link_requirements_to_test_case` | Link Jira issues to a test case |
| `unlink_requirements_from_test_case` | Remove Jira issue links |

### Test Cycles
| Tool | What it does |
|------|-------------|
| `search_test_cycles` | Find cycles in a project |
| `get_test_cycle` | Get a single cycle |
| `create_test_cycle` | Create a new cycle |
| `update_test_cycle` | Rename or change status |
| `link_test_cases_to_cycle` | Add test cases to a cycle |
| `unlink_test_cases_from_cycle` | Remove test cases from a cycle |
| `get_cycle_test_cases` | List test cases inside a cycle |
| `link_requirements_to_cycle` | Link Jira issues to a cycle |
| `unlink_requirements_from_cycle` | Remove Jira issue links from a cycle |
| `archive_test_cycle` | Soft-delete a cycle |
| `unarchive_test_cycle` | Restore a cycle |

### Test Plans
| Tool | What it does |
|------|-------------|
| `search_test_plans` | Find plans in a project |
| `get_test_plan` | Get a single plan |
| `create_test_plan` | Create a new plan (groups cycles into a release) |
| `update_test_plan` | Rename or change status |
| `link_cycles_to_test_plan` | Add cycles to a plan |
| `unlink_cycles_from_test_plan` | Remove cycles from a plan |
| `get_plan_test_cycles` | List cycles in a plan |
| `archive_test_plan` | Soft-delete a plan |
| `unarchive_test_plan` | Restore a plan |

### Folders
| Tool | What it does |
|------|-------------|
| `list_test_case_folders` | List TC folders in a project |
| `create_test_case_folder` | Create a TC folder (with optional parent) |
| `list_test_cycle_folders` | List cycle folders |
| `create_test_cycle_folder` | Create a cycle folder |
| `list_test_plan_folders` | List plan folders |
| `create_test_plan_folder` | Create a plan folder |

### Metadata (lookup helpers)
| Tool | What it does |
|------|-------------|
| `list_labels` | List all labels in a project |
| `create_label` | Create a new label |
| `list_priorities` | List all priority options |
| `list_test_case_statuses` | List valid TC status values |
| `list_test_cycle_statuses` | List valid cycle status values |
| `list_test_plan_statuses` | List valid plan status values |

### Pipeline
| Tool | What it does |
|------|-------------|
| `publish_test_cases_from_story` | Full flow: folder + TCs + steps + Jira links + cycle in one call |

---

## How the code is organized

```
qmetry_mcp/
│
├── server.py                  ← Entry point. Creates the MCP server, registers all tools.
│                                Run this file.
│
├── tools/                     ← MCP layer. Tools that LLMs/agents call.
│   ├── __init__.py            ← register_all(mcp): registers every domain's tools
│   ├── utils.py               ← get_client(), to_json(), parse_csv(), parse_json()
│   ├── test_cases.py          ← tools: search/get/create/update/archive test cases
│   ├── test_steps.py          ← tools: get/add/update test steps
│   ├── requirements.py        ← tools: link/unlink Jira issues to test cases
│   ├── test_cycles.py         ← tools: full cycle CRUD + link TCs + link Jira
│   ├── test_plans.py          ← tools: full plan CRUD + link cycles
│   ├── folders.py             ← tools: list/create folders (TC, cycle, plan)
│   ├── metadata.py            ← tools: list labels, priorities, statuses
│   ├── projects.py            ← tools: list projects
│   └── pipeline.py            ← tool: publish_test_cases_from_story (composite)
│
└── qmetry/                    ← REST layer. Pure Python. No MCP here.
    ├── client.py              ← QMetryClient: composes all mixins into one class
    ├── base_client.py         ← HTTP transport: httpx, auth headers, _get/_post/_put/_delete
    ├── test_cases.py          ← TestCasesMixin: search/get/create/update/archive
    ├── test_steps.py          ← TestStepsMixin: get/add/update/delete steps
    ├── requirements.py        ← RequirementsMixin: link/unlink Jira issues
    ├── test_cycles.py         ← TestCyclesMixin: full cycle operations
    ├── test_plans.py          ← TestPlansMixin: full plan operations
    ├── folders.py             ← FoldersMixin: folder operations
    ├── metadata.py            ← MetadataMixin: labels, priorities, statuses
    └── projects.py            ← ProjectsMixin: list projects
```

**The two-layer rule:**
- `tools/` = what agents see and call. Knows about MCP, knows nothing about HTTP.
- `qmetry/` = what makes HTTP calls. Knows about REST, knows nothing about MCP.

They connect through `tools/utils.py → get_client()` which returns a `QMetryClient`.

---

## How to add a new API endpoint

Say qMetry adds a new `/testcases/{id}/attachments` endpoint you want to support.

**Step 1** — Add the method to `qmetry/test_cases.py`:
```python
def get_attachments(self, test_case_id: str) -> dict:
    """GET /testcases/{id}/attachments"""
    return self._get(f"testcases/{test_case_id}/attachments")
```

**Step 2** — Add the MCP tool to `tools/test_cases.py` inside `register(mcp)`:
```python
@mcp.tool()
def get_test_case_attachments(test_case_id: str) -> str:
    """Get all attachments for a test case.

    Args:
        test_case_id: qMetry test case ID or key.
    """
    with get_client() as c:
        return to_json(c.get_attachments(test_case_id))
```

Done. No changes needed anywhere else.

---

## Common questions

**Q: Do I need to run the Node.js qMetry MCP server?**
No. This project calls the qMetry REST API directly in Python. No Node.js needed.

**Q: Where does the API key go?**
In the `.env` file as `QMETRY_API_KEY`. The server reads it at startup via environment variables.

**Q: What's the difference between a Test Cycle and a Test Plan?**
- **Test Cycle** = one sprint or iteration of testing (groups test cases for one round of execution).
- **Test Plan** = a release plan (groups multiple test cycles across sprints).

**Q: The `publish_test_cases_from_story` tool had an error for one test case but others succeeded. What happened?**
Each test case is created independently. If one fails, the rest still proceed. Check the `"errors"` array in the response — it lists exactly which test cases failed and why.

**Q: How do I call this from my existing Python app (not Claude Desktop)?**

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def publish(story_key, test_cases_json):
    async with streamablehttp_client("http://localhost:8000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool(
                "publish_test_cases_from_story",
                arguments={
                    "project_key": "MYPROJ",
                    "story_key": story_key,
                    "story_summary": "User story summary here",
                    "test_cases_json": test_cases_json,
                    "create_cycle": True,
                }
            )
            return result.content[0].text
```

> Run `python server.py --http --port 8000` first.
