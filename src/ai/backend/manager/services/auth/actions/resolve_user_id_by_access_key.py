from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.keypair.lookups import KeypairAccessKeyUserLookup
from ai.backend.manager.models.keypair.row import KeyPairRow


@dataclass(frozen=True)
class AccessKeyLookupKey(LookupKey):
    """The access key a request authenticates with."""

    access_key: AccessKey

    @override
    def kind(self) -> str:
        return "access_key"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"access_key": str(self.access_key)}


@dataclass(frozen=True)
class ResolveUserIDByAccessKeyAction(LookupEntityOpsAction[KeyPairRow, UserID]):
    """Resolve an access key into the user it authenticates as."""

    access_key: AccessKey

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_user_by_access_key"

    @override
    def lookup_key(self) -> LookupKey:
        return AccessKeyLookupKey(self.access_key)

    @override
    def to_lookup(self) -> KeypairAccessKeyUserLookup:
        return KeypairAccessKeyUserLookup(access_key=self.access_key)
