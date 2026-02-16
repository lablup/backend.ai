import pytest

from ai.backend.common.data.permission.exceptions import InvalidTypeConversion
from ai.backend.common.data.permission.types import (
    EntityType,
    ScopeType,
)

# The 12 overlapping members between EntityType and ScopeType
OVERLAPPING_MEMBERS: list[tuple[EntityType, ScopeType]] = [
    (EntityType.DOMAIN, ScopeType.DOMAIN),
    (EntityType.PROJECT, ScopeType.PROJECT),
    (EntityType.USER, ScopeType.USER),
    (EntityType.VFOLDER, ScopeType.VFOLDER),
    (EntityType.IMAGE, ScopeType.IMAGE),
    (EntityType.SESSION, ScopeType.SESSION),
    (EntityType.ARTIFACT, ScopeType.ARTIFACT),
    (EntityType.ARTIFACT_REGISTRY, ScopeType.ARTIFACT_REGISTRY),
    (EntityType.CONTAINER_REGISTRY, ScopeType.CONTAINER_REGISTRY),
    (EntityType.DEPLOYMENT, ScopeType.DEPLOYMENT),
    (EntityType.RESOURCE_GROUP, ScopeType.RESOURCE_GROUP),
    (EntityType.ROLE, ScopeType.ROLE),
]


class TestEntityTypeToScopeType:
    @pytest.mark.parametrize(
        ("entity_type", "scope_type"),
        OVERLAPPING_MEMBERS,
        ids=[et.value for et, _ in OVERLAPPING_MEMBERS],
    )
    def test_converts_overlapping_entity_type_to_scope_type(
        self, entity_type: EntityType, scope_type: ScopeType
    ) -> None:
        assert entity_type.to_scope_type() == scope_type

    @pytest.mark.parametrize(
        "entity_type",
        [EntityType.AGENT, EntityType.AUTH, EntityType.APP_CONFIG],
        ids=["agent", "auth", "app_config"],
    )
    def test_raises_for_entity_type_without_scope_type(self, entity_type: EntityType) -> None:
        with pytest.raises(InvalidTypeConversion, match="has no corresponding ScopeType"):
            entity_type.to_scope_type()


class TestScopeTypeToEntityType:
    @pytest.mark.parametrize(
        ("entity_type", "scope_type"),
        OVERLAPPING_MEMBERS,
        ids=[et.value for et, _ in OVERLAPPING_MEMBERS],
    )
    def test_converts_overlapping_scope_type_to_entity_type(
        self, entity_type: EntityType, scope_type: ScopeType
    ) -> None:
        assert scope_type.to_entity_type() == entity_type

    @pytest.mark.parametrize(
        "scope_type",
        [ScopeType.GLOBAL, ScopeType.STORAGE_HOST, ScopeType.ARTIFACT_REVISION],
        ids=["global", "storage_host", "artifact_revision"],
    )
    def test_raises_for_scope_type_without_entity_type(self, scope_type: ScopeType) -> None:
        with pytest.raises(InvalidTypeConversion, match="has no corresponding EntityType"):
            scope_type.to_entity_type()


class TestRoundtrip:
    @pytest.mark.parametrize(
        ("entity_type", "scope_type"),
        OVERLAPPING_MEMBERS,
        ids=[et.value for et, _ in OVERLAPPING_MEMBERS],
    )
    def test_entity_to_scope_and_back(self, entity_type: EntityType, scope_type: ScopeType) -> None:
        assert entity_type.to_scope_type().to_entity_type() == entity_type

    @pytest.mark.parametrize(
        ("entity_type", "scope_type"),
        OVERLAPPING_MEMBERS,
        ids=[et.value for et, _ in OVERLAPPING_MEMBERS],
    )
    def test_scope_to_entity_and_back(self, entity_type: EntityType, scope_type: ScopeType) -> None:
        assert scope_type.to_entity_type().to_scope_type() == scope_type
