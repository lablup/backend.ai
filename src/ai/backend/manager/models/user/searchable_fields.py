"""What a user search can filter and order by, and how a user row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.specs.conditions.array import ArrayConditions
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.user.row import UserRow


class _UserOwnFields(RowDataConverter[UserRow, UserData]):
    """The user's own columns.

    ``password`` and ``totp_key`` are not declared: neither is in the data, and both
    leak through repeated filtering. ``allowed_client_ip`` is an access control
    setting and keeps both slots empty. ``UserData.is_active`` has no column behind
    it and is read off ``status``.
    """

    id = SearchableField(UserRow.uuid, UUIDConditions(UserRow.uuid), ColumnOrder(UserRow.uuid))
    uuid = SearchableField(UserRow.uuid, UUIDConditions(UserRow.uuid), ColumnOrder(UserRow.uuid))
    username = SearchableField(
        UserRow.username, StringConditions(UserRow.username), ColumnOrder(UserRow.username)
    )
    email = SearchableField(
        UserRow.email, StringConditions(UserRow.email), ColumnOrder(UserRow.email)
    )
    need_password_change = SearchableField(
        UserRow.need_password_change,
        BoolConditions(UserRow.need_password_change),
        ColumnOrder(UserRow.need_password_change),
    )
    full_name = SearchableField(
        UserRow.full_name, StringConditions(UserRow.full_name), ColumnOrder(UserRow.full_name)
    )
    description = SearchableField(
        UserRow.description, StringConditions(UserRow.description), ColumnOrder(UserRow.description)
    )
    status = SearchableField(
        UserRow.status, EnumConditions(UserRow.status, UserStatus), ColumnOrder(UserRow.status)
    )
    status_info = SearchableField(
        UserRow.status_info, StringConditions(UserRow.status_info), ColumnOrder(UserRow.status_info)
    )
    created_at = SearchableField(
        UserRow.created_at, DateTimeConditions(UserRow.created_at), ColumnOrder(UserRow.created_at)
    )
    modified_at = SearchableField(
        UserRow.updated_at, DateTimeConditions(UserRow.updated_at), ColumnOrder(UserRow.updated_at)
    )
    domain_name = SearchableField(
        UserRow.domain_name, StringConditions(UserRow.domain_name), ColumnOrder(UserRow.domain_name)
    )
    domain_id = SearchableField(
        UserRow.domain_id, UUIDConditions(UserRow.domain_id), ColumnOrder(UserRow.domain_id)
    )
    role = SearchableField(
        UserRow.role, EnumConditions(UserRow.role, UserRole), ColumnOrder(UserRow.role)
    )
    resource_policy = SearchableField(
        UserRow.resource_policy,
        StringConditions(UserRow.resource_policy),
        ColumnOrder(UserRow.resource_policy),
    )
    allowed_client_ip = SearchableField(UserRow.allowed_client_ip, None, None)
    totp_activated = SearchableField(
        UserRow.totp_activated,
        BoolConditions(UserRow.totp_activated),
        ColumnOrder(UserRow.totp_activated),
    )
    totp_activated_at = SearchableField(
        UserRow.totp_activated_at,
        DateTimeConditions(UserRow.totp_activated_at),
        ColumnOrder(UserRow.totp_activated_at),
    )
    sudo_session_enabled = SearchableField(
        UserRow.sudo_session_enabled,
        BoolConditions(UserRow.sudo_session_enabled),
        ColumnOrder(UserRow.sudo_session_enabled),
    )
    container_uid = SearchableField(
        UserRow.container_uid,
        IntConditions(UserRow.container_uid),
        ColumnOrder(UserRow.container_uid),
    )
    container_main_gid = SearchableField(
        UserRow.container_main_gid,
        IntConditions(UserRow.container_main_gid),
        ColumnOrder(UserRow.container_main_gid),
    )
    container_gids = SearchableField(
        UserRow.container_gids,
        ArrayConditions(UserRow.container_gids, sa.Integer()),
        None,
    )
    integration_name = SearchableField(
        UserRow.integration_id,
        StringConditions(UserRow.integration_id),
        ColumnOrder(UserRow.integration_id),
    )

    @override
    def to_data(self, row: UserRow) -> UserData:
        status = self.status.read(row)
        allowed_client_ip = self.allowed_client_ip.read(row)
        return UserData(
            id=self.id.read(row),
            uuid=self.uuid.read(row),
            username=self.username.read(row),
            email=self.email.read(row),
            need_password_change=self.need_password_change.read(row),
            full_name=self.full_name.read(row),
            description=self.description.read(row),
            is_active=status == UserStatus.ACTIVE,
            status=status.value,
            status_info=self.status_info.read(row),
            created_at=self.created_at.read(row),
            modified_at=self.modified_at.read(row),
            domain_name=self.domain_name.read(row),
            domain_id=self.domain_id.read(row),
            role=self.role.read(row),
            resource_policy=self.resource_policy.read(row),
            allowed_client_ip=[str(ip) for ip in allowed_client_ip] if allowed_client_ip else None,
            totp_activated=self.totp_activated.read(row),
            totp_activated_at=self.totp_activated_at.read(row),
            sudo_session_enabled=self.sudo_session_enabled.read(row),
            container_uid=self.container_uid.read(row),
            container_main_gid=self.container_main_gid.read(row),
            container_gids=self.container_gids.read(row),
            integration_name=self.integration_name.read(row),
        )


class _UserNestedFields:
    """The keypairs the user owns, read under the user's own permission.

    A keypair is the user's field row (``KeypairCreator`` is a
    ``FieldCreator[UserID, ...]``), so one permission answers for the pair. Narrowing a
    user search by keypair does not replace the keypair search, which lists the rows
    themselves.
    """

    keypairs = NestedSearchableField(
        KeyPairSearchableFields.own,
        ToManyCorrelation(KeyPairRow, UserRow, KeyPairRow.user == UserRow.uuid),
    )


class UserSearchableFields:
    """What a user search reaches.

    There is no ``linked``. A column naming a user (``groups.creator_id``,
    ``error_logs.user``, ``entity_shares.sharer_user_id``) records provenance or
    ownership, not a use, so no entity answers a ``usage``.
    """

    own = _UserOwnFields()
    nested = _UserNestedFields
