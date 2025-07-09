from contextlib import asynccontextmanager as actxmgr
from decimal import Decimal
from typing import AsyncIterator, override

from ai.backend.client.utils import to_global_id
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    AutoScalingRuleContext,
    CreatedAutoScalingRuleIDContext,
    CreatedModelServiceEndpointMetaContext,
)
from ai.backend.test.templates.template import WrapperTestTemplate

_AUTO_SCALING_RULE_NODE_NAME = "endpoint_auto_scaling_rule_node"


class AutoScalingRuleTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "auto_scaling_rule"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        auto_scaling_rule_dep = AutoScalingRuleContext.current()
        client_session = ClientSessionContext.current()
        endpoint_meta = CreatedModelServiceEndpointMetaContext.current()

        try:
            result = await client_session.ServiceAutoScalingRule.create(
                service=endpoint_meta.service_id,
                metric_source=auto_scaling_rule_dep.metric_source,
                metric_name=auto_scaling_rule_dep.metric_name,
                threshold=Decimal(auto_scaling_rule_dep.threshold),
                comparator=auto_scaling_rule_dep.comparator,
                step_size=auto_scaling_rule_dep.step_size,
                cooldown_seconds=auto_scaling_rule_dep.cooldown_seconds,
                min_replicas=auto_scaling_rule_dep.min_replicas,
                max_replicas=auto_scaling_rule_dep.max_replicas,
            )
            with CreatedAutoScalingRuleIDContext.with_current(result.rule_id):
                yield
        finally:
            global_rule_id = to_global_id(_AUTO_SCALING_RULE_NODE_NAME, result.rule_id)
            await client_session.ServiceAutoScalingRule(global_rule_id).delete()
