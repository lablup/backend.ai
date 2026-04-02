"""``backend.ai v2 login`` / ``logout`` CLI commands."""

from __future__ import annotations

import asyncio
import getpass
import json
import os

import click

from .helpers import COOKIE_FILE, SESSION_DIR, create_v2_registry, load_v2_config


@click.command()
@click.option(
    "--force", is_flag=True, default=False, help="Force login, invalidating existing sessions."
)
def login(force: bool) -> None:
    """Log in to a Backend.AI webserver endpoint.

    Stores the session cookie in ``~/.backend.ai/session/cookie.dat``.
    Requires ``endpoint-type`` to be ``session``.
    """
    user_id = os.environ.get("BACKEND_USER") or input("User ID: ")
    password = os.environ.get("BACKEND_PASSWORD") or getpass.getpass("Password: ")

    async def _run() -> None:
        config = load_v2_config()

        if config.endpoint_type != "session":
            click.echo(
                click.style(
                    "Login requires endpoint-type=session. "
                    "Run: backend.ai v2 config set endpoint-type session",
                    fg="yellow",
                )
            )
            raise SystemExit(1)

        registry = await create_v2_registry(config)
        try:
            client = registry._client
            login_url = client.build_url_raw("/server/login")
            payload: dict[str, str | bool] = {"username": user_id, "password": password}
            if force:
                payload["force"] = True
            async with client.session.post(login_url, json=payload) as resp:
                data = await resp.json()

            if not data.get("authenticated"):
                if data.get("data", {}).get("details") == "OTP not provided":
                    otp = input("One-time Password: ")
                    payload["otp"] = otp.strip()
                    async with client.session.post(login_url, json=payload) as resp:
                        data = await resp.json()

            if not data.get("authenticated"):
                details = data.get("data", {}).get("details", "Unknown error")
                click.echo(click.style(f"Login failed: {details}", fg="red"))
                raise SystemExit(1)

            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            cookie_jar = client.session.cookie_jar
            if hasattr(cookie_jar, "save"):
                cookie_jar.save(COOKIE_FILE)

            login_config = data.get("config", {})
            if login_config:
                config_path = SESSION_DIR / "config.json"
                config_path.write_text(json.dumps(login_config))

            click.echo(click.style("Login succeeded.", fg="green"))
        finally:
            await registry.close()

    asyncio.run(_run())


@click.command()
def logout() -> None:
    """Log out and clear the stored session cookie."""

    async def _run() -> None:
        config = load_v2_config()

        if config.endpoint_type != "session":
            click.echo(
                click.style(
                    "Logout requires endpoint-type=session.",
                    fg="yellow",
                )
            )
            raise SystemExit(1)

        registry = await create_v2_registry(config)
        try:
            client = registry._client
            logout_url = client.build_url_raw("/server/logout")
            try:
                async with client.session.post(logout_url) as resp:
                    await resp.read()
            except Exception:
                pass
        finally:
            await registry.close()

        for path in [COOKIE_FILE, SESSION_DIR / "config.json"]:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

        click.echo(click.style("Logged out.", fg="green"))

    asyncio.run(_run())
