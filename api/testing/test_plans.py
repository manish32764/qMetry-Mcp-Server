"""Test plans domain mixin — all /testplans/ endpoint operations."""


class TestPlansMixin:
    """API methods for qMetry test plan management."""

    def search_test_plans(
        self,
        project_id: str,
        search_text: str = "",
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict:
        """POST /testplans/search/"""
        body: dict = {"filter": {"projectId": project_id}}
        if search_text:
            body["filter"]["searchText"] = search_text
        return self._post(
            "testplans/search/",
            body=body,
            params={"maxResults": max_results, "startAt": start_at},
        )

    def get_test_plan(self, plan_id_or_key: str) -> dict:
        """GET /testplans/{idOrKey}"""
        return self._get(f"testplans/{plan_id_or_key}")

    def create_test_plan(
        self,
        project_id: str,
        name: str,
        description: str = "",
        status: str = "",
        folder_id: str = "",
    ) -> dict:
        """POST /testplans/ — create a new test plan."""
        body: dict = {"projectId": project_id, "summary": name}
        if description:
            body["description"] = description
        if status:
            body["status"] = status
        if folder_id:
            body["folderId"] = folder_id
        return self._post("testplans/", body=body)

    def update_test_plan(
        self, plan_id: str, name: str = "", description: str = "", status: str = ""
    ) -> dict:
        """PUT /testplans/{id}"""
        body: dict = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        if status:
            body["status"] = status
        return self._put(f"testplans/{plan_id}", body=body)

    def link_cycles_to_test_plan(
        self, plan_id: str, cycle_keys: list[str]
    ) -> dict:
        """POST /testplans/{id}/testcycles — add cycles to a plan."""
        return self._post(
            f"testplans/{plan_id}/testcycles",
            body={"testCycleKeys": cycle_keys},
        )

    def unlink_cycles_from_test_plan(
        self, plan_id: str, cycle_keys: list[str]
    ) -> dict:
        """DELETE /testplans/{id}/testcycles"""
        return self._delete(
            f"testplans/{plan_id}/testcycles",
            body={"filter": {"testCycleKeys": cycle_keys}},
        )

    def get_plan_test_cycles(self, plan_id: str, max_results: int = 50) -> dict:
        """POST /testplans/{id}/testcycles/search"""
        return self._post(
            f"testplans/{plan_id}/testcycles/search",
            body={"filter": {}},
            params={"maxResults": max_results, "startAt": 0},
        )

    def archive_test_plan(self, plan_id_or_key: str) -> dict:
        """PUT /testplans/{idOrKey}/archive"""
        return self._put(f"testplans/{plan_id_or_key}/archive")

    def unarchive_test_plan(self, plan_id_or_key: str) -> dict:
        """PUT /testplans/{idOrKey}/unarchive"""
        return self._put(f"testplans/{plan_id_or_key}/unarchive")
