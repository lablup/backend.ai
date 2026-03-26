"""V2 REST API CLI command group.

Registers config/login commands, the admin sub-group, and all entity
sub-groups under ``backend.ai v2 {entity} {command}``.

Entity names are singular (domain, user, project, agent).
Admin-only commands live under ``backend.ai v2 admin {entity} {command}``.
"""

from __future__ import annotations

import click

from ai.backend.common.cli import LazyGroup

from .admin import admin
from .config_cmd import config
from .login_cmd import login, logout
from .my import my


@click.group()
def v2() -> None:
    """V2 REST API commands."""


# Infrastructure commands
v2.add_command(config)
v2.add_command(login)
v2.add_command(logout)

# Admin group — contains admin-only commands per entity
v2.add_command(admin)

# My group — contains self-service commands per entity
v2.add_command(my)


# Entity sub-groups — lazy loaded to avoid heavy imports at startup.
# Names are singular following the pattern: ./bai [admin] {entity} {operation}


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.domain:domain")
def domain() -> None:
    """Domain commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.user:user")
def user() -> None:
    """User commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.project:project")
def project() -> None:
    """Project commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.agent:agent")
def agent() -> None:
    """Agent commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.image:image")
def image() -> None:
    """Image commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.session:session")
def session() -> None:
    """Session commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.deployment:deployment")
def deployment() -> None:
    """Deployment commands."""


# ------------------------------------------------------------------ Artifact & registries


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.artifact:artifact")
def artifact() -> None:
    """Artifact commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.artifact_registry:artifact_registry",
)
def artifact_registry() -> None:
    """Artifact registry commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.container_registry:container_registry",
)
def container_registry() -> None:
    """Container registry commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.huggingface_registry:huggingface_registry",
)
def huggingface_registry() -> None:
    """HuggingFace registry commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.reservoir_registry:reservoir_registry",
)
def reservoir_registry() -> None:
    """Reservoir registry commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.service_catalog:service_catalog",
)
def service_catalog() -> None:
    """Service catalog commands."""


# ------------------------------------------------------------------ Storage


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.vfs_storage:vfs_storage")
def vfs_storage() -> None:
    """VFS storage commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.storage_namespace:storage_namespace",
)
def storage_namespace() -> None:
    """Storage namespace commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.object_storage:object_storage")
def object_storage() -> None:
    """Object storage commands."""


# ------------------------------------------------------------------ RBAC & resources


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.rbac:rbac")
def rbac() -> None:
    """RBAC commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_group:resource_group")
def resource_group() -> None:
    """Resource group commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_slot:resource_slot")
def resource_slot() -> None:
    """Resource slot commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_usage:resource_usage")
def resource_usage() -> None:
    """Resource usage commands."""


# ------------------------------------------------------------------ Monitoring & history


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.audit_log:audit_log")
def audit_log() -> None:
    """Audit log commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.scheduling_history:scheduling_history",
)
def scheduling_history() -> None:
    """Scheduling history commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.fair_share:fair_share")
def fair_share() -> None:
    """Fair share commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.notification:notification")
def notification() -> None:
    """Notification commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.app_config:app_config")
def app_config() -> None:
    """App config commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.prometheus_query_preset:prometheus_query_preset",
)
def prometheus_query_preset() -> None:
    """Prometheus query preset commands."""
