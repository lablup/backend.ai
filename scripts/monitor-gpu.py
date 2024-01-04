#! /usr/bin/env python3
import hashlib
import logging
import socket
import smtplib
import subprocess
import time
from email.mime.text import MIMEText
from pathlib import Path

NUM_GPU = 8  # expected number of GPUs
SMTP_HOST = "127.0.0.1"
SMTP_PORT = 25
SENDER_EMAIL = "admin@backend.ai"
NOTIFY_EMAILS = [
    # TODO: update
    "admin@example.com",
]
NOTIFY_INTERVAL = 6 * 3600  # in seconds

log = logging.getLogger("ai.backend.agent.monitor")


def check_lspci():
    proc = subprocess.run("lspci", capture_output=True)
    faulty_gpus = []
    gpu_count = 0
    for raw_line in proc.stdout.splitlines():
        line = raw_line.decode()
        if "3d controller" in line.lower() and "NVIDIA" in line:
            if "(rev ff)" in line or "(rev 00)" in line:
                pci_id, name = line.split(" ", maxsplit=1)
                faulty_gpus.append(pci_id)
            gpu_count += 1
    hostname = socket.gethostname()

    if gpu_count < NUM_GPU:
        subject = (
            f"WARNING: {NUM_GPU - gpu_count} GPU(s) have fallen off the bus! (host: {hostname})"
        )
        body = (
            f"Please check the node hardware status!\n\n"
            f"Hostname: {hostname}\n"
            f"The expected number of GPUs: {NUM_GPU}\n"
            f"The actual number of detected GPUs: {gpu_count}\n"
        )
        if check_interval("missing", subject + "\x00" + body):
            send_mail(
                SENDER_EMAIL,
                NOTIFY_EMAILS,
                "[Backend.AI] " + subject,
                body,
            )
    if faulty_gpus:
        subject = f"WARNING: detected {len(faulty_gpus)} faulty GPU(s) (host: {hostname})"
        body = (
            f"Please check the node hardware status!\n\n"
            f"Hostname: {hostname}\n"
            f"The list of faulty PCI device IDs:\n" + "\n".join(faulty_gpus)
        )
        if check_interval("faulty", subject + "\x00" + body):
            send_mail(
                SENDER_EMAIL,
                NOTIFY_EMAILS,
                "[Backend.AI] " + subject,
                body,
            )


def check_interval(event_name, msg):
    # Prevent flooding of notification emails due to repeated execution in crontab.
    # Send the email only when the message content changes or the configured interval passes.
    hasher = hashlib.sha1()
    hasher.update(msg.encode())
    digest = hasher.hexdigest()
    Path("/tmp/backend.ai/monitor").mkdir(parents=True, exist_ok=True)
    check_path = Path(f"/tmp/backend.ai/monitor/gpu-check.last-sent.{event_name}.{digest}")
    if not check_path.exists():
        log.info(f"notifying about {event_name} GPUs")
        check_path.touch()
        return True
    now = time.time()
    last_modified = check_path.stat().st_mtime
    if now - last_modified >= NOTIFY_INTERVAL:
        for old_check_path in Path("/tmp/backend.ai/monitor").glob(
            f"gpu-check.last-sent.{event_name}.*"
        ):
            old_check_path.unlink()
        check_path.touch()
        return True
    else:
        log.info(
            f"skipped notifying abaout {event_name} GPUs until the next notification interval comes"
        )
        return False


def send_mail(from_addr, to_addrs, subject, body):
    # To use SSL, replace smtplib.SMTP with smtplib.SMTP_SSL
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    # server.set_debuglevel(1)  # for diagnosis with smtp issues
    msg = MIMEText(body)
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    server.sendmail(from_addr, to_addrs, msg.as_string())
    server.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    check_lspci()


# vim: sts=4 sw=4 et
