import logging
import os
from datetime import datetime, timedelta

import aiohttp
from yarl import URL

from .. import BaseRunner

log = logging.getLogger()


class Runner(BaseRunner):
    """
    Implements an adaptor to Microsoft R Server API.
    """

    log_prefix = "r-server"

    def __init__(self, *args, endpoint=None, credentials=None, **kwargs):
        super().__init__(*args, **kwargs)
        if endpoint is None:
            endpoint = os.environ.get("MRS_ENDPOINT", "localhost")
        if credentials is None:
            credentials = {
                "username": os.environ.get("MRS_USERNAME", "anonymous"),
                "password": os.environ.get("MRS_PASSWORD", "unknown"),
            }
        self.http_sess = None
        self.endpoint = endpoint
        self.credentials = credentials
        self.access_token = None
        self.expires_on = None

    async def init_with_loop(self):
        self.http_sess = aiohttp.ClientSession()
        await self._refresh_token()
        sess_create_url = self.endpoint + "/sessions"
        resp = await self.http_sess.post(sess_create_url, headers=self.auth_hdrs, json={})
        data = await resp.json()
        self.sess_id = data["sessionId"]
        log.debug("created session:", self.sess_id)

    async def shutdown(self):
        await self._refresh_token()
        sess_url = f"{self.endpoint}/sessions/{self.sess_id}"
        resp = await self.http_sess.delete(sess_url, headers=self.auth_hdrs)
        resp.raise_for_status()
        log.debug("deleted session:", self.sess_id)
        revoke_url = URL(f"{self.endpoint}/login/refreshToken")
        revoke_url = revoke_url.update_query({
            "refreshToken": self.refresh_token,
        })
        resp = await self.http_sess.delete(revoke_url, headers=self.auth_hdrs)
        resp.raise_for_status()
        await self.http_sess.close()

    async def build_heuristic(self) -> int:
        raise NotImplementedError

    async def execute_heuristic(self) -> int:
        raise NotImplementedError

    async def query(self, code_text) -> int:
        await self._refresh_token()
        execute_url = f"{self.endpoint}/sessions/{self.sess_id}/execute"
        resp = await self.http_sess.post(
            execute_url,
            headers=self.auth_hdrs,
            json={
                "code": code_text,
            },
        )
        data = await resp.json()
        self.outsock.send_multipart(["stdout", data["consoleOutput"]])
        return 0

    async def complete(self, data):
        return []

    async def interrupt(self):
        # TODO: cancel session?
        pass

    async def _refresh_token(self):
        if self.access_token is None:
            login_url = self.endpoint + "/login"
            resp = await self.http_sess.post(login_url, json=self.credentials)
        elif self.expires_on is not None and self.expires_on <= datetime.now():
            refresh_url = f"{self.endpoint}/login/refreshToken"
            resp = await self.http_sess.post(
                refresh_url,
                headers=self.auth_hdrs,
                json={
                    "refreshToken": self.refresh_token,
                },
            )
        else:
            return
        data = await resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_on = datetime.now() + timedelta(seconds=int(data["expires_in"]))
        self.auth_hdrs = {
            "Authorization": f"Bearer {self.access_token}",
        }

    async def start_service(self, service_info):
        return None, {}
