from __future__ import annotations

import pytest

from ai.backend.appproxy.coordinator.models.subdomain import SubdomainGenerator
from ai.backend.common.types import Subdomain

LDH_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")


@pytest.fixture
def generator() -> SubdomainGenerator:
    return SubdomainGenerator()


class TestNormalization:
    """Behavior of name normalization, observed via ``generate_subdomain`` with
    an empty ``taken`` set so the normalized preferred value is returned as-is.
    """

    def test_dot_is_replaced_so_it_stays_a_single_label(
        self, generator: SubdomainGenerator
    ) -> None:
        assert generator.generate_subdomain(Subdomain("glm-5.2-fp8"), set()) == "glm-5-2-fp8"

    def test_uppercase_is_lowercased(self, generator: SubdomainGenerator) -> None:
        assert generator.generate_subdomain(Subdomain("GLM-52"), set()) == "glm-52"

    def test_disallowed_ascii_characters_become_hyphen(self, generator: SubdomainGenerator) -> None:
        assert generator.generate_subdomain(Subdomain("my_app!name"), set()) == "my-app-name"

    def test_leading_and_trailing_hyphens_are_stripped(self, generator: SubdomainGenerator) -> None:
        assert generator.generate_subdomain(Subdomain("--foo--"), set()) == "foo"

    def test_hyphen_runs_are_collapsed(self, generator: SubdomainGenerator) -> None:
        assert generator.generate_subdomain(Subdomain("a...b"), set()) == "a-b"

    def test_non_ascii_is_punycode_encoded(self, generator: SubdomainGenerator) -> None:
        result = generator.generate_subdomain(Subdomain("한글"), set())
        assert result.startswith("xn--")
        assert result.isascii()
        # The encoded portion round-trips back to the original label.
        assert result.removeprefix("xn--").encode("ascii").decode("punycode") == "한글"

    def test_mixed_ascii_and_non_ascii_stays_single_ascii_label(
        self, generator: SubdomainGenerator
    ) -> None:
        result = generator.generate_subdomain(Subdomain("glm-한글"), set())
        assert result.startswith("xn--")
        assert set(result) <= LDH_CHARS

    def test_result_contains_only_ldh_characters(self, generator: SubdomainGenerator) -> None:
        assert set(generator.generate_subdomain(Subdomain("Model Service @ v2.0!"), set())) <= (
            LDH_CHARS
        )

    def test_length_is_capped_at_63(self, generator: SubdomainGenerator) -> None:
        assert len(generator.generate_subdomain(Subdomain("a" * 100), set())) == 63


class TestFallback:
    def test_none_preferred_uses_generated_fallback(self, generator: SubdomainGenerator) -> None:
        result = generator.generate_subdomain(None, set())
        assert result.startswith("app-")
        assert set(result) <= LDH_CHARS

    def test_empty_preferred_uses_generated_fallback(self, generator: SubdomainGenerator) -> None:
        result = generator.generate_subdomain(Subdomain(""), set())
        assert result.startswith("app-")

    def test_unusable_preferred_uses_generated_fallback(
        self, generator: SubdomainGenerator
    ) -> None:
        result = generator.generate_subdomain(Subdomain("..."), set())
        assert result.startswith("app-")


class TestUniqueness:
    def test_returns_normalized_when_not_taken(self, generator: SubdomainGenerator) -> None:
        assert generator.generate_subdomain(Subdomain("glm-52"), set()) == "glm-52"

    def test_appends_suffix_when_taken(self, generator: SubdomainGenerator) -> None:
        result = generator.generate_subdomain(Subdomain("glm-52"), {Subdomain("glm-52")})
        assert result != "glm-52"
        assert result.startswith("glm-52-")
        assert set(result) <= LDH_CHARS

    def test_suffixed_form_fits_label_limit(self, generator: SubdomainGenerator) -> None:
        base = Subdomain("a" * 63)
        result = generator.generate_subdomain(base, {base})
        assert len(result) <= 63
        assert result != base
