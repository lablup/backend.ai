"""
Backfill model_definition in deployment_revisions for pre-26.4.2 endpoints.

Calls Service.modify() (no-op) for every endpoint so the server resolves
model_definition for revisions that still have NULL.

Usage:
  python scripts/backfill_model_definitions.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from ai.backend.client.func.service import Service
from ai.backend.client.output.fields import service_fields
from ai.backend.client.session import AsyncSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)


async def main(dry_run: bool = False) -> None:
    async with AsyncSession():
        page_size = 100
        page_offset = 0
        endpoint_ids: list[str] = []

        while True:
            result = await Service.paginated_list(
                fields=[service_fields["endpoint_id"]],
                page_size=page_size,
                page_offset=page_offset,
            )
            for item in result.items:
                endpoint_ids.append(item["endpoint_id"])
            if page_offset + page_size >= result.total_count:
                break
            page_offset += page_size

        total = len(endpoint_ids)
        log.info(f"Found {total} endpoint(s).")

        succeeded = 0
        failed = 0

        for i, eid in enumerate(endpoint_ids, 1):
            if dry_run:
                log.info(f"[dry-run] [{i}/{total}] {eid}")
                continue

            try:
                data = await Service(eid).modify()
                if data["ok"]:
                    log.info(f"[{i}/{total}] {eid} — ok")
                    succeeded += 1
                else:
                    log.warning(f"[{i}/{total}] {eid} — {data['msg']}")
                    failed += 1
            except Exception as e:
                log.warning(f"[{i}/{total}] {eid} — error: {e}")
                failed += 1

        log.info(f"Done. succeeded={succeeded}, failed={failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
