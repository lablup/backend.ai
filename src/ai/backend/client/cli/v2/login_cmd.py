"""``backend.ai v2 login`` / ``logout`` CLI commands."""

from __future__ import annotations

import asyncio
import getpass
import json

import aiohttp
import click

from .helpers import COOKIE_FILE, SESSION_DIR, load_v2_config


@click.command()
def login() -> None:
    """Log in to a Backend.AI webserver endpoint.

    Stores the session cookie in ``~/.backend.ai/session/cookie.dat``.
    Requires ``endpoint-type`` to be ``session``.
    """
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

    user_id = input("User ID: ")
    password = getpass.getpass("Password: ")

    async def _run() -> None:
        connector = aiohttp.TCPConnector(ssl=not config.skip_ssl_verification)
        cookie_jar = aiohttp.CookieJar()
        async with aiohttp.ClientSession(connector=connector, cookie_jar=cookie_jar) as session:
            login_url = str(config.endpoint).rstrip("/") + "/server/login"
            payload = {"username": user_id, "password": password}
            async with session.post(login_url, json=payload) as resp:
                data = await resp.json()

            if not data.get("authenticated"):
                if data.get("data", {}).get("details") == "OTP not provided":
                    otp = input("One-time Password: ")
                    payload["otp"] = otp.strip()
                    async with session.post(login_url, json=payload) as resp:
                        data = await resp.json()

            if not data.get("authenticated"):
                details = data.get("data", {}).get("details", "Unknown error")
                click.echo(click.style(f"Login failed: {details}", fg="red"))
                raise SystemExit(1)

            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            cookie_jar.save(COOKIE_FILE)

            login_config = data.get("config", {})
            if login_config:
                config_path = SESSION_DIR / "config.json"
                config_path.write_text(json.dumps(login_config))

            click.echo(click.style("Login succeeded.", fg="green"))

    asyncio.run(_run())


@click.command()
def logout() -> None:
    """Log out and clear the stored session cookie."""
    config = load_v2_config()

    if config.endpoint_type != "session":
        click.echo(
            click.style(
                "Logout requires endpoint-type=session.",
                fg="yellow",
            )
        )
        raise SystemExit(1)

    async def _run() -> None:
        connector = aiohttp.TCPConnector(ssl=not config.skip_ssl_verification)
        cookie_jar = aiohttp.CookieJar()
        if COOKIE_FILE.exists():
            cookie_jar.load(COOKIE_FILE)
        async with aiohttp.ClientSession(connector=connector, cookie_jar=cookie_jar) as session:
            logout_url = str(config.endpoint).rstrip("/") + "/server/logout"
            try:
                async with session.post(logout_url) as resp:
                    await resp.read()
            except Exception:
                pass

        for path in [COOKIE_FILE, SESSION_DIR / "config.json"]:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

        click.echo(click.style("Logged out.", fg="green"))

    asyncio.run(_run())
