import uuid
from dataclasses import dataclass


@dataclass
class TestSpecMeta:
    test_id: uuid.UUID
    spec_name: str
