from ai.backend.manager.config.loader.config_overrider import ConfigOverrider


async def test_empty_overrides() -> None:
    overrider = ConfigOverrider([])
    cfg = await overrider.load()
    assert cfg == {}


async def test_single_level_key() -> None:
    overrider = ConfigOverrider([
        (("debug",), True),
    ])
    cfg = await overrider.load()
    assert cfg == {"debug": True}


async def test_nested_keys() -> None:
    overrider = ConfigOverrider([
        (("logging", "level"), "INFO"),
        (("logging", "pkg-ns", "aiohttp"), "DEBUG"),
    ])
    cfg = await overrider.load()
    assert cfg == {
        "logging": {
            "level": "INFO",
            "pkg-ns": {
                "aiohttp": "DEBUG",
            },
        },
    }
