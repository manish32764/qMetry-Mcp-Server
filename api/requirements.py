"""Requirements (Jira ↔ Test Case) domain mixin."""


class RequirementsMixin:
    """API methods for linking Jira issues to test cases for traceability."""

    def link_requirements_to_test_case(
        self, test_case_id: str, version_no: int, issue_keys: list[str]
    ) -> dict:
        """POST /testcases/{id}/version/{no}/requirements/link"""
        return self._post(
            f"testcases/{test_case_id}/version/{version_no}/requirements/link",
            body={"issueKeys": issue_keys},
        )

    def unlink_requirements_from_test_case(
        self, test_case_id: str, version_no: int, issue_keys: list[str]
    ) -> dict:
        """POST /testcases/{id}/versions/{no}/requirements/unlink"""
        return self._post(
            f"testcases/{test_case_id}/versions/{version_no}/requirements/unlink",
            body={"issueKeys": issue_keys},
        )

    def get_linked_requirements(self, test_case_id: str) -> dict:
        """GET /testcases/{id}/testcycles — inspect linked Jira stories."""
        return self._get(f"testcases/{test_case_id}/testcycles")
