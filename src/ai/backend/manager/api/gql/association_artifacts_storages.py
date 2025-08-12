import uuid
from typing import Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.association.creator import AssociationArtifactsStoragesCreator
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData


@strawberry.type
class AssociationArtifactsStorages(Node):
    id: NodeID[str]
    artifact_id: ID
    storage_id: ID

    @classmethod
    def from_dataclass(cls, image_data: AssociationArtifactsStoragesData) -> Self:
        return cls(
            id=ID(str(image_data.id)),
            artifact_id=ID(str(image_data.artifact_id)),
            storage_id=ID(str(image_data.storage_id)),
        )


@strawberry.input
class AssociateArtifactWithStorageInput:
    artifact_id: ID
    storage_id: ID

    def to_creator(self) -> AssociationArtifactsStoragesCreator:
        return AssociationArtifactsStoragesCreator(
            artifact_id=uuid.UUID(self.artifact_id),
            storage_id=uuid.UUID(self.storage_id),
        )


@strawberry.type
class AssociateArtifactWithStoragePayload:
    association: AssociationArtifactsStorages


@strawberry.input
class DisassociateArtifactWithStorageInput:
    artifact_id: ID
    storage_id: ID


@strawberry.type
class DisassociateArtifactWithStoragePayload:
    association: AssociationArtifactsStorages


# TODO: 이름 바꿔둘 것. DB만 다루는, 내부 스키마가 드러나는 이름이면 안 됨.
# 동작도 굳이 필요한지 잘 모르겠음.
# 아티팩트를 다른 스토리지로 옮겨주는 뮤테이션으로?


# row_id 드러내는 것도 사실 별로인데 GQL에서 그렇게 한다고 하니...
# 인터페이스만 맞춰주면 되는거고, 내부에 있는 것들을 쉽게 갈아낄 수 있는 방향이어야 함. 바꿀 수 있는 여지를 깨지말 것.
@strawberry.mutation
async def associate_artifact_with_storage(
    input: AssociateArtifactWithStorageInput, info: Info[StrawberryGQLContext]
) -> AssociateArtifactWithStoragePayload:
    # processors = info.context.processors

    # action_result = await processors.object_storage.create.wait_for_complete(
    #     CreateObjectStorageAction(
    #         creator=input.to_creator(),
    #     )
    # )

    # return CreateObjectStoragePayload(
    #     object_storage=ObjectStorage.from_dataclass(action_result.result)
    # )
    raise NotImplementedError("This mutation is not implemented yet.")


@strawberry.mutation
async def disassociate_artifact_with_storage(
    input: DisassociateArtifactWithStorageInput, info: Info[StrawberryGQLContext]
) -> DisassociateArtifactWithStoragePayload:
    # processors = info.context.processors

    # action_result = await processors.object_storage.create.wait_for_complete(
    #     CreateObjectStorageAction(
    #         creator=input.to_creator(),
    #     )
    # )

    # return CreateObjectStoragePayload(
    #     object_storage=ObjectStorage.from_dataclass(action_result.result)
    # )
    raise NotImplementedError("This mutation is not implemented yet.")
