from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class RuntimeVariantPresetOrderField(StrEnum):
    NAME = "name"
    RANK = "rank"
    CREATED_AT = "created_at"


class PresetTarget(StrEnum):
    ENV = "env"
    ARGS = "args"


class PresetValueType(StrEnum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


class UIType(StrEnum):
    SLIDER = "slider"
    NUMBER_INPUT = "number_input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    TEXT_INPUT = "text_input"


class SliderOption(BaseModel):
    min: float = Field(description="Minimum value.")
    max: float = Field(description="Maximum value.")
    step: float = Field(default=1, description="Increment step.")


class NumberOption(BaseModel):
    min: float | None = Field(default=None, description="Minimum value.")
    max: float | None = Field(default=None, description="Maximum value.")


class ChoiceItem(BaseModel):
    value: str = Field(description="Option value.")
    label: str = Field(description="Display label.")


class ChoiceOption(BaseModel):
    items: list[ChoiceItem] = Field(description="List of choices.")


class TextOption(BaseModel):
    placeholder: str | None = Field(default=None, description="Placeholder text.")


class UIOption(BaseModel):
    """UI rendering options. ui_type determines which option field is valid."""

    ui_type: UIType = Field(description="UI render type.")
    slider: SliderOption | None = Field(default=None, description="Slider config.")
    number: NumberOption | None = Field(default=None, description="Number input config.")
    choices: ChoiceOption | None = Field(default=None, description="Select/radio config.")
    text: TextOption | None = Field(default=None, description="Text input config.")

    @model_validator(mode="after")
    def validate_option_matches_type(self) -> Self:
        match self.ui_type:
            case UIType.SLIDER:
                if self.slider is None:
                    raise ValueError("slider is required for ui_type=slider.")
                if self.number or self.choices or self.text:
                    raise ValueError("Only slider is allowed for ui_type=slider.")
            case UIType.NUMBER_INPUT:
                if self.slider or self.choices or self.text:
                    raise ValueError("Only number is allowed for ui_type=number_input.")
            case UIType.SELECT:
                if self.choices is None:
                    raise ValueError("choices is required for ui_type=select.")
                if self.slider or self.number or self.text:
                    raise ValueError("Only choices is allowed for ui_type=select.")
            case UIType.CHECKBOX:
                if self.slider or self.number or self.choices or self.text:
                    raise ValueError("No option field is allowed for ui_type=checkbox.")
            case UIType.TEXT_INPUT:
                if self.slider or self.number or self.choices:
                    raise ValueError("Only text is allowed for ui_type=text_input.")
        return self
