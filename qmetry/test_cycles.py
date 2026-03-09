"""Test cycles domain mixin — all /testcycles/ endpoint operations."""


class TestCyclesMixin:
    """API methods for qMetry test cycle management."""

    def search_test_cycles(
        self,
        project_key: str,
        search_text: str = "",
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict:
        """POST /testcycles/search/"""
        body: dict = {"filter": {"projectKey": project_key}}
        if search_text:
            body["filter"]["searchText"] = search_text
        return self._post(
            "testcycles/search/",
            body=body,
            params={"maxResults": max_results, "startAt": start_at},
        )

    def get_test_cycle(self, cycle_id_or_key: str) -> dict:
        """GET /testcycles/{idOrKey}"""
        return self._get(f"testcycles/{cycle_id_or_key}")

    def create_test_cycle(
        self,
        project_key: str,
        name: str,
        description: str = "",
        status: str = "",
        folder_id: str = "",
    ) -> dict:
        """POST /testcycles/ — create a new test cycle."""
        body: dict = {"projectKey": project_key, "name": name}
        if description:
            body["description"] = description
        if status:
            body["status"] = status
        if folder_id:
            body["folderId"] = folder_id
        return self._post("testcycles/", body=body)

    def update_test_cycle(
        self, cycle_id: str, name: str = "", description: str = "", status: str = ""
    ) -> dict:
        """PUT /testcycles/{id}"""
        body: dict = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        if status:
            body["status"] = status
        return self._put(f"testcycles/{cycle_id}", body=body)

    def link_test_cases_to_cycle(
        self, cycle_id: str, test_case_keys: list[str]
    ) -> dict:
        """POST /testcycles/{id}/testcases — add test cases to a cycle."""
        return self._post(
            f"testcycles/{cycle_id}/testcases",
            body={"testCaseKeys": test_case_keys},
        )

    def unlink_test_cases_from_cycle(
        self, cycle_id: str, test_case_keys: list[str]
    ) -> dict:
        """DELETE /testcycles/{id}/testcases"""
        return self._delete(
            f"testcycles/{cycle_id}/testcases",
            body={"testCaseKeys": test_case_keys},
        )

    def get_cycle_test_cases(
        self,
        cycle_id: str,
        search_text: str = "",
        status: str = "",
        max_results: int = 50,
    ) -> dict:
        """POST /testcycles/{id}/testcases/search"""
        body: dict = {"filter": {}}
        if search_text:
            body["filter"]["searchText"] = search_text
        if status:
            body["filter"]["executionResult"] = status
        return self._post(
            f"testcycles/{cycle_id}/testcases/search",
            body=body,
            params={"maxResults": max_results, "startAt": 0},
        )

    def link_requirements_to_cycle(
        self, cycle_id: str, issue_keys: list[str]
    ) -> dict:
        """POST /testcycles/{id}/requirements/link"""
        return self._post(
            f"testcycles/{cycle_id}/requirements/link",
            body={"issueKeys": issue_keys},
        )

    def unlink_requirements_from_cycle(
        self, cycle_id: str, issue_keys: list[str]
    ) -> dict:
        """POST /testcycles/{id}/requirements/unlink"""
        return self._post(
            f"testcycles/{cycle_id}/requirements/unlink",
            body={"issueKeys": issue_keys},
        )

    def archive_test_cycle(self, cycle_id_or_key: str) -> dict:
        """PUT /testcycles/{idOrKey}/archive"""
        return self._put(f"testcycles/{cycle_id_or_key}/archive")

    def unarchive_test_cycle(self, cycle_id_or_key: str) -> dict:
        """PUT /testcycles/{idOrKey}/unarchive"""
        return self._put(f"testcycles/{cycle_id_or_key}/unarchive")
