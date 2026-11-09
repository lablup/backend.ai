from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from pytest_aiohttp.plugin import AiohttpClient

from ai.backend.web.config.unified import WebServerUnifiedConfig
from ai.backend.web.server import console_handler, static_handler


class TestStaticExposure:
    @pytest.fixture
    def static_path(self, tmp_path: Path) -> Path:
        (tmp_path / "assets").mkdir()
        for name in ("app.js", "app.css", "app.js.map", "app.css.map"):
            (tmp_path / "assets" / name).write_text("asset content")
        (tmp_path / "stats").write_text("diagnostic data")
        (tmp_path / "config.ini").write_text("legacy configuration")
        return tmp_path

    @pytest.fixture(params=["static", "webui"])
    def mode(self, request: pytest.FixtureRequest) -> str:
        return str(request.param)

    @pytest.fixture
    async def client(
        self,
        mode: str,
        static_path: Path,
        aiohttp_client: AiohttpClient,
    ) -> TestClient[web.Request, web.Application]:
        config = WebServerUnifiedConfig.model_validate({
            "session": {"redis": {"password": "test-password"}}
        })
        config.service.static_path = static_path
        app = web.Application()
        app["config"] = config
        app["webui_index_template"] = "<html>WebUI</html>"
        handler = static_handler if mode == "static" else console_handler
        app.router.add_get("/{path:.*}", handler)
        return await aiohttp_client(app)

    @pytest.mark.parametrize(
        "path",
        [
            "/stats",
            "/stats?format=json",
            "/config.ini",
            "/config%2Eini",
            "/assets/app.js.map",
            "/assets/app.css.map",
            "/assets/app.js%2Emap",
        ],
    )
    async def test_rejects_existing_blocked_files(
        self, client: TestClient[web.Request, web.Application], path: str
    ) -> None:
        response = await client.get(path)
        assert response.status == 404

    @pytest.mark.parametrize(
        "path", ["/stats", "/config.ini", "/assets/app.js.map", "/assets/app.css.map"]
    )
    async def test_rejects_missing_blocked_files(
        self, client: TestClient[web.Request, web.Application], static_path: Path, path: str
    ) -> None:
        (static_path / path.lstrip("/")).unlink()
        response = await client.get(path)
        assert response.status == 404

    @pytest.mark.parametrize("path", ["/assets/app.js", "/assets/app.css"])
    async def test_serves_regular_assets(
        self, client: TestClient[web.Request, web.Application], path: str
    ) -> None:
        response = await client.get(path)
        assert response.status == 200
        assert await response.text() == "asset content"

    @pytest.mark.parametrize("mode", ["webui"], indirect=True)
    async def test_webui_navigation_returns_spa(
        self, client: TestClient[web.Request, web.Application]
    ) -> None:
        response = await client.get("/sessions")
        assert response.status == 200
        assert await response.text() == "<html>WebUI</html>"

    @pytest.mark.parametrize("mode", ["static"], indirect=True)
    async def test_static_navigation_returns_not_found(
        self, client: TestClient[web.Request, web.Application]
    ) -> None:
        response = await client.get("/sessions")
        assert response.status == 404
