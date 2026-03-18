"""Tests for domain GraphQL DataLoader utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.domain.loader import load_domains_by_names
from ai.backend.manager.data.domain.types import DomainData


class TestLoadDomainsByNames:
    """Tests for load_domains_by_names function."""

    @staticmethod
    def create_mock_domain(domain_name: str) -> MagicMock:
        mock = MagicMock(spec=DomainData)
        mock.name = domain_name
        return mock

    @staticmethod
    def create_mock_processor(domains: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.items = domains
        mock_processor.search_domains.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_names_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_domains_by_names(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_domains.wait_for_complete.assert_not_called()

    async def test_returns_domains_in_request_order(self) -> None:
        # Given
        name1, name2, name3 = "domain-a", "domain-b", "domain-c"
        domain1 = self.create_mock_domain(name1)
        domain2 = self.create_mock_domain(name2)
        domain3 = self.create_mock_domain(name3)
        mock_processor = self.create_mock_processor(
            [domain3, domain1, domain2]  # DB returns in different order
        )

        # When
        result = await load_domains_by_names(mock_processor, [name1, name2, name3])

        # Then
        assert result == [domain1, domain2, domain3]

    async def test_returns_none_for_missing_names(self) -> None:
        # Given
        existing_name = "existing-domain"
        missing_name = "missing-domain"
        existing_domain = self.create_mock_domain(existing_name)
        mock_processor = self.create_mock_processor([existing_domain])

        # When
        result = await load_domains_by_names(mock_processor, [existing_name, missing_name])

        # Then
        assert result == [existing_domain, None]
