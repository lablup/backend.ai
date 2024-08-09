# conftest.py
from uuid import UUID

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.common.utils import update_nested_dict

@pytest.fixture(scope="module", autouse=True)
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


@pytest.fixture(scope="function")
def get_base_context():  # noqa: F811
    def _get_base_context(**overrides):
        default_params = {
            "schema": None,
            "dataloader_manager": None,
            "local_config": None,
            "shared_config": None,
            "etcd": None,
            "user": {
                "role": "user",
                "email": "example@lablup.com",
                "uuid": UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                "domain_name": "default",
            },
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "db": None,
            "redis_stat": None,
            "redis_image": None,
            "redis_live": None,
            "manager_status": None,
            "known_slot_types": None,
            "background_task_manager": None,
            "storage_manager": None,
            "registry": None,
            "idle_checker_host": None,
        }
        update_nested_dict(default_params, overrides)
        return GraphQueryContext(**default_params)

    return _get_base_context
