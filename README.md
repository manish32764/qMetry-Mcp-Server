# qMetry Test Management MCP Server

A Python MCP server that exposes the **qMetry REST API** as tools for LLM agents.
Built for the **Jira → LLM → qMetry** test case generation pipeline.

No Node.js. No third-party MCP wrapper. Pure Python talking directly to the qMetry REST API.

---

## Project Structure

```
qmetry_mcp/
├── server.py                  ← Entry point: init MCP server, register tools, run
│
├── tools/                     ← MCP layer (what agents call)
│   ├── __init__.py            ← register_all(mcp)
│   ├── utils.py               ← shared helpers: get_client, to_json, parse_csv, parse_json
│   ├── projects.py
│   ├── test_cases.py
│   ├── test_steps.py
│   ├── requirements.py
│   ├── test_cycles.py
│   ├── test_plans.py
│   ├── folders.py
│   ├── metadata.py
│   └── pipeline.py            ← composite: publish_test_cases_from_story
│
├── qmetry/                    ← REST layer (HTTP calls, no MCP)
│   ├── client.py              ← QMetryClient facade (composes all mixins)
│   ├── base_client.py         ← HTTP transport: httpx, auth, _get/_post/_put/_delete
│   ├── projects.py
│   ├── test_cases.py
│   ├── test_steps.py
│   ├── requirements.py
│   ├── test_cycles.py
│   ├── test_plans.py
│   ├── folders.py
│   └── metadata.py
│
├── .env.example
└── requirements.txt
```

---

## Setup

```bash
cd qmetry_mcp

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env: add your QMETRY_API_KEY
#   Get it from: Jira → QMetry → Configuration → Open API → Generate

# 3. Load env and run
set -a && source .env && set +a   # Linux/Mac
# or on Windows:
# set QMETRY_API_KEY=your-key-here
```

---

## Running the Server

### stdio (for any MCP client)
```bash
python server.py
```

### HTTP (for programmatic Python access)
```bash
python server.py --http --port 8000
# Server runs at http://localhost:8000/mcp
```

---

## MCP Client Integration

Add this to your MCP client's server config (e.g. `mcp_config.json`):

```json
{
  "mcpServers": {
    "qmetry": {
      "command": "python",
      "args": ["C:/path/to/qmetry_mcp/server.py"],
      "env": {
        "QMETRY_API_KEY": "your-api-key-here",
        "QMETRY_BASE_URL": "https://qtmcloud.qmetry.com/rest/api/latest/"
      }
    }
  }
}
```

---

## Available Tools (40 total)

### Projects
| Tool | Description |
|------|-------------|
| `list_projects` | List all qMetry-enabled Jira projects |

### Test Cases
| Tool | Description |
|------|-------------|
| `search_test_cases` | Search with filters (status, priority, label, folder) |
| `get_test_case` | Get single test case by ID/key |
| `create_test_case` | Create a new test case |
| `update_test_case` | Update summary, description, priority, status, labels |
| `archive_test_case` | Archive (soft delete) |
| `unarchive_test_case` | Restore archived test case |

### Test Steps
| Tool | Description |
|------|-------------|
| `get_test_steps` | Get all steps for a test case version |
| `add_test_steps` | Add steps to a test case |
| `update_test_steps` | Replace all steps |

### Requirements (Jira ↔ Test Case Links)
| Tool | Description |
|------|-------------|
| `link_requirements_to_test_case` | Link Jira issues to a test case |
| `unlink_requirements_from_test_case` | Remove Jira issue links |

### Test Cycles
| Tool | Description |
|------|-------------|
| `search_test_cycles` | Search cycles in a project |
| `get_test_cycle` | Get a single cycle |
| `create_test_cycle` | Create a new test cycle |
| `update_test_cycle` | Update name/description/status |
| `link_test_cases_to_cycle` | Add test cases to a cycle |
| `unlink_test_cases_from_cycle` | Remove test cases from a cycle |
| `get_cycle_test_cases` | List test cases in a cycle |
| `link_requirements_to_cycle` | Link Jira issues to a cycle |
| `unlink_requirements_from_cycle` | Remove Jira issue links from a cycle |
| `archive_test_cycle` | Archive a cycle |
| `unarchive_test_cycle` | Restore an archived cycle |

### Test Plans
| Tool | Description |
|------|-------------|
| `search_test_plans` | Search plans in a project |
| `get_test_plan` | Get a single plan |
| `create_test_plan` | Create a new test plan |
| `update_test_plan` | Update name/description/status |
| `link_cycles_to_test_plan` | Add cycles to a plan |
| `unlink_cycles_from_test_plan` | Remove cycles from a plan |
| `get_plan_test_cycles` | List cycles in a plan |
| `archive_test_plan` | Archive a plan |
| `unarchive_test_plan` | Restore an archived plan |

### Folders
| Tool | Description |
|------|-------------|
| `list_test_case_folders` | List test case folders |
| `create_test_case_folder` | Create a test case folder |
| `list_test_cycle_folders` | List test cycle folders |
| `create_test_cycle_folder` | Create a test cycle folder |
| `list_test_plan_folders` | List test plan folders |
| `create_test_plan_folder` | Create a test plan folder |

### Metadata Lookups
| Tool | Description |
|------|-------------|
| `list_labels` | List all labels in a project |
| `create_label` | Create a new label |
| `list_priorities` | List all priorities |
| `list_test_case_statuses` | List test case status options |
| `list_test_cycle_statuses` | List test cycle status options |
| `list_test_plan_statuses` | List test plan status options |

### Pipeline (Composite)
| Tool | Description |
|------|-------------|
| `publish_test_cases_from_story` | **Full pipeline**: create folder + test cases + steps + Jira links + cycle in one call |

---

## Pipeline Usage: Jira → LLM → qMetry

The `publish_test_cases_from_story` tool handles the entire flow.

### Input format (`test_cases_json`)

```json
[
  {
    "summary": "Verify login with valid credentials",
    "description": "Ensure authenticated users can access the dashboard",
    "priority": "High",
    "labels": ["regression", "smoke"],
    "steps": [
      {"description": "Navigate to /login", "expectedResult": "Login page is displayed"},
      {"description": "Enter valid username and password", "expectedResult": "Fields accept input"},
      {"description": "Click Login button", "expectedResult": "User is redirected to dashboard"}
    ]
  },
  {
    "summary": "Verify login fails with wrong password",
    "description": "Ensure correct error message shown on wrong password",
    "priority": "Medium",
    "labels": ["regression"],
    "steps": [
      {"description": "Navigate to /login", "expectedResult": "Login page is displayed"},
      {"description": "Enter valid username and WRONG password", "expectedResult": "Fields accept input"},
      {"description": "Click Login", "expectedResult": "Error 'Invalid credentials' is shown"}
    ]
  }
]
```

### What it does internally

```
publish_test_cases_from_story(
    project_key="MYPROJ",
    story_key="MYPROJ-42",
    story_summary="User can log in securely",
    test_cases_json=<above>,
    create_cycle=True
)

→ 1. POST /projects                           (get project ID)
→ 2. POST /projects/{id}/testcase-folders     (create folder "MYPROJ-42 — User can log in...")
→ 3. POST /testcases/                         (create TC #1)
→ 4. POST /testcases/{id}/versions/1/teststeps (add 3 steps)
→ 5. POST /testcases/{id}/version/1/requirements/link  (link MYPROJ-42)
→ 6. POST /testcases/                         (create TC #2)
→ 7. POST /testcases/{id}/versions/1/teststeps (add 3 steps)
→ 8. POST /testcases/{id}/version/1/requirements/link  (link MYPROJ-42)
→ 9. POST /testcycles/                        (create cycle)
→ 10. POST /testcycles/{id}/testcases         (link TC-1, TC-2)
→ 11. POST /testcycles/{id}/requirements/link (link MYPROJ-42)
```

### Output

```json
{
  "story_key": "MYPROJ-42",
  "folder_name": "MYPROJ-42 — User can log in securely",
  "published": [
    {"key": "TC-101", "summary": "Verify login with valid credentials", "steps_count": 3},
    {"key": "TC-102", "summary": "Verify login fails with wrong password", "steps_count": 3}
  ],
  "cycle_key": "CY-15",
  "errors": []
}
```

---

## REST API Endpoints Used

| # | Method | Endpoint |
|---|--------|----------|
| 1 | POST | `/projects` |
| 2 | POST | `/testcases/search/` |
| 3 | GET | `/testcases/{id}` |
| 4 | POST | `/testcases/` |
| 5 | PUT | `/testcases/{id}/versions/{no}` |
| 6 | PUT | `/testcases/{id}/archive` |
| 7 | PUT | `/testcases/{id}/unarchive` |
| 8 | POST | `/testcases/{id}/versions/{no}/teststeps/search/` |
| 9 | POST | `/testcases/{id}/versions/{no}/teststeps` |
| 10 | PUT | `/testcases/{id}/versions/{no}/teststeps` |
| 11 | DELETE | `/testcases/{id}/versions/{no}/teststeps` |
| 12 | POST | `/testcases/{id}/version/{no}/requirements/link` |
| 13 | POST | `/testcases/{id}/versions/{no}/requirements/unlink` |
| 14 | POST | `/testcycles/search/` |
| 15 | GET | `/testcycles/{idOrKey}` |
| 16 | POST | `/testcycles/` |
| 17 | PUT | `/testcycles/{id}` |
| 18 | POST | `/testcycles/{id}/testcases` |
| 19 | DELETE | `/testcycles/{id}/testcases` |
| 20 | POST | `/testcycles/{id}/testcases/search` |
| 21 | POST | `/testcycles/{id}/requirements/link` |
| 22 | POST | `/testcycles/{id}/requirements/unlink` |
| 23 | PUT | `/testcycles/{idOrKey}/archive` |
| 24 | PUT | `/testcycles/{idOrKey}/unarchive` |
| 25 | POST | `/testplans/search/` |
| 26 | GET | `/testplans/{idOrKey}` |
| 27 | POST | `/testplans/` |
| 28 | PUT | `/testplans/{id}` |
| 29 | POST | `/testplans/{id}/testcycles` |
| 30 | DELETE | `/testplans/{id}/testcycles` |
| 31 | GET | `/testplans/{id}/testcycles` |
| 32 | PUT | `/testplans/{idOrKey}/archive` |
| 33 | PUT | `/testplans/{idOrKey}/unarchive` |
| 34 | GET/POST | `/projects/{id}/testcase-folders` |
| 35 | GET/POST | `/projects/{id}/testcycle-folders` |
| 36 | GET/POST | `/projects/{id}/testplan-folders` |
| 37 | GET | `/projects/{id}/labels` |
| 38 | POST | `/projects/{id}/labels` |
| 39 | GET | `/projects/{id}/priorities` |
| 40 | GET | `/projects/{id}/testcase-statuses` |
| 41 | GET | `/projects/{id}/testcycle-statuses` |
| 42 | GET | `/projects/{id}/testplan-statuses` |
"# qMetry-Mcp-Server" 
