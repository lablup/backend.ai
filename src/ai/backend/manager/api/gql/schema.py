import strawberry
from strawberry.federation import Schema
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
from .object_storage import (
    create_object_storage,
    delete_object_storage,
    object_storage,
    object_storages,
    update_object_storage,
)


@strawberry.type
class Queries:
    artifact = artifact
    artifacts = artifacts
    artifact_group = artifact_group
    artifact_groups = artifact_groups
    deployments = deployments
    deployment = deployment
    revisions = revisions
    revision = revision
    replica = replica
    object_storage = object_storage
    object_storages = object_storages


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
    create_object_storage = create_object_storage
    update_object_storage = update_object_storage
    delete_object_storage = delete_object_storage


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    artifact_import_progress_updated = artifact_import_progress_updated
    deployment_status_changed = deployment_status_changed
    replica_status_changed = replica_status_changed


class CustomizedSchema(Schema):
    def as_str(self) -> str:
        sdl = super().as_str()
        sdl = (
            sdl.replace("type Query", "type Queries")
            .replace("query: Query", "query: Queries")
            .replace("type PageInfo", "type PageInfo @shareable")
            .replace('import: ["@external", "@key"]', 'import: ["@external", "@key", "@shareable"]')
        )

        return sdl


schema = CustomizedSchema(
    query=Queries,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
)
