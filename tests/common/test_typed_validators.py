import datetime

import pytest
from pydantic import BaseModel, ValidationError

from ai.backend.common import typed_validators as tv


def test_time_duration() -> None:
    class NormalModel(BaseModel):
        duration: tv.TimeDuration

    class GenerousModel(BaseModel):
        duration: tv.NaiveTimeDuration

    NormalModel.model_validate({"duration": "3s"})
    NormalModel.model_validate({"duration": "10"})
    NormalModel.model_validate({"duration": "20.5"})
    NormalModel.model_validate({"duration": 8})
    NormalModel.model_validate({"duration": 7.2})
    NormalModel.model_validate({"duration": "2d"})
    NormalModel.model_validate({"duration": "6yr"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "6y"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "6k"})
    with pytest.raises(ValidationError):
        NormalModel.model_validate({"duration": "-6y"})
    GenerousModel.model_validate({"duration": -12})
    GenerousModel.model_validate({"duration": 2})

    NormalModel(duration=datetime.timedelta(days=5)).model_dump_json()
