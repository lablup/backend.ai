"""``backend.ai v2 login`` / ``logout`` CLI commands."""

from __future__ import annotations

import asyncio
import getpass
import json
import os
from typing import Any

import click

from ai.backend.client.auth import encrypt_payload
from ai.backend.client.cli.v2.insecure_http_guard import InsecureEndpointError
from ai.backend.client.owner_only_files import ensure_owner_only_file

from .helpers import ProfileStore, create_v2_registry, load_v2_config


@click.command()
@click.option(
    "--force", is_flag=True, default=False, help="Force login, invalidating existing sessions."
)
def login(force: bool) -> None:
    """Log in to a Backend.AI webserver endpoint.

    Stores the session cookie in ``session/cookie.dat`` of the selected profile.
    Requires ``endpoint-type`` to be ``session``.
    """

    async def _log_in_and_save_session() -> None:
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
            user_id = os.environ.get("BACKEND_USER") or input("User ID: ")
            password = os.environ.get("BACKEND_PASSWORD") or getpass.getpass("Password: ")

            client = registry._client
            login_url = client.build_url_raw("/server/login")
            payload: dict[str, str | bool] = {"username": user_id, "password": password}
            if force:
                payload["force"] = True

            async def _post_login_payload() -> dict[str, Any]:
                if config.endpoint.scheme == "https":
                    login_request = client.session.post(login_url, json=payload)
                else:
                    # The webserver derives the key from the request's scheme and Host header,
                    # so a path or trailing slash in the configured endpoint must not reach it.
                    encoded_body = encrypt_payload(
                        str(config.endpoint.origin()), json.dumps(payload).encode()
                    )
                    login_request = client.session.post(
                        login_url, data=encoded_body, headers={"X-BackendAI-Encoded": "true"}
                    )
                async with login_request as resp:
                    response_body: dict[str, Any] = await resp.json()
                    return response_body

            login_response = await _post_login_payload()

            def _get_details(resp_data: dict[str, Any]) -> str:
                raw = resp_data.get("data")
                if isinstance(raw, dict):
                    details = raw.get("details")
                    if details:
                        return str(details)
                elif raw:
                    return str(raw)
                # Handle RFC 7807 problem responses (e.g., {"type": ..., "title": ...})
                if "title" in resp_data:
                    return str(resp_data["title"])
                return "Unknown error"

            if not login_response.get("authenticated"):
                details = _get_details(login_response)

                if details == "OTP not provided":
                    otp = input("One-time Password: ")
                    payload["otp"] = otp.strip()
                    login_response = await _post_login_payload()

            if not login_response.get("authenticated"):
                details = _get_details(login_response)
                click.echo(click.style(f"Login failed: {details}", fg="red"))
                raise SystemExit(1)

            paths = ProfileStore().selected()
            cookie_jar = client.session.cookie_jar
            if hasattr(cookie_jar, "save"):
                ensure_owner_only_file(paths.cookie_file)
                cookie_jar.save(paths.cookie_file)

            login_config = login_response.get("config", {})
            if login_config:
                session_config_path = paths.session_dir / "config.json"
                ensure_owner_only_file(session_config_path)
                session_config_path.write_text(json.dumps(login_config))

            click.echo(click.style("Login succeeded.", fg="green"))
        finally:
            await registry.close()

    asyncio.run(_log_in_and_save_session())


def _remove_stored_session() -> None:
    paths = ProfileStore().selected()
    for path in [paths.cookie_file, paths.session_dir / "config.json"]:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


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

        try:
            registry = await create_v2_registry(config)
        except InsecureEndpointError as refusal:
            _remove_stored_session()
            click.echo(
                click.style(
                    f"Removed the stored session. The server session stays active: {refusal.message}",
                    fg="yellow",
                )
            )
            return

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

        _remove_stored_session()
        click.echo(click.style("Logged out.", fg="green"))

    asyncio.run(_run())
