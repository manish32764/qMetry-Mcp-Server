"""Folders domain mixin — test case, test cycle, and test plan folder operations."""


class FoldersMixin:
    """API methods for managing folder hierarchy under a qMetry project."""

    # --- Test Case Folders ---

    def list_test_case_folders(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testcase-folders"""
        return self._get(f"projects/{project_id}/testcase-folders")

    def create_test_case_folder(
        self, project_id: str, name: str, parent_id: str = ""
    ) -> dict:
        """POST /projects/{projectId}/testcase-folders"""
        body: dict = {"folderName": name}
        if parent_id:
            body["parentId"] = parent_id
        return self._post(f"projects/{project_id}/testcase-folders", body=body)

    # --- Test Cycle Folders ---

    def list_test_cycle_folders(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testcycle-folders"""
        return self._get(f"projects/{project_id}/testcycle-folders")

    def create_test_cycle_folder(
        self, project_id: str, name: str, parent_id: str = ""
    ) -> dict:
        """POST /projects/{projectId}/testcycle-folders"""
        body: dict = {"folderName": name}
        if parent_id:
            body["parentId"] = parent_id
        return self._post(f"projects/{project_id}/testcycle-folders", body=body)

    # --- Test Plan Folders ---

    def list_test_plan_folders(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testplan-folders"""
        return self._get(f"projects/{project_id}/testplan-folders")

    def create_test_plan_folder(
        self, project_id: str, name: str, parent_id: str = ""
    ) -> dict:
        """POST /projects/{projectId}/testplan-folders"""
        body: dict = {"folderName": name}
        if parent_id:
            body["parentId"] = parent_id
        return self._post(f"projects/{project_id}/testplan-folders", body=body)
