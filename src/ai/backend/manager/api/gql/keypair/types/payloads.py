"""Keypair GraphQL mutation payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload as AdminCreateKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminDeleteKeypairPayload as AdminDeleteKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminDeleteSSHKeypairPayload as AdminDeleteSSHKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminGetSSHKeypairPayload as AdminGetSSHKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminKeypairSecretStatusPayload as AdminKeypairSecretStatusPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminReencryptKeypairSecretsPayload as AdminReencryptKeypairSecretsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminRegisterSSHKeypairPayload as AdminRegisterSSHKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminUpdateKeypairPayload as AdminUpdateKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    CreateKeypairPayload as CreateKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload as IssueMyKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    KeypairSecretKeyCount as KeypairSecretKeyCountDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    RevokeMyKeypairPayload as RevokeMyKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    SSHKeypairNode as SSHKeypairNodeDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    SwitchMyMainAccessKeyPayload as SwitchMyMainAccessKeyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    UpdateMyKeypairPayload as UpdateMyKeypairPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.keypair.types.node import KeyPairGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="A keypair returned at creation time, including its one-time secret key.",
    ),
    model=CreateKeypairPayloadDTO,
    name="CreateKeypairPayload",
)
class CreateKeypairPayloadGQL(PydanticOutputMixin[CreateKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The newly created keypair.")
    secret_key: str = gql_field(
        description="The secret key of the generated keypair. Only returned at creation time."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    ),
    model=IssueMyKeypairPayloadDTO,
    name="IssueMyKeypairPayload",
)
class IssueMyKeypairPayloadGQL(PydanticOutputMixin[IssueMyKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The newly created keypair.")
    secret_key: str = gql_field(
        description="The newly generated secret key. This value is only returned at creation time."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after revoking a keypair.",
    ),
    model=RevokeMyKeypairPayloadDTO,
    all_fields=True,
    name="RevokeMyKeypairPayload",
)
class RevokeMyKeypairPayloadGQL(PydanticOutputMixin[RevokeMyKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after switching the main access key.",
    ),
    model=SwitchMyMainAccessKeyPayloadDTO,
    all_fields=True,
    name="SwitchMyMainAccessKeyPayload",
)
class SwitchMyMainAccessKeyPayloadGQL(PydanticOutputMixin[SwitchMyMainAccessKeyPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after updating a keypair.",
    ),
    model=UpdateMyKeypairPayloadDTO,
    name="UpdateMyKeypairPayload",
)
class UpdateMyKeypairPayloadGQL(PydanticOutputMixin[UpdateMyKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The updated keypair.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after admin creates a keypair. The secret_key is only shown once.",
    ),
    model=AdminCreateKeypairPayloadDTO,
    name="AdminCreateKeypairPayload",
)
class AdminCreateKeypairPayloadGQL(PydanticOutputMixin[AdminCreateKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The newly created keypair.")
    secret_key: str = gql_field(description="The secret key. Only returned at creation time.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after admin updates a keypair.",
    ),
    model=AdminUpdateKeypairPayloadDTO,
    name="AdminUpdateKeypairPayload",
)
class AdminUpdateKeypairPayloadGQL(PydanticOutputMixin[AdminUpdateKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The updated keypair.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after admin deletes a keypair.",
    ),
    model=AdminDeleteKeypairPayloadDTO,
    all_fields=True,
    name="AdminDeleteKeypairPayload",
)
class AdminDeleteKeypairPayloadGQL(PydanticOutputMixin[AdminDeleteKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="SSH keypair read model. Never includes the private key.",
    ),
    model=SSHKeypairNodeDTO,
    all_fields=True,
    name="SSHKeypairNode",
)
class SSHKeypairNodeGQL(PydanticOutputMixin[SSHKeypairNodeDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after admin registers a user's SSH keypair.",
    ),
    model=AdminRegisterSSHKeypairPayloadDTO,
    all_fields=True,
    name="AdminRegisterSSHKeypairPayload",
)
class AdminRegisterSSHKeypairPayloadGQL(PydanticOutputMixin[AdminRegisterSSHKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after admin clears a user's SSH keypair.",
    ),
    model=AdminDeleteSSHKeypairPayloadDTO,
    all_fields=True,
    name="AdminDeleteSSHKeypairPayload",
)
class AdminDeleteSSHKeypairPayloadGQL(PydanticOutputMixin[AdminDeleteSSHKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned by admin SSH keypair lookup.",
    ),
    model=AdminGetSSHKeypairPayloadDTO,
    name="AdminGetSSHKeypairPayload",
)
class AdminGetSSHKeypairPayloadGQL(PydanticOutputMixin[AdminGetSSHKeypairPayloadDTO]):
    keypair: SSHKeypairNodeGQL = gql_field(description="SSH keypair public information.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="How many stored keypair secrets one provider's one key still holds.",
    ),
    model=KeypairSecretKeyCountDTO,
    name="KeypairSecretKeyCount",
)
class KeypairSecretKeyCountGQL(PydanticOutputMixin[KeypairSecretKeyCountDTO]):
    provider_type: str = gql_field(
        description="The key provider holding these secrets. 'plain' means legacy plaintext."
    )
    key_id: str | None = gql_field(description="The key within that provider. Unset for plaintext.")
    count: int = gql_field(description="How many stored secrets that key holds.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Which key each stored keypair secret sits on.",
    ),
    model=AdminKeypairSecretStatusPayloadDTO,
    name="AdminKeypairSecretStatusPayload",
)
class AdminKeypairSecretStatusPayloadGQL(PydanticOutputMixin[AdminKeypairSecretStatusPayloadDTO]):
    write_provider_type: str = gql_field(
        description="The key provider new and re-encrypted secrets are written through."
    )
    counts: list[KeypairSecretKeyCountGQL] = gql_field(
        description="The stored secrets, grouped by the key holding them."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="What one re-encryption pass wrote, and what the column holds afterwards.",
    ),
    model=AdminReencryptKeypairSecretsPayloadDTO,
    name="AdminReencryptKeypairSecretsPayload",
)
class AdminReencryptKeypairSecretsPayloadGQL(
    PydanticOutputMixin[AdminReencryptKeypairSecretsPayloadDTO]
):
    scanned: int = gql_field(description="How many rows this pass read.")
    reencrypted: int = gql_field(description="How many rows this pass wrote back.")
    status: AdminKeypairSecretStatusPayloadGQL = gql_field(
        description="The count per key id after this pass."
    )
