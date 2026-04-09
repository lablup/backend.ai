from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.data.runtime_variant_preset.types import (
    ChoiceItemData,
    ChoiceOptionData,
    NumberOptionData,
    RuntimeVariantPresetData,
    SliderOptionData,
    TextOptionData,
    UIOptionData,
)
from ai.backend.manager.models.base import GUID, Base, PydanticColumn
from ai.backend.manager.models.runtime_variant_preset.types import UIOption

if TYPE_CHECKING:
    from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow

__all__ = ("RuntimeVariantPresetRow",)


def _get_runtime_variant_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow

    return foreign(RuntimeVariantPresetRow.runtime_variant) == RuntimeVariantRow.id


class RuntimeVariantPresetRow(Base):  # type: ignore[misc]
    __tablename__ = "runtime_variant_presets"

    __table_args__ = (
        sa.UniqueConstraint(
            "runtime_variant", "name", name="uq_runtime_variant_presets_variant_name"
        ),
        sa.Index("ix_runtime_variant_presets_variant_rank", "runtime_variant", "rank"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    runtime_variant: Mapped[uuid.UUID] = mapped_column("runtime_variant", GUID, nullable=False)
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    rank: Mapped[int] = mapped_column("rank", sa.Integer, nullable=False)
    preset_target: Mapped[str] = mapped_column(
        "preset_target", sa.String(length=16), nullable=False
    )
    value_type: Mapped[str] = mapped_column("value_type", sa.String(length=16), nullable=False)
    default_value: Mapped[str | None] = mapped_column(
        "default_value", sa.String(length=512), nullable=True
    )
    key: Mapped[str] = mapped_column("key", sa.String(length=256), nullable=False)

    # UI metadata
    category: Mapped[str | None] = mapped_column("category", sa.String(length=64), nullable=True)
    ui_type: Mapped[str | None] = mapped_column("ui_type", sa.String(length=32), nullable=True)
    display_name: Mapped[str | None] = mapped_column(
        "display_name", sa.String(length=256), nullable=True
    )
    ui_option: Mapped[UIOption | None] = mapped_column(
        "ui_option", PydanticColumn(UIOption), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.now(),
    )

    runtime_variant_row: Mapped[RuntimeVariantRow] = relationship(
        "RuntimeVariantRow",
        primaryjoin=_get_runtime_variant_join_condition,
    )

    @staticmethod
    def _convert_ui_option_to_data(opt: UIOption | None) -> UIOptionData | None:
        if opt is None:
            return None
        return UIOptionData(
            ui_type=opt.ui_type.value,
            slider=SliderOptionData(min=opt.slider.min, max=opt.slider.max, step=opt.slider.step)
            if opt.slider
            else None,
            number=NumberOptionData(min=opt.number.min, max=opt.number.max) if opt.number else None,
            choices=ChoiceOptionData(
                items=[ChoiceItemData(value=c.value, label=c.label) for c in opt.choices.items]
            )
            if opt.choices
            else None,
            text=TextOptionData(placeholder=opt.text.placeholder) if opt.text else None,
        )

    def to_data(self) -> RuntimeVariantPresetData:
        return RuntimeVariantPresetData(
            id=self.id,
            runtime_variant_id=self.runtime_variant,
            name=self.name,
            description=self.description,
            rank=self.rank,
            preset_target=PresetTarget(self.preset_target),
            value_type=PresetValueType(self.value_type),
            default_value=self.default_value,
            key=self.key,
            category=self.category,
            ui_type=self.ui_type,
            display_name=self.display_name,
            ui_option=self._convert_ui_option_to_data(self.ui_option),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
