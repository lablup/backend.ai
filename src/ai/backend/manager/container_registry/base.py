from __future__ import annotations

import asyncio
import logging
import json
from contextvars import ContextVar
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Mapping,
    Optional,
    cast,
)

import aiohttp
import aiotools
import sqlalchemy as sa
import yarl

from abc import ABCMeta, abstractmethod

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.docker import (
    ImageRef,
    MIN_KERNELSPEC, MAX_KERNELSPEC,
    arch_name_aliases,
    login as registry_login,
)
from ai.backend.common.logging import BraceStyleAdapter

from ai.backend.manager.models.image import ImageRow, ImageType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__name__))


class BaseContainerRegistry(metaclass=ABCMeta):

    db: ExtendedAsyncSAEngine
    registry_name: str
    registry_info: Mapping[str, Any]
    registry_url: yarl.URL
    max_concurrency_per_registry: int
    base_hdrs: Dict[str, str]
    credentials: Dict[str, str]
    ssl_verify: bool

    sema: ContextVar[asyncio.Semaphore]
    reporter: ContextVar[Optional[ProgressReporter]]
    all_updates: ContextVar[Dict[ImageRef, Dict[str, Any]]]

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry_name: str,
        registry_info: Mapping[str, Any],
        *,
        max_concurrency_per_registry: int = 4,
        ssl_verify: bool = True,
    ) -> None:
        self.db = db
        self.registry_name = registry_name
        self.registry_info = registry_info
        self.registry_url = registry_info['']
        self.max_concurrency_per_registry = max_concurrency_per_registry
        self.base_hdrs = {
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
        }
        self.credentials = {}
        self.ssl_verify = ssl_verify
        self.sema = ContextVar('sema')
        self.reporter = ContextVar('reporter', default=None)
        self.all_updates = ContextVar('all_updates')

    async def rescan_single_registry(
        self,
        reporter: ProgressReporter = None,
    ) -> None:
        self.all_updates.set({})
        self.sema.set(asyncio.Semaphore(self.max_concurrency_per_registry))
        self.reporter.set(reporter)
        username = self.registry_info['username']
        if username is not None:
            self.credentials['username'] = username
        password = self.registry_info['password']
        if password is not None:
            self.credentials['password'] = password
        non_kernel_words = (
            'common-', 'commons-', 'base-',
            'krunner', 'builder',
            'backendai', 'geofront',
        )
        ssl_ctx = None  # default
        if not self.registry_info['ssl-verify']:
            ssl_ctx = False
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as sess:
            async with aiotools.TaskGroup() as tg:
                async for image in self.fetch_repositories(sess):
                    if not any((w in image) for w in non_kernel_words):  # skip non-kernel images
                        tg.create_task(self._scan_image(sess, image))

        all_updates = self.all_updates.get()
        if not all_updates:
            log.info('No images found in registry {0}', self.registry_url)
        else:
            image_identifiers = [
                (k.canonical, k.architecture) for k in all_updates.keys()
            ]
            async with self.db.begin_session() as session:
                existing_images = await session.scalars(
                    sa.select(ImageRow)
                    .where(
                        sa.func.ROW(ImageRow.name, ImageRow.architecture)
                        .in_(image_identifiers),
                    ),
                )

                for image_row in existing_images:
                    key = image_row.image_ref
                    values = all_updates.get(key)
                    if values is None:
                        continue
                    all_updates.pop(key)
                    image_row.config_digest = values['config_digest']
                    image_row.size_bytes = values['size_bytes']
                    image_row.accelerators = values.get('accels')
                    image_row.labels = values['labels']
                    image_row.resources = values['resources']

                session.add_all([
                    ImageRow(
                        name=k.canonical,
                        registry=k.registry,
                        image=k.name,
                        tag=k.tag,
                        architecture=k.architecture,
                        config_digest=v['config_digest'],
                        size_bytes=v['size_bytes'],
                        type=ImageType.COMPUTE,
                        accelerators=v.get('accels'),
                        labels=v['labels'],
                        resources=v['resources'],
                    ) for k, v in all_updates.items()
                ])

    async def _scan_image(
        self,
        sess: aiohttp.ClientSession,
        image: str,
    ) -> None:
        rqst_args = await registry_login(
            sess,
            self.registry_url,
            self.credentials,
            f'repository:{image}:pull',
        )
        rqst_args['headers'].update(**self.base_hdrs)
        tags = []
        tag_list_url: Optional[yarl.URL]
        tag_list_url = (self.registry_url / f'v2/{image}/tags/list').with_query(
            {'n': '10'},
        )
        while tag_list_url is not None:
            async with sess.get(tag_list_url, **rqst_args) as resp:
                data = json.loads(await resp.read())
                if 'tags' in data:
                    # sometimes there are dangling image names in the hub.
                    tags.extend(data['tags'])
                tag_list_url = None
                next_page_link = resp.links.get('next')
                if next_page_link:
                    next_page_url = cast(yarl.URL, next_page_link['url'])
                    tag_list_url = (
                        self.registry_url
                        .with_path(next_page_url.path)
                        .with_query(next_page_url.query)
                    )
        if (reporter := self.reporter.get()) is not None:
            reporter.total_progress += len(tags)
        async with aiotools.TaskGroup() as tg:
            for tag in tags:
                tg.create_task(self._scan_tag(sess, rqst_args, image, tag))

    async def _scan_tag(
        self,
        sess: aiohttp.ClientSession,
        rqst_args,
        image: str,
        tag: str,
    ) -> None:
        skip_reason = None

        async def _load_manifest(_tag: str):
            async with sess.get(self.registry_url / f'v2/{image}/manifests/{_tag}',
                                **rqst_args) as resp:
                if resp.status == 404:
                    # ignore missing tags
                    # (may occur after deleting an image from the docker hub)
                    return {}
                resp.raise_for_status()
                data = await resp.json()

                if data['mediaType'] == 'application/vnd.docker.distribution.manifest.list.v2+json':
                    # recursively call _load_manifests with detected arch and corresponding image digest
                    ret = {}
                    for m in data['manifests']:
                        ret.update(
                            await _load_manifest(
                                m['digest'],
                            ),
                        )
                    if (reporter := self.reporter.get()) is not None:
                        reporter.total_progress += len(ret) - 1
                    return ret

                config_digest = data['config']['digest']
                size_bytes = (sum(layer['size'] for layer in data['layers']) +
                                data['config']['size'])
                async with sess.get(self.registry_url / f'v2/{image}/blobs/{config_digest}',
                                    **rqst_args) as resp:
                    resp.raise_for_status()
                    data = json.loads(await resp.read())
                    architecture = arch_name_aliases.get(data['architecture'], data['architecture'])
                    labels = {}
                    if 'container_config' in data:
                        raw_labels = data['container_config'].get('Labels')
                        if raw_labels:
                            labels.update(raw_labels)
                        else:
                            log.warn('label not found on image {}:{}/{}', image, _tag, architecture)
                    else:
                        raw_labels = data['config'].get('Labels')
                        if raw_labels:
                            labels.update(raw_labels)
                        else:
                            log.warn('label not found on image {}:{}/{}', image, _tag, architecture)
                    return {
                        architecture: {
                            'size': size_bytes,
                            'labels': labels,
                            'digest': config_digest,
                        },
                    }

        async with self.sema.get():
            manifests = await _load_manifest(tag)

        if len(manifests.keys()) == 0:
            log.warning('Skipped image - {}:{} (missing/deleted)', image, tag)
            progress_msg = f"Skipped {image}:{tag} (missing/deleted)"
            if (reporter := self.reporter.get()) is not None:
                await reporter.update(1, message=progress_msg)

        idx = 0
        for architecture, manifest in manifests.items():
            idx += 1
            if manifest is None:
                skip_reason = 'missing/deleted'
                continue

            try:
                size_bytes = manifest['size']
                labels = manifest['labels']
                config_digest = manifest['digest']
                if 'ai.backend.kernelspec' not in labels:
                    # Skip non-Backend.AI kernel images
                    skip_reason = architecture + ": missing kernelspec"
                    continue
                if not (MIN_KERNELSPEC <= int(labels['ai.backend.kernelspec']) <= MAX_KERNELSPEC):
                    # Skip unsupported kernelspec images
                    skip_reason = architecture + ": unsupported kernelspec"
                    continue

                update_key = ImageRef(
                    f'{self.registry_name}/{image}:{tag}',
                    [self.registry_name],
                    architecture,
                )
                updates = {
                    'config_digest': config_digest,
                    'size_bytes': size_bytes,
                    'labels': labels,
                }
                accels = labels.get('ai.backend.accelerators')
                if accels:
                    updates['accels'] = accels

                resources = {}
                res_prefix = 'ai.backend.resource.min.'
                for k, v in filter(lambda pair: pair[0].startswith(res_prefix),
                                    labels.items()):
                    res_key = k[len(res_prefix):]
                    resources[res_key] = {'min': v}
                updates['resources'] = resources
                self.all_updates.get().update({
                    update_key: updates,
                })
            finally:
                if skip_reason:
                    log.warning('Skipped image - {}:{}/{} ({})', image, tag, architecture, skip_reason)
                    progress_msg = f"Skipped {image}:{tag}/{architecture} ({skip_reason})"
                else:
                    log.info('Updated image - {0}:{1}/{2}', image, tag, architecture)
                    progress_msg = f"Updated {image}:{tag}/{architecture}"
                if (reporter := self.reporter.get()) is not None:
                    await reporter.update(1, message=progress_msg)

    @abstractmethod
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        yield ""
