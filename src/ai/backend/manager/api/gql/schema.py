import strawberry
from strawberry.schema.config import StrawberryConfig

from .artifact_registry import (
    artifact,
    artifact_group,
    artifact_groups,
    artifact_import_progress_updated,
    artifact_status_changed,
    artifacts,
    cancel_import_artifact,
    delete_artifact,
    import_artifact,
    update_artifact,
)
from .model_deployment.model_deployment import (
    create_model_deployment,
    delete_model_deployment,
    deployment,
    deployment_status_changed,
    deployments,
    replica,
    replica_status_changed,
    update_model_deployment,
)
from .model_deployment.model_revision import (
    create_model_revision,
    revision,
    revisions,
)


@strawberry.type
class Query:
    artifact = artifact
    artifacts = artifacts
    artifact_group = artifact_group
    artifact_groups = artifact_groups
    deployments = deployments
    deployment = deployment
    revisions = revisions
    revision = revision
    replica = replica


@strawberry.type
class Mutation:
    import_artifact = import_artifact
    update_artifact = update_artifact
    delete_artifact = delete_artifact
    cancel_import_artifact = cancel_import_artifact
    create_model_deployment = create_model_deployment
    update_model_deployment = update_model_deployment
    delete_model_deployment = delete_model_deployment
    create_model_revision = create_model_revision


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    artifact_import_progress_updated = artifact_import_progress_updated
    deployment_status_changed = deployment_status_changed
    replica_status_changed = replica_status_changed


schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
)
