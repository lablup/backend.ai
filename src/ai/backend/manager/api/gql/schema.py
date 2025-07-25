import strawberry
from strawberry.schema.config import StrawberryConfig

from .artifact_registry import (
    artifact,
    artifact_group,
    artifact_groups,
    artifact_status_changed,
    artifacts,
    cancel_pull,
    delete_artifact,
    download_progress,
    install_artifact,
    pull_artifact,
    update_artifact,
    verify_artifact,
)
from .model_deployment.model_deployment import (
    create_model_deployment,
    delete_model_deployment,
    deployment,
    deployment_metrics,
    deployment_status_changed,
    deployments,
    metrics_updated,
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
    artifacts = artifacts
    artifact_groups = artifact_groups
    artifact = artifact
    artifact_group = artifact_group
    deployments = deployments
    deployment = deployment
    revisions = revisions
    revision = revision
    deployment_metrics = deployment_metrics
    replica = replica


@strawberry.type
class Mutation:
    pull_artifact = pull_artifact
    install_artifact = install_artifact
    update_artifact = update_artifact
    delete_artifact = delete_artifact
    verify_artifact = verify_artifact
    cancel_pull = cancel_pull
    create_model_deployment = create_model_deployment
    update_model_deployment = update_model_deployment
    delete_model_deployment = delete_model_deployment
    create_model_revision = create_model_revision


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    download_progress = download_progress
    deployment_status_changed = deployment_status_changed
    replica_status_changed = replica_status_changed
    metrics_updated = metrics_updated


schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
)
