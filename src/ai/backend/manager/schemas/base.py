from pydantic import BaseModel, Extra


class BaseQuerySchema(BaseModel):
    class Config:
        from_attributes = True
        extra = Extra.forbid


class BaseCreationSchema(BaseModel):
    class Config:
        extra = Extra.forbid
