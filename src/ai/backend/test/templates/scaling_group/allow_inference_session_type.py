from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.scaling_group import ScalingGroupContext, ScalingGroupNameContext
from ai.backend.test.templates.template import WrapperTestTemplate


class AllowInferenceSessionTypeTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "allow_inference_session_type"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        scaling_group_cfg = ScalingGroupContext.current()
        allowed_session_types = {"allowed_session_types": ["interactive", "inference", "batch"]}
        await client_session.ScalingGroup.update(
            name=scaling_group_cfg.name, scheduler_opts=allowed_session_types
        )
        with ScalingGroupNameContext.with_current(scaling_group_cfg.name):  # type: ignore
            yield
        # NOTE: Do we have to reset the allowed session types?
