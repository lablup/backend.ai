"""Pydantic models for RuntimeVariantPreset column types."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SliderOption(BaseModel):
    min: float
    max: float
    step: float = 1


class NumberOption(BaseModel):
    min: float | None = None
    max: float | None = None


class ChoiceItem(BaseModel):
    value: str
    label: str


class ChoiceOption(BaseModel):
    items: list[ChoiceItem]


class TextOption(BaseModel):
    placeholder: str | None = None


class UIOption(BaseModel):
    """UI rendering hints for a runtime variant preset parameter.

    Only one of the option fields should be set, matching the ui_type
    on the parent preset row. Fields for non-matching ui_types are ignored.
    """

    slider: SliderOption | None = Field(default=None, description="Slider UI config")
    number: NumberOption | None = Field(default=None, description="Number input UI config")
    choices: ChoiceOption | None = Field(default=None, description="Select/radio UI config")
    text: TextOption | None = Field(default=None, description="Text input UI config")
