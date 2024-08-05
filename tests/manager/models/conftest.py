# conftest.py
from uuid import UUID

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries


@pytest.fixture(scope="module", autouse=True)
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


@pytest.fixture(scope="module")
def base_context():  # noqa: F811
    def _base_context(**overrides):
        """
        default_params is used to bypass the decorators.
        """
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
        # if "user" in overrides:
        #     default_params["user"] = update_dict_fields(default_params["user"], overrides["user"])
        #     del overrides["user"]
        updated_params = deep_update(default_params, overrides)
        # default_params.update(overrides)
        return GraphQueryContext(**updated_params)

    return _base_context


def deep_update(original: dict, updates: dict) -> dict:
    """
    Recursively updates the original dictionary with values from the updates dictionary.

    :param original: The original dictionary to update.
    :param updates: The dictionary containing updates.
    :return: The updated dictionary.
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in original and isinstance(original[key], dict):
            original[key] = deep_update(original[key], value)
        else:
            original[key] = value
    return original
