"""Shared fixtures for validator tests."""

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Optional

import pytest
import yarl

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.models import NetworkRow
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionCreationSpec
from ai.backend.manager.types import UserScope


@pytest.fixture
def session_spec_factory() -> Callable[..., SessionCreationSpec]:
    """Factory fixture for creating SessionCreationSpec instances."""

    def create_spec(
        session_creation_id: str = "test-001",
        session_name: str = "test-session",
        access_key: AccessKey = AccessKey("test-key"),
        user_scope: UserScope = UserScope(
            domain_name="default",
            group_id=uuid.uuid4(),
            user_uuid=uuid.uuid4(),
            user_role="user",
        ),
        session_type: SessionTypes = SessionTypes.INTERACTIVE,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        priority: int = 10,
        resource_policy: dict | None = None,
        kernel_specs: list[KernelEnqueueingConfig] | None = None,
        creation_spec: dict | None = None,
        scaling_group: Optional[str] = None,
        session_tag: Optional[str] = None,
        starts_at: Optional[datetime] = None,
        batch_timeout: Optional[timedelta] = None,
        dependency_sessions: Optional[list[SessionId]] = None,
        callback_url: Optional[yarl.URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
        network: Optional[NetworkRow] = None,
        designated_agent_list: Optional[list[str]] = None,
        internal_data: Optional[dict] = None,
        public_sgroup_only: bool = True,
    ) -> SessionCreationSpec:
        return SessionCreationSpec(
            session_creation_id=session_creation_id,
            session_name=session_name,
            access_key=access_key,
            user_scope=user_scope,
            session_type=session_type,
            cluster_mode=cluster_mode,
            cluster_size=cluster_size,
            priority=priority,
            resource_policy=resource_policy or {},
            kernel_specs=kernel_specs or [],
            creation_spec=creation_spec or {},
            scaling_group=scaling_group,
            session_tag=session_tag,
            starts_at=starts_at,
            batch_timeout=batch_timeout,
            dependency_sessions=dependency_sessions,
            callback_url=callback_url,
            route_id=route_id,
            sudo_session_enabled=sudo_session_enabled,
            network=network,
            designated_agent_list=designated_agent_list,
            internal_data=internal_data,
            public_sgroup_only=public_sgroup_only,
        )

    return create_spec
