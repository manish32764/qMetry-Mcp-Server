"""Test steps domain mixin — operations on /testcases/{id}/versions/{no}/teststeps/ endpoints."""


class TestStepsMixin:
    """API methods for managing steps within a test case version."""

    def get_test_steps(
        self, test_case_id: str, version_no: int, max_results: int = 100
    ) -> dict:
        """POST /testcases/{id}/versions/{no}/teststeps/search"""
        return self._post(
            f"testcases/{test_case_id}/versions/{version_no}/teststeps/search",
            body={"filter": {}},
            params={"maxResults": max_results, "startAt": 0},
        )

    def add_test_steps(
        self, test_case_id: str, version_no: int, steps: list[dict]
    ) -> dict:
        """POST /testcases/{id}/versions/{no}/teststeps — append steps.

        Each step: {"description": str, "expectedResult": str, "testData": str (optional)}
        """
        return self._post(
            f"testcases/{test_case_id}/versions/{version_no}/teststeps",
            body={"steps": steps},
        )

    def update_test_steps(
        self, test_case_id: str, version_no: int, steps: list[dict]
    ) -> dict:
        """PUT /testcases/{id}/versions/{no}/teststeps — replace all steps."""
        return self._put(
            f"testcases/{test_case_id}/versions/{version_no}/teststeps",
            body={"steps": steps},
        )

    def delete_test_steps(
        self, test_case_id: str, version_no: int, step_ids: list[str]
    ) -> dict:
        """DELETE /testcases/{id}/versions/{no}/teststeps — remove specific steps."""
        return self._delete(
            f"testcases/{test_case_id}/versions/{version_no}/teststeps",
            body={"stepIds": step_ids},
        )
