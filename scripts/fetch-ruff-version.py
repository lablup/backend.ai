# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
# ]
# ///
"""
Fetch Ruff release information and generate pants.toml known_versions entries.

Usage:
    uv run scripts/fetch-ruff-version.py 0.14.8
"""
from __future__ import annotations

import argparse
import sys

import httpx

# Mapping from Ruff release asset names to pants platform names
PLATFORM_MAPPING = {
    "aarch64-apple-darwin": "macos_arm64",
    "x86_64-apple-darwin": "macos_x86_64",
    "aarch64-unknown-linux-musl": "linux_arm64",
    "x86_64-unknown-linux-musl": "linux_x86_64",
}

BASE_URL = "https://github.com/astral-sh/ruff/releases/download"


def fetch_asset_info(version: str, ruff_platform: str) -> tuple[str, int]:
    """Fetch SHA256 checksum and file size for a specific asset."""
    tarball_url = f"{BASE_URL}/{version}/ruff-{ruff_platform}.tar.gz"
    checksum_url = f"{tarball_url}.sha256"

    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        # Fetch checksum
        checksum_response = client.get(checksum_url)
        checksum_response.raise_for_status()
        # The .sha256 file contains: "checksum  filename" or just "checksum"
        checksum_text = checksum_response.text.strip()
        sha256 = checksum_text.split()[0]

        # Fetch file size via HEAD request
        head_response = client.head(tarball_url)
        head_response.raise_for_status()
        size = int(head_response.headers["content-length"])

    return sha256, size


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Ruff release info and generate pants.toml known_versions entries"
    )
    parser.add_argument(
        "version",
        help="Ruff version number (e.g., 0.14.8)",
    )
    args = parser.parse_args()

    version = args.version

    print(f"Fetching release info for Ruff {version}...", file=sys.stderr)
    print(file=sys.stderr)

    entries: list[str] = []

    for ruff_platform, pants_platform in PLATFORM_MAPPING.items():
        try:
            sha256, size = fetch_asset_info(version, ruff_platform)
            entry = f'    "{version}|{pants_platform}|{sha256}|{size}",'
            entries.append(entry)
            print(f"  {pants_platform}: OK", file=sys.stderr)
        except httpx.HTTPStatusError as e:
            print(
                f"  {pants_platform}: FAILED ({e.response.status_code})",
                file=sys.stderr,
            )
            return 1
        except Exception as e:
            print(f"  {pants_platform}: ERROR ({e})", file=sys.stderr)
            return 1

    print(file=sys.stderr)
    print("Copy the following to pants.toml [ruff] section:", file=sys.stderr)
    print(file=sys.stderr)

    print("known_versions = [")
    for entry in entries:
        print(entry)
    print("]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
