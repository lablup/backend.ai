import strawberry
from strawberry.schema.config import StrawberryConfig

from .artifact_registry import (
    artifact,
    artifact_group,
    artifact_groups,
    artifact_import_progress,
    artifact_status_changed,
    artifacts,
    cancel_import_artifact,
    delete_artifact,
    import_artifact,
    update_artifact,
)


@strawberry.type
class Query:
    artifacts = artifacts
    artifact_groups = artifact_groups
    artifact = artifact
    artifact_group = artifact_group


@strawberry.type
class Mutation:
    import_artifact = import_artifact
    update_artifact = update_artifact
    delete_artifact = delete_artifact
    cancel_import_artifact = cancel_import_artifact


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    artifact_import_progress = artifact_import_progress


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
)
