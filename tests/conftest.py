from pytest import Config, Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        dest="integration",
        default=False,
        help="Enable tests marked as integration",
    )


def pytest_configure(config: Config) -> None:
    # Disable the tests marked as "integration" by default,
    # unless the user gives the "--integration" CLI option.
    markerexpr = getattr(config.option, "markexpr", "")
    if not config.option.integration:
        if markerexpr:
            setattr(config.option, "markexpr", f"({markerexpr}) and not integration")
        else:
            setattr(config.option, "markexpr", "not integration")
