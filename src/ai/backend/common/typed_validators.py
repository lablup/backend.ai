import datetime
import re
from typing import Annotated, Any, TypeAlias

from dateutil.relativedelta import relativedelta
from pydantic import (
    AfterValidator,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

TVariousDelta: TypeAlias = datetime.timedelta | relativedelta


class _TimeDurationPydanticAnnotation:
    allow_negative = False

    @classmethod
    def time_duration_validator(
        cls,
        value: int | float | str,
    ) -> TVariousDelta:
        assert isinstance(value, (int, float, str)), "value must be a number or string"
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        assert len(value) > 0, "value must not be empty"

        try:
            unit = value[-1]
            if unit.isdigit():
                t = float(value)
                assert cls.allow_negative or t >= 0, "value must be positive"
                return datetime.timedelta(seconds=t)
            elif value[-2:].isalpha():
                t = int(value[:-2])
                assert cls.allow_negative or t >= 0, "value must be positive"
                match value[-2:]:
                    case "yr":
                        return relativedelta(years=t)
                    case "mo":
                        return relativedelta(months=t)
                    case _:
                        raise AssertionError("value is not a known time duration")
            else:
                t = float(value[:-1])
                assert cls.allow_negative or t >= 0, "value must be positive"
                match value[-1]:
                    case "w":
                        return datetime.timedelta(weeks=t)
                    case "d":
                        return datetime.timedelta(days=t)
                    case "h":
                        return datetime.timedelta(hours=t)
                    case "m":
                        return datetime.timedelta(minutes=t)
                    case "s":
                        return datetime.timedelta(seconds=t)
                    case _:
                        raise AssertionError("value is not a known time duration")
        except ValueError:
            raise AssertionError(f"invalid numeric literal: {value[:-1]}")

    @classmethod
    def time_duration_serializer(cls, value: TVariousDelta) -> float | str:
        match value:
            case datetime.timedelta():
                return value.total_seconds()
            case relativedelta():
                # just like the deserializer, serializing relativedelta is only supported when year or month (not both) is supplied
                # years or months being normalized is not considered as a valid case since relativedelta does not allow fraction of years or months as an input
                assert not (
                    value.years and value.months
                ), "Serializing relativedelta with both years and months contained is not supported"
                assert (
                    value.years or value.months
                ), "Serialization is supported only for months or years field"
                if value.years:
                    return f"{value.years}yr"
                elif value.months:
                    return f"{value.months}mo"
                else:
                    raise AssertionError("Should not reach here")
            case _:
                raise AssertionError("Not a valid type")

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = core_schema.chain_schema([
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(),
            ]),
            core_schema.no_info_plain_validator_function(cls.time_duration_validator),
        ])

        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([
                # check if it's an instance first before doing any further work
                core_schema.union_schema([
                    core_schema.is_instance_schema(datetime.timedelta),
                    core_schema.is_instance_schema(relativedelta),
                ]),
                schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.time_duration_serializer
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(
            core_schema.union_schema([
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(),
            ])
        )


class _NaiveTimeDurationPydanticAnnotation(_TimeDurationPydanticAnnotation):
    allow_negative = True


TimeDuration = Annotated[
    TVariousDelta,
    _TimeDurationPydanticAnnotation,
]
"""Time duration validator accepting only non-negative value"""


NaiveTimeDuration = Annotated[TVariousDelta, _NaiveTimeDurationPydanticAnnotation]
"""Time duration validator which also accepts negative value"""


SESSION_NAME_MATCHER = re.compile(r"^(?=.{4,24}$)\w[\w.-]*\w$", re.ASCII)


def session_name_validator(s: str) -> str:
    if SESSION_NAME_MATCHER.search(s):
        return s
    else:
        raise AssertionError(f"String did not match {SESSION_NAME_MATCHER}")


SessionName = Annotated[str, AfterValidator(session_name_validator)]
"""Validator with extended re.ASCII option to match session name string literal"""
