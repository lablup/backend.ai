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


@strawberry.type
class Query:
    artifacts = artifacts
    artifact_groups = artifact_groups
    artifact = artifact
    artifact_group = artifact_group


@strawberry.type
class Mutation:
    pull_artifact = pull_artifact
    install_artifact = install_artifact
    update_artifact = update_artifact
    delete_artifact = delete_artifact
    verify_artifact = verify_artifact
    cancel_pull = cancel_pull


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    download_progress = download_progress


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
)
