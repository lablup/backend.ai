"""Unit tests for ``PydanticColumn`` bind/result behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import ClassVar

import pytest
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.engine import Dialect
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.models.base import PydanticColumn
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestPydanticColumnExcludeUnset:
    @pytest.fixture
    def dialect(self) -> Dialect:
        # process_bind_param/process_result_value ignore the dialect.
        return DefaultDialect()

    @pytest.fixture
    def column(self) -> PydanticColumn[ModelDefinitionDraft]:
        return PydanticColumn(ModelDefinitionDraft, exclude_unset=True)

    @pytest.fixture
    def column_with_exclude_unset_false(self) -> PydanticColumn[ModelDefinitionDraft]:
        return PydanticColumn(ModelDefinitionDraft, exclude_unset=False)

    def test_round_trip_keeps_unset_fields_unset(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column.process_bind_param(draft, dialect)
        loaded = column.process_result_value(stored, dialect)

        assert stored is not None
        assert "shell" not in stored["models"][0]["service"]
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" not in service.model_fields_set

    def test_preserves_explicit_null(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        draft = ModelDefinitionDraft.model_validate({
            "models": [{"service": {"port": 8080, "shell": None}}]
        })

        stored = column.process_bind_param(draft, dialect)
        loaded = column.process_result_value(stored, dialect)

        assert stored is not None
        assert stored["models"][0]["service"]["shell"] is None
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" in service.model_fields_set

    def test_default_dump_materializes_unset_fields_as_null(
        self,
        column_with_exclude_unset_false: PydanticColumn[ModelDefinitionDraft],
        dialect: Dialect,
    ) -> None:
        # Contrast case: without exclude_unset, unset fields are stored as explicit
        # nulls, and reloading marks them "explicitly set" — the legacy bug behavior.
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column_with_exclude_unset_false.process_bind_param(draft, dialect)
        loaded = column_with_exclude_unset_false.process_result_value(stored, dialect)

        assert stored is not None
        assert stored["models"][0]["service"]["shell"] is None
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" in service.model_fields_set
        assert service.shell is None

    def test_copy_preserves_exclude_unset(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        # SQLAlchemy clones TypeDecorators internally; a copy() dropping the flag
        # would silently revert to materializing nulls.
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column.copy().process_bind_param(draft, dialect)

        assert stored is not None
        assert "shell" not in stored["models"][0]["service"]


class _Spec(BaseModel):
    value: int


class _ProbeBase(DeclarativeBase):
    __table__: ClassVar[sa.Table]


class _ProbeRow(_ProbeBase):
    __tablename__ = "pydantic_column_probes"

    id: Mapped[int] = mapped_column("id", sa.Integer, primary_key=True)
    optional_spec: Mapped[_Spec | None] = mapped_column(
        "optional_spec", PydanticColumn(_Spec), nullable=True
    )
    required_spec: Mapped[_Spec] = mapped_column(
        "required_spec", PydanticColumn(_Spec), nullable=False
    )


class TestPydanticColumnStoresNoneAsSQLNull:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [_ProbeRow]):
            yield database_connection

    async def _is_sql_null(self, db: ExtendedAsyncSAEngine, row_id: int) -> bool:
        async with db.begin_readonly() as conn:
            result = await conn.scalar(
                sa.select(_ProbeRow.optional_spec.is_(None)).where(_ProbeRow.id == row_id)
            )
        return bool(result)

    async def test_core_insert(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.execute(
                sa.insert(_ProbeRow).values(id=1, optional_spec=None, required_spec=_Spec(value=1))
            )

        assert await self._is_sql_null(db, 1)

    async def test_orm_insert(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as session:
            session.add(_ProbeRow(id=1, optional_spec=None, required_spec=_Spec(value=1)))

        assert await self._is_sql_null(db, 1)

    async def test_core_update(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.execute(
                sa.insert(_ProbeRow).values(
                    id=1, optional_spec=_Spec(value=1), required_spec=_Spec(value=1)
                )
            )
            await conn.execute(
                sa.update(_ProbeRow).where(_ProbeRow.id == 1).values(optional_spec=None)
            )

        assert await self._is_sql_null(db, 1)

    async def test_orm_update(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as session:
            session.add(_ProbeRow(id=1, optional_spec=_Spec(value=1), required_spec=_Spec(value=1)))
        async with db.begin_session() as session:
            row = await session.get_one(_ProbeRow, 1)
            row.optional_spec = None

        assert await self._is_sql_null(db, 1)

    async def test_none_in_not_null_column_is_rejected(self, db: ExtendedAsyncSAEngine) -> None:
        with pytest.raises(IntegrityError):
            async with db.begin() as conn:
                await conn.execute(
                    sa.insert(_ProbeRow).values(id=1, optional_spec=None, required_spec=None)
                )
