"""Metadata domain mixin — labels, priorities, and status lookups."""


class MetadataMixin:
    """API methods for reading project-level metadata (labels, priorities, statuses)."""

    # --- Labels ---

    def list_labels(self, project_id: str) -> dict:
        """GET /projects/{projectId}/labels"""
        return self._get(f"projects/{project_id}/labels")

    def create_label(self, project_id: str, name: str) -> dict:
        """POST /projects/{projectId}/labels"""
        return self._post(f"projects/{project_id}/labels", body={"name": name})

    # --- Priorities ---

    def list_priorities(self, project_id: str) -> dict:
        """GET /projects/{projectId}/priorities"""
        return self._get(f"projects/{project_id}/priorities")

    # --- Statuses ---

    def list_test_case_statuses(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testcase-statuses"""
        return self._get(f"projects/{project_id}/testcase-statuses")

    def list_test_cycle_statuses(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testcycle-statuses"""
        return self._get(f"projects/{project_id}/testcycle-statuses")

    def list_test_plan_statuses(self, project_id: str) -> dict:
        """GET /projects/{projectId}/testplan-statuses"""
        return self._get(f"projects/{project_id}/testplan-statuses")
