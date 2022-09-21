import datetime
import json
import uuid


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)
