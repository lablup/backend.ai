"""Default construction of the shared :class:`VictimSelector`."""

from __future__ import annotations

from collections import defaultdict

from ai.backend.common.types import PreemptionOrder
from ai.backend.sokovan_core.selectors.victims.fewest_sessions import (
    FewestSessionsVictimOrder,
)
from ai.backend.sokovan_core.selectors.victims.newest import (
    NewestVictimOrder,
)
from ai.backend.sokovan_core.selectors.victims.oldest import (
    OldestVictimOrder,
)
from ai.backend.sokovan_core.selectors.victims.order import (
    AbstractVictimOrder,
)
from ai.backend.sokovan_core.selectors.victims.selector import (
    VictimSelector,
)
from ai.backend.sokovan_core.selectors.victims.smallest_resources import (
    SmallestResourcesVictimOrder,
)


def create_victim_selector() -> VictimSelector:
    """Build the victim selector with the full order pool (unknown orders
    fall back to oldest — the scheduler must never break on enum drift)."""
    order_pool: dict[PreemptionOrder, AbstractVictimOrder] = defaultdict(OldestVictimOrder)
    order_pool[PreemptionOrder.OLDEST] = OldestVictimOrder()
    order_pool[PreemptionOrder.NEWEST] = NewestVictimOrder()
    order_pool[PreemptionOrder.FEWEST_SESSIONS] = FewestSessionsVictimOrder()
    order_pool[PreemptionOrder.SMALLEST_RESOURCES] = SmallestResourcesVictimOrder()
    return VictimSelector(order_pool)
