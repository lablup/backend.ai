from typing import List, Mapping, Optional

from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("Dotfile",)


class Dotfile(BaseFunction):
    @api_function
    @classmethod
    async def create(
        cls,
        data: str,
        path: str,
        permission: str,
        owner_access_key: str = None,
        domain: str = None,
        project: Optional[str] = None,
    ) -> "Dotfile":
        body = {
            "data": data,
            "path": path,
            "permission": permission,
        }
        if project:
            body["project"] = project
            if domain:
                body["domain"] = domain
            rqst_endpoint = "/project-config/dotfiles"
        elif domain:
            body["domain"] = domain
            rqst_endpoint = "/domain-config/dotfiles"
        else:
            if owner_access_key:
                body["owner_access_key"] = owner_access_key
            rqst_endpoint = "/user-config/dotfiles"

        rqst = Request("POST", rqst_endpoint)
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            await resp.json()
        return cls(path, owner_access_key=owner_access_key, project=project, domain=domain)

    @api_function
    @classmethod
    async def list_dotfiles(
        cls,
        owner_access_key: str = None,
        domain: str = None,
        project: Optional[str] = None,
    ) -> "List[Mapping[str, str]]":
        params = {}
        if project:
            params["project"] = project
            if domain:
                params["domain"] = domain
            rqst_endpoint = "/project-config/dotfiles"
        elif domain:
            params["domain"] = domain
            rqst_endpoint = "/domain-config/dotfiles"
        else:
            if owner_access_key:
                params["onwer_access_key"] = owner_access_key
            rqst_endpoint = "/user-config/dotfiles"

        rqst = Request("GET", rqst_endpoint, params=params)
        async with rqst.fetch() as resp:
            return await resp.json()

    def __init__(
        self,
        path: str,
        owner_access_key: Optional[str] = None,
        project: Optional[str] = None,
        domain: str = None,
    ):
        self.path = path
        self.owner_access_key = owner_access_key
        self.project = project
        self.domain = domain

    @api_function
    async def get(self) -> str:
        params = {"path": self.path}
        if self.project:
            params["project"] = self.project
            if self.domain:
                params["domain"] = self.domain
            rqst_endpoint = "/project-config/dotfiles"
        elif self.domain:
            params["domain"] = self.domain
            rqst_endpoint = "/domain-config/dotfiles"
        else:
            if self.owner_access_key:
                params["owner_access_key"] = self.owner_access_key
            rqst_endpoint = "/user-config/dotfiles"

        rqst = Request("GET", rqst_endpoint, params=params)
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def update(self, data: str, permission: str):
        body = {
            "data": data,
            "path": self.path,
            "permission": permission,
        }
        if self.project:
            body["project"] = self.project
            if self.domain:
                body["domain"] = self.domain
            rqst_endpoint = "/project-config/dotfiles"
        elif self.domain:
            body["domain"] = self.domain
            rqst_endpoint = "/domain-config/dotfiles"
        else:
            if self.owner_access_key:
                body["owner_access_key"] = self.owner_access_key
            rqst_endpoint = "/user-config/dotfiles"

        rqst = Request("PATCH", rqst_endpoint)
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        params = {"path": self.path}
        if self.project:
            params["project"] = self.project
            if self.domain:
                params["domain"] = self.domain
            rqst_endpoint = "/project-config/dotfiles"
        elif self.domain:
            params["domain"] = self.domain
            rqst_endpoint = "/domain-config/dotfiles"
        else:
            if self.owner_access_key:
                params["owner_access_key"] = self.owner_access_key
            rqst_endpoint = "/user-config/dotfiles"

        rqst = Request("DELETE", rqst_endpoint, params=params)
        async with rqst.fetch() as resp:
            return await resp.json()
