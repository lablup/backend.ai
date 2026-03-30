from pydantic import BaseModel


class DFEntry(BaseModel):
    total: int
    used: int
    available: int
    percent: int
