"""What a runtime variant preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

import re
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VERSION_PREFIX_PATTERN,
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
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.base import SearchOrder
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

_VERSION_PREFIX = re.compile(VERSION_PREFIX_PATTERN)


def _version_segments(version: str) -> tuple[int, int, int] | None:
    """Read a version the way the row's generated columns read theirs."""
    prefix = _VERSION_PREFIX.match(version)
    if prefix is None:
        return None
    segments = [int(segment) for segment in prefix.group().split(".")]
    major, minor, patch = (segments + [0, 0, 0])[:3]
    return major, minor, patch


class _VersionBoundConditions(StringEqualityConditions):
    """One end of the range a preset is valid in.

    The text column holds the version and the three generated columns hold its numeric
    segments, so the comparison runs on the segments while equality runs on the text.
    An absent bound leaves that end open.
    """

    _segments: tuple[FilterColumn, FilterColumn, FilterColumn]

    def __init__(
        self, column: FilterColumn, segments: tuple[FilterColumn, FilterColumn, FilterColumn]
    ) -> None:
        super().__init__(column)
        self._segments = segments

    def at_or_before(self, version: str) -> QueryCondition:
        return self._compare(version, inclusive=True)

    def after(self, version: str) -> QueryCondition:
        return self._compare(version, inclusive=False)

    def _compare(self, version: str, *, inclusive: bool) -> QueryCondition:
        target = _version_segments(version)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if target is None:
                return sa.false()
            major, minor, patch = target
            bound = sa.tuple_(*self._segments)
            asked = sa.tuple_(sa.literal(major), sa.literal(minor), sa.literal(patch))
            compared = bound <= asked if inclusive else bound > asked
            return sa.or_(self._column.is_(None), compared)

        return inner


class _VersionSegmentOrder(SearchOrder):
    """Orders by one version segment, putting the open end where the range opens."""

    _column: FilterColumn
    _open_end_first: bool

    def __init__(self, column: FilterColumn, *, open_end_first: bool) -> None:
        self._column = column
        self._open_end_first = open_end_first

    @override
    def apply(self, ascending: bool) -> QueryOrder:
        ordered = self._column.asc() if ascending else self._column.desc()
        if ascending == self._open_end_first:
            return ordered.nullsfirst()
        return ordered.nullslast()


class _RuntimeVariantPresetOwnFields(
    RowDataConverter[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """The preset's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches, and
    ``ui_option`` is JSON. ``ui_type`` is derived — it is read out of ``ui_option`` — so it
    carries no field and is built in :meth:`to_data`. The two version bounds order by their
    generated segment columns, so the text columns themselves carry no order.
    """

    id = SearchableField(
        RuntimeVariantPresetRow.id,
        UUIDConditions(RuntimeVariantPresetRow.id),
        ColumnOrder(RuntimeVariantPresetRow.id),
    )
    runtime_variant_id = SearchableField(
        RuntimeVariantPresetRow.runtime_variant,
        UUIDConditions(RuntimeVariantPresetRow.runtime_variant),
        ColumnOrder(RuntimeVariantPresetRow.runtime_variant),
    )
    name = SearchableField(
        RuntimeVariantPresetRow.name,
        StringConditions(RuntimeVariantPresetRow.name),
        ColumnOrder(RuntimeVariantPresetRow.name),
    )
    description = SearchableField(RuntimeVariantPresetRow.description, None, None)
    rank = SearchableField(
        RuntimeVariantPresetRow.rank,
        IntConditions(RuntimeVariantPresetRow.rank),
        ColumnOrder(RuntimeVariantPresetRow.rank),
    )
    preset_target = SearchableField(
        RuntimeVariantPresetRow.preset_target,
        EnumConditions(RuntimeVariantPresetRow.preset_target, PresetTarget),
        ColumnOrder(RuntimeVariantPresetRow.preset_target),
    )
    value_type = SearchableField(
        RuntimeVariantPresetRow.value_type,
        EnumConditions(RuntimeVariantPresetRow.value_type, PresetValueType),
        ColumnOrder(RuntimeVariantPresetRow.value_type),
    )
    default_value = SearchableField(
        RuntimeVariantPresetRow.default_value,
        StringConditions(RuntimeVariantPresetRow.default_value),
        ColumnOrder(RuntimeVariantPresetRow.default_value),
    )
    key = SearchableField(
        RuntimeVariantPresetRow.key,
        StringConditions(RuntimeVariantPresetRow.key),
        ColumnOrder(RuntimeVariantPresetRow.key),
    )
    required = SearchableField(
        RuntimeVariantPresetRow.required,
        BoolConditions(RuntimeVariantPresetRow.required),
        ColumnOrder(RuntimeVariantPresetRow.required),
    )
    added_version = SearchableField(
        RuntimeVariantPresetRow.added_version,
        _VersionBoundConditions(
            RuntimeVariantPresetRow.added_version,
            (
                RuntimeVariantPresetRow.added_version_major,
                RuntimeVariantPresetRow.added_version_minor,
                RuntimeVariantPresetRow.added_version_patch,
            ),
        ),
        None,
    )
    deprecated_version = SearchableField(
        RuntimeVariantPresetRow.deprecated_version,
        _VersionBoundConditions(
            RuntimeVariantPresetRow.deprecated_version,
            (
                RuntimeVariantPresetRow.deprecated_version_major,
                RuntimeVariantPresetRow.deprecated_version_minor,
                RuntimeVariantPresetRow.deprecated_version_patch,
            ),
        ),
        None,
    )
    added_version_major = SearchableField(
        RuntimeVariantPresetRow.added_version_major,
        IntConditions(RuntimeVariantPresetRow.added_version_major),
        _VersionSegmentOrder(RuntimeVariantPresetRow.added_version_major, open_end_first=True),
    )
    added_version_minor = SearchableField(
        RuntimeVariantPresetRow.added_version_minor,
        IntConditions(RuntimeVariantPresetRow.added_version_minor),
        _VersionSegmentOrder(RuntimeVariantPresetRow.added_version_minor, open_end_first=True),
    )
    added_version_patch = SearchableField(
        RuntimeVariantPresetRow.added_version_patch,
        IntConditions(RuntimeVariantPresetRow.added_version_patch),
        _VersionSegmentOrder(RuntimeVariantPresetRow.added_version_patch, open_end_first=True),
    )
    deprecated_version_major = SearchableField(
        RuntimeVariantPresetRow.deprecated_version_major,
        IntConditions(RuntimeVariantPresetRow.deprecated_version_major),
        _VersionSegmentOrder(
            RuntimeVariantPresetRow.deprecated_version_major, open_end_first=False
        ),
    )
    deprecated_version_minor = SearchableField(
        RuntimeVariantPresetRow.deprecated_version_minor,
        IntConditions(RuntimeVariantPresetRow.deprecated_version_minor),
        _VersionSegmentOrder(
            RuntimeVariantPresetRow.deprecated_version_minor, open_end_first=False
        ),
    )
    deprecated_version_patch = SearchableField(
        RuntimeVariantPresetRow.deprecated_version_patch,
        IntConditions(RuntimeVariantPresetRow.deprecated_version_patch),
        _VersionSegmentOrder(
            RuntimeVariantPresetRow.deprecated_version_patch, open_end_first=False
        ),
    )
    category = SearchableField(
        RuntimeVariantPresetRow.category,
        StringConditions(RuntimeVariantPresetRow.category),
        ColumnOrder(RuntimeVariantPresetRow.category),
    )
    display_name = SearchableField(
        RuntimeVariantPresetRow.display_name,
        StringConditions(RuntimeVariantPresetRow.display_name),
        ColumnOrder(RuntimeVariantPresetRow.display_name),
    )
    ui_option = SearchableField(RuntimeVariantPresetRow.ui_option, None, None)
    created_at = SearchableField(
        RuntimeVariantPresetRow.created_at,
        DateTimeConditions(RuntimeVariantPresetRow.created_at),
        ColumnOrder(RuntimeVariantPresetRow.created_at),
    )
    updated_at = SearchableField(
        RuntimeVariantPresetRow.updated_at,
        DateTimeConditions(RuntimeVariantPresetRow.updated_at),
        ColumnOrder(RuntimeVariantPresetRow.updated_at),
    )

    def added_version_order(self, ascending: bool) -> list[QueryOrder]:
        """The three segments of the lower bound, most significant first."""
        return [
            self.added_version_major.order.apply(ascending),
            self.added_version_minor.order.apply(ascending),
            self.added_version_patch.order.apply(ascending),
        ]

    def deprecated_version_order(self, ascending: bool) -> list[QueryOrder]:
        """The three segments of the upper bound, most significant first."""
        return [
            self.deprecated_version_major.order.apply(ascending),
            self.deprecated_version_minor.order.apply(ascending),
            self.deprecated_version_patch.order.apply(ascending),
        ]

    def valid_at_version(self, version: str) -> list[QueryCondition]:
        """The half-open range a preset is valid in: added <= version < deprecated."""
        return [
            self.added_version.filter.at_or_before(version),
            self.deprecated_version.filter.after(version),
        ]

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        ui_option = self._to_ui_option_data(self.ui_option.read(row))
        return RuntimeVariantPresetData(
            id=RuntimeVariantPresetID(self.id.read(row)),
            runtime_variant_id=RuntimeVariantID(self.runtime_variant_id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            rank=self.rank.read(row),
            preset_target=PresetTarget(self.preset_target.read(row)),
            value_type=PresetValueType(self.value_type.read(row)),
            default_value=self.default_value.read(row),
            key=self.key.read(row),
            required=self.required.read(row),
            added_version=self.added_version.read(row),
            deprecated_version=self.deprecated_version.read(row),
            category=self.category.read(row),
            ui_type=ui_option.ui_type if ui_option is not None else None,
            display_name=self.display_name.read(row),
            ui_option=ui_option,
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )

    def _to_ui_option_data(self, option: UIOption | None) -> UIOptionData | None:
        if option is None:
            return None
        return UIOptionData(
            ui_type=option.ui_type.value,
            slider=SliderOptionData(
                min=option.slider.min, max=option.slider.max, step=option.slider.step
            )
            if option.slider
            else None,
            number=NumberOptionData(min=option.number.min, max=option.number.max)
            if option.number
            else None,
            choices=ChoiceOptionData(
                items=[ChoiceItemData(value=c.value, label=c.label) for c in option.choices.items]
            )
            if option.choices
            else None,
            text=TextOptionData(placeholder=option.text.placeholder) if option.text else None,
        )


class RuntimeVariantPresetSearchableFields:
    own = _RuntimeVariantPresetOwnFields()
