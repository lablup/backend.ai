import logging

import pytest

from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import with_log_context_fields


def test_brace_style_adapter_positional_args(caplog: pytest.LogCaptureFixture) -> None:
    logger = BraceStyleAdapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {}!", "World")
        logger.info("Hello, {1} {0}!", "foo", "bar")

    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, World!"),
        ("root", logging.INFO, "Hello, bar foo!"),
    ]


def test_brace_style_adapter_custom_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    logger = BraceStyleAdapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {name}!", name="World")
    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, World!"),
    ]

    with pytest.raises(KeyError):
        # System-level context kwargs are hidden.
        with caplog.at_level(logging.INFO):
            logger.info("Hello, {stacklevel}!", stacklevel=0)


def test_brace_style_adapter_exceptions(caplog: pytest.LogCaptureFixture) -> None:
    logger = BraceStyleAdapter(logging.getLogger())
    with caplog.at_level(logging.ERROR):
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("Oops! {detail}", detail="big mistake")

    assert caplog.record_tuples == [("root", logging.ERROR, "Oops! big mistake")]
    assert "Traceback (most recent call last):" in caplog.text


def test_brace_style_adapter_context_fields_via_extra(caplog: pytest.LogCaptureFixture) -> None:
    logger = BraceStyleAdapter(logging.getLogger())
    with (
        with_log_context_fields({"user": "Alice"}),
        caplog.at_level(logging.INFO),
    ):
        logger.info("Hello, {extra[user]} {extra[email]}!", extra={"email": "alice@example.com"})

    assert caplog.record_tuples == [("root", logging.INFO, "Hello, Alice alice@example.com!")]


def test_brace_style_adapter_formatting(caplog: pytest.LogCaptureFixture) -> None:
    logger = BraceStyleAdapter(logging.getLogger())
    with caplog.at_level(logging.INFO):
        logger.info("Hello, {!r}!", "World")
        logger.info("Hello, {:.2f}!", 0.123)
        logger.info("Hello, {name!r}!", name="Earth")
        logger.info("Hello, {value:.2f}!", value=0.567)

    assert caplog.record_tuples == [
        ("root", logging.INFO, "Hello, 'World'!"),
        ("root", logging.INFO, "Hello, 0.12!"),
        ("root", logging.INFO, "Hello, 'Earth'!"),
        ("root", logging.INFO, "Hello, 0.57!"),
    ]
