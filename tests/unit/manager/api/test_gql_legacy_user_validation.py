"""
Tests for user UID/GID validation in GraphQL legacy API.

Tests for:
- _validate_container_uid_gid() function
- validate_user_mutation_props() function
- CreateUser.mutate() validation behavior
- ModifyUser.mutate() validation behavior
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
from graphql import Undefined

from ai.backend.manager.api.gql_legacy.user import (
    CreateUser,
    ModifyUser,
    ModifyUserInput,
    UserInput,
    _validate_container_uid_gid,
    validate_user_mutation_props,
)

# ============= Helper Functions =============


def create_user_input_with_container_fields(
    container_uid: int | Any = Undefined,
    container_main_gid: int | Any = Undefined,
    container_gids: list[int] | None = None,
) -> UserInput:
    """Helper to create UserInput with container fields set."""
    props = UserInput()
    props.container_uid = container_uid
    props.container_main_gid = container_main_gid
    props.container_gids = container_gids if container_gids is not None else []
    return props


def create_modify_user_input_with_container_fields(
    container_uid: int | Any = Undefined,
    container_main_gid: int | Any = Undefined,
    container_gids: list[int] | None = None,
) -> ModifyUserInput:
    """Helper to create ModifyUserInput with container fields set."""
    props = ModifyUserInput()
    props.container_uid = container_uid
    props.container_main_gid = container_main_gid
    props.container_gids = container_gids if container_gids is not None else []
    return props


# ============= Part 1: Validation Function Unit Tests =============


class TestValidateContainerUidGid:
    """Tests for _validate_container_uid_gid function."""

    def test_valid_positive_value(self) -> None:
        """Accept positive integer values (e.g., 1000)."""
        # Should not raise
        _validate_container_uid_gid(1000)
        _validate_container_uid_gid(65534)

    def test_valid_zero_value(self) -> None:
        """Accept zero value (root user/group)."""
        # Should not raise
        _validate_container_uid_gid(0)

    def test_valid_undefined_value(self) -> None:
        """Skip validation when value is Undefined."""
        # Should not raise
        _validate_container_uid_gid(Undefined)

    def test_invalid_negative_value_raises_error(self) -> None:
        """Raise ValueError for negative values."""
        with pytest.raises(ValueError):
            _validate_container_uid_gid(-1)

        with pytest.raises(ValueError):
            _validate_container_uid_gid(-1000)

    def test_error_message_content(self) -> None:
        """Verify error message contains expected text."""
        with pytest.raises(ValueError, match="UID and GID must be non-negative integers"):
            _validate_container_uid_gid(-1)


class TestValidateUserMutationProps:
    """Tests for validate_user_mutation_props function."""

    def test_user_input_with_valid_uid_gid(self) -> None:
        """Accept UserInput with valid container_uid, container_main_gid."""
        props = create_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[100, 200, 300],
        )
        # Should not raise
        validate_user_mutation_props(props)

    def test_user_input_with_undefined_values(self) -> None:
        """Accept UserInput when all container fields are Undefined."""
        props = create_user_input_with_container_fields()
        # Should not raise
        validate_user_mutation_props(props)

    def test_user_input_with_negative_uid_raises_error(self) -> None:
        """Raise ValueError when container_uid is negative."""
        props = create_user_input_with_container_fields(
            container_uid=-1,
            container_main_gid=1000,
        )
        with pytest.raises(ValueError, match="UID and GID must be non-negative integers"):
            validate_user_mutation_props(props)

    def test_user_input_with_negative_main_gid_raises_error(self) -> None:
        """Raise ValueError when container_main_gid is negative."""
        props = create_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=-1,
        )
        with pytest.raises(ValueError, match="UID and GID must be non-negative integers"):
            validate_user_mutation_props(props)

    def test_user_input_with_negative_gid_in_list_raises_error(self) -> None:
        """Raise ValueError when container_gids contains negative value."""
        props = create_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[100, -1, 200],
        )
        with pytest.raises(ValueError, match="UID and GID must be non-negative integers"):
            validate_user_mutation_props(props)

    def test_modify_user_input_with_valid_uid_gid(self) -> None:
        """Accept ModifyUserInput with valid container_uid, container_main_gid."""
        props = create_modify_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=1000,
        )
        # Should not raise
        validate_user_mutation_props(props)

    def test_modify_user_input_with_undefined_values(self) -> None:
        """Accept ModifyUserInput when all container fields are Undefined."""
        props = create_modify_user_input_with_container_fields()
        # Should not raise
        validate_user_mutation_props(props)

    def test_modify_user_input_with_negative_uid_raises_error(self) -> None:
        """Raise ValueError when ModifyUserInput container_uid is negative."""
        props = create_modify_user_input_with_container_fields(
            container_uid=-1,
        )
        with pytest.raises(ValueError, match="UID and GID must be non-negative integers"):
            validate_user_mutation_props(props)


# ============= Part 2: Handler Tests with Mocked Processor =============


@pytest.fixture
def mock_graph_ctx() -> MagicMock:
    """Create mock GraphQueryContext with mocked processors."""
    ctx = MagicMock()

    # Mock config_provider for password hashing config
    ctx.config_provider.config.auth.password_hash_algorithm = "argon2"
    ctx.config_provider.config.auth.password_hash_rounds = 4
    ctx.config_provider.config.auth.password_hash_salt_size = 16

    # Mock processors.user.create_user
    ctx.processors.user.create_user.wait_for_complete = AsyncMock()
    ctx.processors.user.modify_user.wait_for_complete = AsyncMock()

    return ctx


@pytest.fixture
def mock_info(mock_graph_ctx: MagicMock) -> MagicMock:
    """Create mock graphene.ResolveInfo with mocked context."""
    info = MagicMock(spec=graphene.ResolveInfo)
    info.context = mock_graph_ctx
    return info


class TestCreateUserMutationValidation:
    """Tests for CreateUser.mutate() validation behavior."""

    @pytest.mark.asyncio
    async def test_create_user_with_negative_uid_raises_before_processor(
        self,
        mock_info: MagicMock,
        mock_graph_ctx: MagicMock,
    ) -> None:
        """CreateUser.mutate() raises ValueError before calling processor."""
        props = create_user_input_with_container_fields(
            container_uid=-1,
            container_main_gid=1000,
        )
        # Set required fields for UserInput
        props.username = "testuser"
        props.password = "testpass"
        props.need_password_change = False
        props.domain_name = "default"

        with pytest.raises(ValueError, match="UID and GID must be non-negative"):
            await CreateUser.mutate(None, mock_info, "test@example.com", props)

        # Verify processor was NOT called
        mock_graph_ctx.processors.user.create_user.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_with_negative_gid_raises_before_processor(
        self,
        mock_info: MagicMock,
        mock_graph_ctx: MagicMock,
    ) -> None:
        """CreateUser.mutate() raises ValueError for negative container_main_gid."""
        props = create_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=-1,
        )
        # Set required fields for UserInput
        props.username = "testuser"
        props.password = "testpass"
        props.need_password_change = False
        props.domain_name = "default"

        with pytest.raises(ValueError, match="UID and GID must be non-negative"):
            await CreateUser.mutate(None, mock_info, "test@example.com", props)

        # Verify processor was NOT called
        mock_graph_ctx.processors.user.create_user.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_with_negative_supplementary_gid_raises_before_processor(
        self,
        mock_info: MagicMock,
        mock_graph_ctx: MagicMock,
    ) -> None:
        """CreateUser.mutate() raises ValueError for negative gid in container_gids."""
        props = create_user_input_with_container_fields(
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[100, -1, 200],
        )
        # Set required fields for UserInput
        props.username = "testuser"
        props.password = "testpass"
        props.need_password_change = False
        props.domain_name = "default"

        with pytest.raises(ValueError, match="UID and GID must be non-negative"):
            await CreateUser.mutate(None, mock_info, "test@example.com", props)

        # Verify processor was NOT called
        mock_graph_ctx.processors.user.create_user.wait_for_complete.assert_not_called()


class TestModifyUserMutationValidation:
    """Tests for ModifyUser.mutate() validation behavior."""

    @pytest.mark.asyncio
    async def test_modify_user_with_negative_uid_raises_before_processor(
        self,
        mock_info: MagicMock,
        mock_graph_ctx: MagicMock,
    ) -> None:
        """ModifyUser.mutate() raises ValueError before calling processor."""
        props = create_modify_user_input_with_container_fields(
            container_uid=-1,
        )

        with pytest.raises(ValueError, match="UID and GID must be non-negative"):
            await ModifyUser.mutate(None, mock_info, "test@example.com", props)

        # Verify processor was NOT called
        mock_graph_ctx.processors.user.modify_user.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_modify_user_with_negative_gid_raises_before_processor(
        self,
        mock_info: MagicMock,
        mock_graph_ctx: MagicMock,
    ) -> None:
        """ModifyUser.mutate() raises ValueError for negative container_main_gid."""
        props = create_modify_user_input_with_container_fields(
            container_main_gid=-1,
        )

        with pytest.raises(ValueError, match="UID and GID must be non-negative"):
            await ModifyUser.mutate(None, mock_info, "test@example.com", props)

        # Verify processor was NOT called
        mock_graph_ctx.processors.user.modify_user.wait_for_complete.assert_not_called()
