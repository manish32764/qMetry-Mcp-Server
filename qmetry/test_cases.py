"""Test cases domain mixin — CRUD operations on /testcases/ endpoints."""


class TestCasesMixin:
    """API methods for qMetry test case management."""

    def search_test_cases(
        self,
        project_key: str,
        search_text: str = "",
        status: str = "",
        priority: str = "",
        label: str = "",
        folder_id: str = "",
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict:
        """POST /testcases/search/ — search test cases with filters."""
        body: dict = {"filter": {}}
        if project_key:
            body["filter"]["projectKey"] = project_key
        if search_text:
            body["filter"]["searchText"] = search_text
        if status:
            body["filter"]["status"] = status
        if priority:
            body["filter"]["priority"] = priority
        if label:
            body["filter"]["label"] = label
        if folder_id:
            body["filter"]["folderId"] = folder_id
        return self._post(
            "testcases/search/",
            body=body,
            params={"maxResults": max_results, "startAt": start_at},
        )

    def get_test_case(self, test_case_id: str) -> dict:
        """GET /testcases/{id}"""
        return self._get(f"testcases/{test_case_id}")

    def create_test_case(
        self,
        project_key: str,
        summary: str,
        description: str = "",
        priority: str = "Medium",
        status: str = "",
        labels: list[str] | None = None,
        folder_id: str = "",
    ) -> dict:
        """POST /testcases/ — create a new test case (no steps yet)."""
        body: dict = {"projectKey": project_key, "summary": summary}
        if description:
            body["description"] = description
        if priority:
            body["priority"] = priority
        if status:
            body["status"] = status
        if labels:
            body["labels"] = labels
        if folder_id:
            body["folderId"] = folder_id
        return self._post("testcases/", body=body)

    def update_test_case(
        self,
        test_case_id: str,
        version_no: int,
        summary: str = "",
        description: str = "",
        priority: str = "",
        status: str = "",
        labels: list[str] | None = None,
    ) -> dict:
        """PUT /testcases/{id}/versions/{no} — update an existing test case."""
        body: dict = {}
        if summary:
            body["summary"] = summary
        if description:
            body["description"] = description
        if priority:
            body["priority"] = priority
        if status:
            body["status"] = status
        if labels is not None:
            body["labels"] = labels
        return self._put(f"testcases/{test_case_id}/versions/{version_no}", body=body)

    def archive_test_case(self, test_case_id: str) -> dict:
        """PUT /testcases/{id}/archive"""
        return self._put(f"testcases/{test_case_id}/archive")

    def unarchive_test_case(self, test_case_id: str) -> dict:
        """PUT /testcases/{id}/unarchive"""
        return self._put(f"testcases/{test_case_id}/unarchive")
