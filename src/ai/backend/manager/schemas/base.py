from pydantic import BaseModel, Extra
from pydantic.main import ModelMetaclass


class BaseSchema(BaseModel):
    class Config:
        extra = Extra.forbid


class ToNullableFields(ModelMetaclass):
    def __new__(mcls, name, bases, namespaces, **kwargs):
        cls = super().__new__(mcls, name, bases, namespaces, **kwargs)
        for field in cls.__fields__.values():
            field.required = False
        return cls


class BaseQuerySchema(BaseModel):
    class Config:
        orm_mode = True
        allow_mutation = False
        extra = Extra.forbid
