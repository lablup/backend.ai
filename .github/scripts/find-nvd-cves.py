#!/usr/bin/env python3
"""List the NVD CVEs about Backend.AI that were published or modified in a window.

    find-nvd-cves.py [--start <time>] [--end <time>]

<time> is an ISO date or datetime, read as UTC when it carries no offset. An empty
or omitted ``--end`` is now, and an empty or omitted ``--start`` is ``--end`` minus
``DEFAULT_WINDOW``.

Each keyword in ``KEYWORDS`` is searched separately and the hits are merged by CVE
id. Every CVE carries the GitHub Advisory Database entries for its id, read with
``gh api``; ``advisories`` is ``[]`` when GitHub has none.

Prints one JSON object: ``{"start": ..., "end": ..., "cves": [...]}``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
# The CNA writes the product as "BackendAI"; "Backend.AI" alone finds none of them.
KEYWORDS = ("Lablup", "BackendAI", "Backend.AI")
DEFAULT_WINDOW = datetime.timedelta(days=8)
# NVD rejects a lastMod range longer than 120 days.
MAX_RANGE = datetime.timedelta(days=120)
# Without an API key NVD allows 5 requests in a rolling 30 seconds.
REQUEST_INTERVAL = 6.5
RETRIES = 3


def parse_time(value: str, default: datetime.datetime) -> datetime.datetime:
    if not value:
        return default
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.UTC)
    return parsed.astimezone(datetime.UTC)


def nvd_time(value: datetime.datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class NvdClient:
    _last_request: float

    def __init__(self) -> None:
        self._last_request = 0.0

    def get(self, params: dict[str, str | int]) -> dict:
        url = f"{NVD_API}?{urllib.parse.urlencode(params)}"
        for attempt in range(RETRIES + 1):
            wait = self._last_request + REQUEST_INTERVAL - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as e:
                # 403 and 503 are how NVD reports rate limiting and overload.
                if e.code not in (403, 429, 503) or attempt == RETRIES:
                    raise
            except urllib.error.URLError:
                if attempt == RETRIES:
                    raise
            time.sleep(REQUEST_INTERVAL * (attempt + 1))
        raise AssertionError("unreachable")

    def search(self, keyword: str, start: datetime.datetime, end: datetime.datetime) -> list[dict]:
        found = []
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + MAX_RANGE, end)
            index = 0
            while True:
                page = self.get({
                    "keywordSearch": keyword,
                    "lastModStartDate": nvd_time(chunk_start),
                    "lastModEndDate": nvd_time(chunk_end),
                    "startIndex": index,
                })
                found.extend(item["cve"] for item in page["vulnerabilities"])
                index += page["resultsPerPage"]
                if page["resultsPerPage"] == 0 or index >= page["totalResults"]:
                    break
            chunk_start = chunk_end
        return found


def english_description(cve: dict) -> str:
    for description in cve.get("descriptions", []):
        if description["lang"] == "en":
            return description["value"]
    return ""


def cvss(cve: dict) -> dict | None:
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if not entries:
            continue
        primary = next((m for m in entries if m.get("type") == "Primary"), entries[0])
        data = primary["cvssData"]
        return {
            "version": data["version"],
            "score": data["baseScore"],
            "severity": data.get("baseSeverity") or primary.get("baseSeverity"),
        }
    return None


def advisories(cve_id: str) -> list[dict]:
    result = subprocess.run(
        ["gh", "api", "--method", "GET", "/advisories", "-f", f"cve_id={cve_id}"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [
        {
            "ghsa_id": advisory["ghsa_id"],
            "url": advisory["html_url"],
            "ranges": [
                {
                    "package": f"{v['package']['ecosystem']}:{v['package']['name']}",
                    "vulnerable": v["vulnerable_version_range"],
                    "first_patched": v["first_patched_version"],
                }
                for v in advisory["vulnerabilities"]
            ],
        }
        for advisory in json.loads(result.stdout)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--start", default="")
    parser.add_argument("--end", default="")
    args = parser.parse_args()

    end = parse_time(args.end, datetime.datetime.now(datetime.UTC))
    start = parse_time(args.start, end - DEFAULT_WINDOW)
    if start >= end:
        sys.stderr.write(f"--start {start.isoformat()} is not before --end {end.isoformat()}.\n")
        return 2

    nvd = NvdClient()
    cves: dict[str, dict] = {}
    for keyword in KEYWORDS:
        for cve in nvd.search(keyword, start, end):
            cves.setdefault(cve["id"], cve)

    sys.stdout.write(
        json.dumps(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "cves": [
                    {
                        "id": cve_id,
                        "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                        "published": cve["published"],
                        "last_modified": cve["lastModified"],
                        "status": cve.get("vulnStatus"),
                        "cvss": cvss(cve),
                        "description": english_description(cve),
                        "advisories": advisories(cve_id),
                    }
                    for cve_id, cve in sorted(cves.items())
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
