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
        default_params.update(overrides)
        return GraphQueryContext(**default_params)

    return _base_context


@pytest.fixture(scope="module")
def deprecated_query():
    query = """
    query {
        images {
            tag
            name
            registry
            architecture
            digest
            installed
                labels{
                    key
                    value
                }
                resource_limits{
                    key
                    min
                    max
                }
        }
    }
    """
    variables = {"is_operation": True}
    return query, variables


@pytest.fixture(scope="module")
def non_deprecated_query():
    query = """
        query($limit:Int!, $offset:Int!, $ak:String, $group_id:String, $status:String) {
            compute_session_list(limit:$limit, offset:$offset, access_key:$ak, group_id:$group_id, status:$status) {
                total_count
            }
        }
    """
    variables = {"limit": 1, "offset": 0, "status": "RUNNING"}
    return query, variables
