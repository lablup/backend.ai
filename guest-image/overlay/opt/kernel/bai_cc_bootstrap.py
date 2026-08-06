import io
import json
import os
import pathlib
import sys
import tarfile
import time
import urllib.error
import urllib.request

STATE = pathlib.Path("/run/backend.ai")
CONFIG = pathlib.Path("/home/config")


class Refusal(Exception):
    pass


def profile():
    if not (STATE / "ready").is_file():
        raise Refusal("the guest never established attested wall-clock time")
    return json.loads((STATE / "profile.json").read_text())


def fetch(api, resource):
    url = f"{api}/cdh/resource/{resource}"
    refusal = ""
    for attempt in range(12):
        if attempt:
            time.sleep(2)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace").strip()
            refusal = f"the broker refused {resource} with {error.code}: {detail}"
            continue
        except OSError as error:
            refusal = f"the broker at {api} was unreachable for {resource}: {error}"
            continue
        if payload:
            return payload
        refusal = f"the broker released {resource} as zero bytes"
    raise Refusal(refusal)


def unpack(payload, destination, mode):
    raw = destination.parent / f".{destination.name}.received"
    raw.write_bytes(payload)
    raw.chmod(mode)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:*") as bundle:
        bundle.extractall(destination, filter="data")
    raw.unlink()


def starve(reason):
    message = f"backend.ai confidential kernel refuses to start: {reason}"
    print(message, file=sys.stderr, flush=True)
    try:
        with open("/dev/console", "w") as console:
            print(message, file=console, flush=True)
    except OSError:
        pass
    while True:
        time.sleep(3600)


def tunnel():
    request = {
        "tunnel": os.environ.get("BACKENDAI_CC_TUNNEL_URI", ""),
        "peers": os.environ.get("BACKENDAI_CC_PEERS_URI", ""),
    }
    if not request["tunnel"]:
        return
    if not all(request.values()):
        raise Refusal("the session names a tunnel key with no peer directory to bring up against")
    shared = STATE / "session"
    (shared / "tunnel.json").write_text(json.dumps(request, sort_keys=True))
    state = shared / "tunnel-state.json"
    report = None
    for _ in range(120):
        if state.is_file():
            report = json.loads(state.read_text())
            if report["state"] != "retrying":
                break
        time.sleep(1)
    if report is None:
        raise Refusal("the guest never reported on the inter-kernel tunnel")
    if report["state"] != "up":
        raise Refusal(f"the inter-kernel tunnel did not come up: {report['reason']}")
    with open("/etc/hosts", "a") as hosts:
        hosts.write((shared / "hosts").read_text())


def main():
    api = profile()["api"]
    config_uri = os.environ.get("BACKENDAI_CC_CONFIG_URI")
    if not config_uri:
        raise Refusal("no session configuration resource was named for this kernel")
    CONFIG.mkdir(mode=0o755, parents=True, exist_ok=True)
    unpack(fetch(api, config_uri), CONFIG, 0o644)
    if not (CONFIG / "environ.txt").is_file():
        raise Refusal("the released session configuration carries no environ.txt")
    secrets_uri = os.environ.get("BACKENDAI_CC_SECRETS_URI")
    if secrets_uri:
        unpack(fetch(api, secrets_uri), CONFIG, 0o600)
    identity = STATE / "ssh" / "dropbear_rsa_host_key"
    if not identity.is_file():
        raise Refusal("the guest generated no in-guest secure shell host identity")
    (CONFIG / "ssh").mkdir(mode=0o700, exist_ok=True)
    delivered = CONFIG / "ssh" / "dropbear_rsa_host_key"
    delivered.write_bytes(identity.read_bytes())
    delivered.chmod(0o600)
    tunnel()


try:
    main()
except Refusal as refusal:
    starve(refusal)
