from pydantic import BaseModel


class Capacity(BaseModel):
    total: int
    used: int
    free: int
