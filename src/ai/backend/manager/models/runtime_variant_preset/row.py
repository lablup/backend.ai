from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
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
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("RuntimeVariantPresetRow",)


class RuntimeVariantPresetRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "runtime_variant_presets"

    __table_args__ = (
        sa.UniqueConstraint(
            "runtime_variant", "name", name="uq_runtime_variant_presets_variant_name"
        ),
        sa.Index("ix_runtime_variant_presets_variant_rank", "runtime_variant", "rank"),
    )

    id: Mapped[RuntimeVariantPresetID] = mapped_column(
        "id",
        GUID(RuntimeVariantPresetID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    runtime_variant: Mapped[RuntimeVariantID] = mapped_column(
        "runtime_variant", GUID(RuntimeVariantID), nullable=False
    )
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
    required: Mapped[bool] = mapped_column(
        "required", sa.Boolean, nullable=False, server_default=sa.false()
    )

    # UI metadata
    category: Mapped[str | None] = mapped_column("category", sa.String(length=64), nullable=True)
    display_name: Mapped[str | None] = mapped_column(
        "display_name", sa.String(length=256), nullable=True
    )
    # ``ui_option`` JSONB carries both ``ui_type`` and the type-specific
    # sub-field config (slider/number/choices/text). The previously
    # separate ``ui_type`` column has been folded into this JSONB.
    ui_option: Mapped[UIOption | None] = mapped_column(
        "ui_option", PydanticColumn(UIOption), nullable=True
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
        ui_option_data = self._convert_ui_option_to_data(self.ui_option)
        return RuntimeVariantPresetData(
            id=RuntimeVariantPresetID(self.id),
            runtime_variant_id=RuntimeVariantID(self.runtime_variant),
            name=self.name,
            description=self.description,
            rank=self.rank,
            preset_target=PresetTarget(self.preset_target),
            value_type=PresetValueType(self.value_type),
            default_value=self.default_value,
            key=self.key,
            required=self.required,
            category=self.category,
            ui_type=ui_option_data.ui_type if ui_option_data is not None else None,
            display_name=self.display_name,
            ui_option=ui_option_data,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
