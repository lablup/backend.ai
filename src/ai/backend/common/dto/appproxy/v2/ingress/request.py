from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressKey


class IngressUpsertRequest(BaseRequestModel):
    ingresses: list[Ingress] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        keys = [ingress.key() for ingress in self.ingresses]
        if len(set(keys)) != len(keys):
            raise ValueError("An ingress appears more than once")
        return self


class IngressRemoveRequest(BaseRequestModel):
    keys: list[IngressKey] = Field(min_length=1)


class IngressReplaceRequest(BaseRequestModel):
    ingresses: list[Ingress] = Field(description="Every ingress to hold; empty clears all.")

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        keys = [ingress.key() for ingress in self.ingresses]
        if len(set(keys)) != len(keys):
            raise ValueError("An ingress appears more than once")
        return self
