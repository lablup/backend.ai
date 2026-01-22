"""
Tests for group purgers functionality.
Tests the purger pattern implementation for group-related deletions.
"""

from __future__ import annotations

import uuid

from ai.backend.manager.repositories.base.purger import BatchPurger
from ai.backend.manager.repositories.group.purgers import (
    GroupBatchPurgerSpec,
    GroupEndpointBatchPurgerSpec,
    GroupEndpointSessionBatchPurgerSpec,
    GroupKernelBatchPurgerSpec,
    GroupSessionBatchPurgerSpec,
    create_group_endpoint_purger,
    create_group_endpoint_session_purger,
    create_group_kernel_purger,
    create_group_purger,
    create_group_session_purger,
)


class TestGroupPurgerFactoryFunctions:
    """Tests for purger factory functions."""

    def test_create_group_kernel_purger(self) -> None:
        """Test create_group_kernel_purger returns correct BatchPurger."""
        group_id = uuid.uuid4()

        purger = create_group_kernel_purger(group_id)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, GroupKernelBatchPurgerSpec)
        assert purger.spec.group_id == group_id

    def test_create_group_session_purger(self) -> None:
        """Test create_group_session_purger returns correct BatchPurger."""
        group_id = uuid.uuid4()

        purger = create_group_session_purger(group_id)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, GroupSessionBatchPurgerSpec)
        assert purger.spec.group_id == group_id

    def test_create_group_endpoint_session_purger(self) -> None:
        """Test create_group_endpoint_session_purger returns correct BatchPurger."""
        group_id = uuid.uuid4()

        purger = create_group_endpoint_session_purger(group_id)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, GroupEndpointSessionBatchPurgerSpec)
        assert purger.spec.group_id == group_id

    def test_create_group_endpoint_purger(self) -> None:
        """Test create_group_endpoint_purger returns correct BatchPurger."""
        group_id = uuid.uuid4()

        purger = create_group_endpoint_purger(group_id)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, GroupEndpointBatchPurgerSpec)
        assert purger.spec.group_id == group_id

    def test_create_group_purger(self) -> None:
        """Test create_group_purger returns correct BatchPurger with batch_size=1."""
        group_id = uuid.uuid4()

        purger = create_group_purger(group_id)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, GroupBatchPurgerSpec)
        assert purger.spec.group_id == group_id
        assert purger.batch_size == 1  # Group purger should have batch_size=1
