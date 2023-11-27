import uuid
from abc import ABC, abstractmethod

import sqlalchemy as sa

import ai.backend.manager.models as models
from ai.backend.manager.api.context import RootContext


def get_random_string(length=10):
    return uuid.uuid4().hex[:length]


class ModelFactory(ABC):
    model = None
    app = None
    defaults = None

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def get_creation_defaults(self):
        return {}

    async def before_creation(self):
        pass

    async def after_creation(self, row):
        return row

    async def create(self, **kwargs):
        self.defaults = self.get_creation_defaults()
        self.defaults.update(**kwargs)
        await self.before_creation()
        root_ctx: RootContext = self.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            query = self.model.insert().returning(self.model).values(self.defaults)
            result = await conn.execute(query)
            row = result.first()
        row = dict(row.items())
        row = await self.after_creation(row)
        return row

    async def get(self, **kwargs):
        root_ctx: RootContext = self.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            filters = [sa.sql.column(key) == value for key, value in kwargs.items()]
            query = sa.select([self.model]).where(sa.and_(*filters))
            result = await conn.execute(query)
            rows = result.fetchall()
            assert len(rows) < 2, "Multiple items found"
            return rows[0] if len(rows) == 1 else None

    async def list(self, **kwargs):
        root_ctx: RootContext = self.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            filters = [sa.sql.column(key) == value for key, value in kwargs.items()]
            query = sa.select([self.model]).where(sa.and_(*filters))
            result = await conn.execute(query)
            return result.fetchall()


class KeyPairFactory(ModelFactory):
    model = models.keypairs

    def get_creation_defaults(self, **kwargs):
        from ai.backend.manager.models.keypair import generate_keypair

        ak, sk = generate_keypair()
        return {
            "access_key": ak,
            "secret_key": sk,
            "is_active": True,
            "is_admin": False,
            "resource_policy": "default",
        }

    async def before_creation(self):
        assert (
            "user_id" in self.defaults and "user" in self.defaults
        ), "user_id and user should be provided to create a keypair"


class UserFactory(ModelFactory):
    model = models.users

    def get_creation_defaults(self, **kwargs):
        username = f"test-user-{get_random_string()}"
        return {
            "username": username,
            "email": username + "@lablup.com",
            "password": get_random_string(),
            "domain_name": "default",
        }

    async def after_creation(self, row):
        kp = await KeyPairFactory(self.app).create(user_id=row["email"], user=row["uuid"])
        row["keypair"] = {
            "access_key": kp["access_key"],
            "secret_key": kp["secret_key"],
        }
        return row


class DomainFactory(ModelFactory):
    model = models.domains

    def get_creation_defaults(self, **kwargs):
        return {
            "name": f"test-domain-{get_random_string()}",
            "total_resource_slots": {},
        }


class GroupFactory(ModelFactory):
    model = models.groups

    def get_creation_defaults(self, **kwargs):
        return {
            "name": f"test-group-{get_random_string()}",
            "domain_name": "default",
            "total_resource_slots": {},
        }


class AssociationGroupsUsersFactory(ModelFactory):
    model = models.association_groups_users

    def get_creation_defaults(self, **kwargs):
        return {}

    async def before_creation(self):
        assert (
            "user_id" in self.defaults and "group_id" in self.defaults
        ), "user_id and group_id should be provided to associate a group and a user"


class VFolderFactory(ModelFactory):
    model = models.vfolders

    def get_creation_defaults(self, **kwargs):
        return {
            "host": "local",
            "name": f"test-vfolder-{get_random_string()}",
        }

    async def before_creation(self):
        if "user" not in self.defaults and "group" not in self.defaults:
            user = await UserFactory(self.app).create()
            self.defaults["user"] = user["uuid"]


class VFolderInvitationFactory(ModelFactory):
    model = models.vfolder_invitations

    def get_creation_defaults(self, **kwargs):
        return {
            "permission": models.VFolderPermission("ro"),
            "state": "pending",
        }

    async def before_creation(self):
        if "vfolder" not in self.defaults:
            vf = await VFolderFactory(self.app).create()
            self.defaults["vfolder"] = vf["id"]
        if "inviter" not in self.defaults:
            user = await UserFactory(self.app).create()
            self.defaults["inviter"] = user["email"]
        if "invitee" not in self.defaults:
            user = await UserFactory(self.app).create()
            self.defaults["invitee"] = user["email"]


class VFolderPermissionFactory(ModelFactory):
    model = models.vfolder_permissions

    def get_creation_defaults(self, **kwargs):
        return {
            "permission": models.VFolderPermission("ro"),
        }

    async def before_creation(self):
        if "vfolder" not in self.defaults:
            vf = await VFolderFactory(self.app).create()
            self.defaults["vfolder"] = vf["id"]
        if "user" not in self.defaults:
            user = await UserFactory(self.app).create()
            self.defaults["user"] = user["uuid"]
