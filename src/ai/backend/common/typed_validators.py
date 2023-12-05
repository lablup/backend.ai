import datetime
from typing import Callable

from dateutil.relativedelta import relativedelta
from pydantic import AfterValidator, ValidationInfo


def TimeDuration(
    allow_negative=False,
) -> Callable[[int | float | str, ValidationInfo], datetime.timedelta]:
    def validator(value: int | float | str, info: ValidationInfo) -> datetime.timedelta:
        assert isinstance(value, (int, float, str)), "value must be a number or string"
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        assert len(value) > 0, "value must not be empty"

        try:
            unit = value[-1]
            if unit.isdigit():
                t = float(value)
                assert allow_negative or t >= 0, "value must be positive"
                return datetime.timedelta(seconds=t)
            elif value[-2:].isalpha():
                t = int(value[:-2])
                assert allow_negative or t >= 0, "value must be positive"
                match value[-2:]:
                    case "yr":
                        return relativedelta(years=t)
                    case "mo":
                        return relativedelta(months=t)
                    case _:
                        assert False, "value is not a known time duration"
            else:
                t = float(value[:-1])
                assert allow_negative or t >= 0, "value must be positive"
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
                        assert False, "value is not a known time duration"
        except ValueError:
            assert False, f"invalid numeric literal: {value[:-1]}"

    return AfterValidator(validator)
