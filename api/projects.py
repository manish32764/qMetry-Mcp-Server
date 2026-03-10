"""Projects domain mixin."""


class ProjectsMixin:
    """API methods for qMetry project listing."""

    def list_projects(self, project_name: str = "", max_results: int = 50) -> dict:
        """POST /projects — list qMetry-enabled Jira projects."""
        return self._post(
            "projects",
            body={"search": project_name},
            params={"search": "key,name", "maxResults": max_results, "startAt": 0},
        )
