import datetime
import json
import uuid

from ai.backend.common.json import ExtendedJSONEncoder


def test_encode():
    ret = json.dumps(
        {'x': uuid.UUID('78bd79c7-214b-4ec6-9a22-3461785bced6')},
        cls=ExtendedJSONEncoder,
    )
    assert '"78bd79c7-214b-4ec6-9a22-3461785bced6"' in ret
    ret = json.dumps(
        {'x': datetime.datetime(year=2000, month=1, day=1, hour=11, minute=30, second=22,
                                tzinfo=datetime.timezone.utc)},
        cls=ExtendedJSONEncoder,
    )
    assert '2000-01-01T11:30:22+00:00' in ret
