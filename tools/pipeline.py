"""MCP tools — Pipeline (composite full-flow tool)."""

from mcp.server.fastmcp import FastMCP

from .utils import get_client, parse_json, to_json


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def publish_test_cases_from_story(
        project_key: str,
        story_key: str,
        story_summary: str,
        test_cases_json: str,
        folder_name: str = "",
        create_cycle: bool = True,
    ) -> str:
        """Full pipeline: publish LLM-generated test cases into qMetry from a Jira story.

        This composite tool performs the complete flow in one call:
          1. Optionally create a folder named after the story.
          2. For each test case: create it, add steps, link it to the Jira story.
          3. Optionally create a test cycle and add all new test cases to it.
          4. Link the cycle back to the Jira story.

        Args:
            project_key:      Jira project key (e.g. "MYPROJ").
            story_key:        Jira user story key to link all test cases to (e.g. "MYPROJ-42").
            story_summary:    Brief summary of the story (used in cycle/folder names).
            test_cases_json:  JSON array of test case objects. Each object:
                                {
                                  "summary":     "Title of the test case",
                                  "description": "Objective / what is being tested",
                                  "priority":    "High" | "Medium" | "Low" | "Critical",
                                  "labels":      ["regression", "smoke"],
                                  "steps": [
                                    {"description": "Action", "expectedResult": "Expected outcome"},
                                    ...
                                  ]
                                }
            folder_name:      Folder to create/use for the new test cases.
                              Defaults to "<story_key> — <story_summary[:40]>".
            create_cycle:     Whether to also create a test cycle (default true).

        Returns:
            JSON summary with created test case keys and cycle key.
        """
        test_cases, err = parse_json(test_cases_json, "test_cases_json")
        if err:
            return err

        if not folder_name:
            folder_name = f"{story_key} — {story_summary[:40]}"

        results: dict = {
            "story_key": story_key,
            "folder_name": folder_name,
            "published": [],
            "cycle_key": None,
            "errors": [],
        }

        with get_client() as c:
            # 1. Resolve project ID and create folder
            folder_id = ""
            try:
                projects = c.list_projects(project_name=project_key, max_results=5)
                project_id = ""
                for p in projects.get("data", projects.get("results", [])):
                    if p.get("key") == project_key or p.get("projectKey") == project_key:
                        project_id = str(p.get("id", ""))
                        break

                if project_id and folder_name:
                    folder = c.create_test_case_folder(project_id, folder_name)
                    folder_id = str(folder.get("id", ""))
            except Exception as exc:
                results["errors"].append(f"Folder creation skipped: {exc}")

            # 2. Create each test case, add steps, link to Jira story
            created_keys: list[str] = []
            for tc in test_cases:
                try:
                    created = c.create_test_case(
                        project_key=project_key,
                        summary=tc["summary"],
                        description=tc.get("description", ""),
                        priority=tc.get("priority", "Medium"),
                        labels=tc.get("labels", []),
                        folder_id=folder_id,
                    )
                    tc_id = str(created.get("id", created.get("key", "")))
                    tc_key = created.get("key", tc_id)
                    version_no = created.get("latestVersion", created.get("versionNo", 1))

                    steps = tc.get("steps", [])
                    if steps:
                        c.add_test_steps(tc_id, version_no, steps)

                    c.link_requirements_to_test_case(tc_id, version_no, [story_key])

                    created_keys.append(tc_key)
                    results["published"].append({
                        "key": tc_key,
                        "summary": tc["summary"],
                        "steps_count": len(steps),
                    })
                except Exception as exc:
                    results["errors"].append(
                        f"Failed to create '{tc.get('summary', '?')}': {exc}"
                    )

            # 3. Create test cycle and link everything
            if create_cycle and created_keys:
                try:
                    cycle = c.create_test_cycle(
                        project_key=project_key,
                        name=f"{story_key} — {story_summary[:50]}",
                        description=f"Auto-generated cycle for {story_key}",
                    )
                    cycle_id = str(cycle.get("id", cycle.get("key", "")))
                    cycle_key = cycle.get("key", cycle_id)

                    c.link_test_cases_to_cycle(cycle_id, created_keys)
                    c.link_requirements_to_cycle(cycle_id, [story_key])

                    results["cycle_key"] = cycle_key
                except Exception as exc:
                    results["errors"].append(f"Cycle creation failed: {exc}")

        return to_json(results)
