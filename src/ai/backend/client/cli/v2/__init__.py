"""V2 REST API CLI command group.

Registers config/login commands and all domain sub-groups
under ``backend.ai v2 {domain} {command}``.
"""

from __future__ import annotations

import click

from ai.backend.common.cli import LazyGroup

from .config_cmd import config
from .login_cmd import login, logout


@click.group()
def v2() -> None:
    """V2 REST API commands."""


# Infrastructure commands
v2.add_command(config)
v2.add_command(login)
v2.add_command(logout)


# Domain sub-groups — lazy loaded to avoid heavy imports at startup.


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.domain:domains")
def domains() -> None:
    """Domain management commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.user:users")
def users() -> None:
    """User management commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.project:projects")
def projects() -> None:
    """Project management commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.agent:agents")
def agents() -> None:
    """Agent management commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.image:images")
def images() -> None:
    """Image management commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.session:sessions")
def sessions() -> None:
    """Session management commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.container_registry:container_registries",
)
def container_registries() -> None:
    """Container registry commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.service_catalog:service_catalogs")
def service_catalogs() -> None:
    """Service catalog commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.vfs_storage:vfs_storages")
def vfs_storages() -> None:
    """VFS storage commands."""


@v2.group(
    cls=LazyGroup, import_name="ai.backend.client.cli.v2.storage_namespace:storage_namespaces"
)
def storage_namespaces() -> None:
    """Storage namespace commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.object_storage:object_storages")
def object_storages() -> None:
    """Object storage commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.artifact:artifacts")
def artifacts() -> None:
    """Artifact commands."""


@v2.group(
    cls=LazyGroup, import_name="ai.backend.client.cli.v2.artifact_registry:artifact_registries"
)
def artifact_registries() -> None:
    """Artifact registry commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.huggingface_registry:huggingface_registries",
)
def huggingface_registries() -> None:
    """HuggingFace registry commands."""


@v2.group(
    cls=LazyGroup, import_name="ai.backend.client.cli.v2.reservoir_registry:reservoir_registries"
)
def reservoir_registries() -> None:
    """Reservoir registry commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.deployment:deployments")
def deployments() -> None:
    """Deployment commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.rbac:rbac")
def rbac() -> None:
    """RBAC commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_group:resource_groups")
def resource_groups() -> None:
    """Resource group commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_slot:resource_slots")
def resource_slots() -> None:
    """Resource slot commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.resource_usage:resource_usage")
def resource_usage() -> None:
    """Resource usage commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.audit_log:audit_logs")
def audit_logs() -> None:
    """Audit log commands."""


@v2.group(
    cls=LazyGroup, import_name="ai.backend.client.cli.v2.scheduling_history:scheduling_history"
)
def scheduling_history() -> None:
    """Scheduling history commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.fair_share:fair_share")
def fair_share() -> None:
    """Fair share commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.notification:notifications")
def notifications() -> None:
    """Notification commands."""


@v2.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.app_config:app_configs")
def app_configs() -> None:
    """App config commands."""


@v2.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.prometheus_query_preset:prometheus_query_presets",
)
def prometheus_query_presets() -> None:
    """Prometheus query preset commands."""
