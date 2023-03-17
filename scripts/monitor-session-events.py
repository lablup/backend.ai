#! /usr/bin/env python3
import asyncio
import json
import logging
import os
import re
import smtplib
import subprocess
import weakref
from email.mime.text import MIMEText

_send_mail_tasks = weakref.WeakSet()
_rx_term_escapes = re.compile(r"(\x9b|\x1b\[)[0-?]*[ -\/]*[@-~]")

log = logging.getLogger("ai.backend.manager.monitor")

SMTP_HOST = "127.0.0.1"
SMTP_PORT = 25
SENDER_EMAIL = "admin@backend.ai"


async def monitor_events():
    # This script assumes that .env is already configured as a super-admin account with API-mode access.
    args = [
        "backend.ai",
        "session",
        "events",
        "*",  # monitor all session events
    ]
    try:
        while True:
            log.info("(re)starting 'session events' command")
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={**os.environb, b"PYTHONUNBUFFERED": b"1"},
            )
            try:
                while True:
                    line = await proc.stdout.readline()
                    if not line:  # terminated
                        break
                    event_raw_name, event_raw_data = line.split(b" ", maxsplit=1)
                    event_name = _rx_term_escapes.sub("", event_raw_name.decode())
                    try:
                        event_data = json.loads(event_raw_data)
                        task = asyncio.create_task(send_notice(event_name, event_data))
                        _send_mail_tasks.add(task)
                    except Exception:
                        log.exception("ooops")
            finally:
                await proc.wait()
    finally:
        # cancel any ongoing send_email() task
        remaining_tasks = {*_send_mail_tasks}
        cancelled_tasks = []
        for task in remaining_tasks:
            if not task.done() and not task.cancelled():
                task.cancel()
                cancelled_tasks.append(task)
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)


async def send_notice(event_name, event_data):
    # reference for event_name: https://github.com/lablup/backend.ai/blob/f5bb6c1/src/ai/backend/common/events.py
    # reference for event_data: https://github.com/lablup/backend.ai/blob/f5bb6c1/src/ai/backend/manager/api/events.py#L149-L155
    session_name = event_data["sessionName"]
    session_id = event_data["sessionId"]
    match event_name:
        case "session_terminated" | "session_success" | "session_failure":
            user_email = await extract_user_email(event_data["ownerAccessKey"])
            reason = event_data["reason"]
            exit_code = event_data["exitCode"]
            if user_email is None:
                log.info(
                    f"{event_name} for {session_name} -> skipped due to the missing user email"
                )
                return
            else:
                log.info(f"{event_name} for {session_name} -> notifying to {user_email}")
            await send_mail(
                SENDER_EMAIL,
                [user_email],
                f"[Backend.AI] {event_name} in your session {session_name}",
                (
                    f"This is a notification for a lifecycle event of your session.\n\n"
                    f"Session ID: {session_id}\n"
                    f"Session Name: {session_name}\n"
                    f"Reason: {reason}\n"
                    f"Exit Code: {exit_code}\n"
                ),
            )
        case _:
            log.debug(f"{event_name} for {session_name} -> skipped")


async def extract_user_email(access_key):
    args = [
        "backend.ai",
        "--output",
        "json",
        "admin",
        "keypair",
        "list",
        "--filter",
        f'access_key == "{access_key}"',
    ]
    proc = await asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE)
    data = json.loads(await proc.stdout.read())
    try:
        return data["items"][0]["user_id"]
    except (IndexError, KeyError):
        return None


async def send_mail(from_addr, to_addrs, subject, body):
    def _send_mail(from_addr, to_addrs, subject, body):
        # To use SSL, replace smtplib.SMTP with smtplib.SMTP_SSL
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        # server.set_debuglevel(1)  # for diagnosis with smtp issues
        msg = MIMEText(body)
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _send_mail, from_addr, to_addrs, subject, body)


async def main():
    try:
        log.info("starting monitoring of session events...")
        await monitor_events()
    finally:
        await asyncio.sleep(0)
        log.info("terminated")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass


# vim: sts=4 sw=4 et
