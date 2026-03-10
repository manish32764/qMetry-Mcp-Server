"""
QMetryClient — public facade that composes all domain mixins over the HTTP base.

Usage:
    from api.client import QMetryClient

    with QMetryClient() as c:
        projects = c.list_projects()
        tc = c.create_test_case(project_key="PROJ", summary="Login test")

The class itself contains no logic; all methods are inherited from domain mixins.
To add a new API domain: create a new mixin module and include it in the MRO below.
"""

from .base_client import QMetryBaseClient
from .folders import FoldersMixin
from .metadata import MetadataMixin
from .projects import ProjectsMixin
from .requirements import RequirementsMixin
from .testing.test_cases import TestCasesMixin
from .testing.test_cycles import TestCyclesMixin
from .testing.test_plans import TestPlansMixin
from .testing.test_steps import TestStepsMixin


class QMetryClient(
    ProjectsMixin,
    TestCasesMixin,
    TestStepsMixin,
    RequirementsMixin,
    TestCyclesMixin,
    TestPlansMixin,
    FoldersMixin,
    MetadataMixin,
    QMetryBaseClient,
):
    """
    Full qMetry API client.

    MRO: domain mixins → QMetryBaseClient (owns _http and HTTP verbs).
    No mixin may override _get/_post/_put/_delete or hold its own httpx.Client.
    """
