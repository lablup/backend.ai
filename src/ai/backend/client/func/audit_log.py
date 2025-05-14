from ai.backend.common.dto.manager.response import ActionTypeVariant, AuditLogSchemaResponseModel

from ..session import api_session
from ..utils import dedent as _d
from .base import BaseFunction, api_function


class AuditLog(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches the information about
    available images.
    """

    @api_function
    @classmethod
    async def fetch_schema(cls) -> AuditLogSchemaResponseModel:
        """
        Fetches the audit log schema.
        """
        q = _d("""
                query {
                    audit_log_schema {
                        entity_type_variants
                        status_variants
                        action_type_variants {
                            entity_type
                            action_types
                        }
                    }
                }
            """)
        resp = await api_session.get().Admin._query(q)
        data = resp["audit_log_schema"]
        action_types = []
        for variant in data["action_type_variants"]:
            action_types.append(
                ActionTypeVariant(
                    entity_type=variant["entity_type"],
                    action_types=variant["action_types"],
                )
            )
        return AuditLogSchemaResponseModel(
            status_variants=data["status_variants"],
            entity_type_variants=data["entity_type_variants"],
            action_type_variants=action_types,
        )
