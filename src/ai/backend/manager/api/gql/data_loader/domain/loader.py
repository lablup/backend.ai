from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.domain.options import DomainConditions
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction
from ai.backend.manager.services.domain.processors import DomainProcessors


async def load_domains_by_names(
    processor: DomainProcessors,
    domain_names: Sequence[str],
) -> list[DomainData | None]:
    """Batch load domains by their names.

    Args:
        processor: The domain processor.
        domain_names: Sequence of domain names to load.

    Returns:
        List of DomainData (or None if not found) in the same order as domain_names.
    """
    if not domain_names:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[DomainConditions.by_names(domain_names)],
    )

    action_result = await processor.search_domains.wait_for_complete(
        SearchDomainsAction(querier=querier)
    )

    domain_map = {domain.name: domain for domain in action_result.items}
    return [domain_map.get(name) for name in domain_names]
