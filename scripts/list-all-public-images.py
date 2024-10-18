import asyncio
import operator
from collections import namedtuple

import aiohttp
import aiojobs

DOCKER_HUB_URL = 'https://hub.docker.com/v2/repositories/lablup/?page_size=100'
AUTH_TOKEN_URL = (
    'https://auth.docker.io/token'
    '?service=registry.docker.io&scope=repository:{0}:pull'
)
TAG_LIST_URL = 'https://registry-1.docker.io/v2/{0}/tags/list'
DIGEST_URL = 'https://registry-1.docker.io/v2/{0}/manifests/{1}'


ImageDetail = namedtuple('ImageDetail', ['name', 'tag_digest_pairs'])


async def fetch(url, sess, is_json=True, headers=None):
    if not headers:
        headers = {}
    async with sess.get(url, headers=headers) as resp:
        resp.raise_for_status()
        if is_json:
            return await resp.json()
        else:
            return await resp.text()


async def get_all_image_summaries(sess):
    result = await fetch(DOCKER_HUB_URL,
                         sess)
    return [(f'lablup/{image["name"]}', image['last_updated'])
            for image in result['results']]


async def get_auth_token(image_name, sess):
    result = await fetch(AUTH_TOKEN_URL.format(image_name),
                         sess)
    return result['token']


async def get_all_tags(image_name, sess, token):
    try:
        result = await fetch(TAG_LIST_URL.format(image_name),
                             sess,
                             headers={'Authorization': f'Bearer {token}'})
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            return []
        else:
            raise e
    return result['tags']


async def get_digest(image_name, tag, sess, token):
    result = await fetch(
        DIGEST_URL.format(image_name, tag),
        sess,
        headers={'Authorization': f'Bearer {token}',
                 'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
    )
    return result['config']['digest']


async def get_image_detail(image_name, sess):
    token = await get_auth_token(image_name, sess)
    tags = await get_all_tags(image_name, sess, token)
    digests = await asyncio.gather(*[get_digest(image_name, tag, sess, token)
                                     for tag in tags])
    return ImageDetail(image_name,
                       [(tag, digest) for tag, digest in zip(tags, digests)])


async def list_all_public_images():
    scheduler = await aiojobs.create_scheduler()
    image_filter = lambda name: (
        name.startswith('lablup/kernel-') and 'base' not in name
    )
    async with aiohttp.ClientSession() as sess:
        image_summaries = await get_all_image_summaries(sess)
        jobs = await asyncio.gather(
            *[scheduler.spawn(get_image_detail(image_name, sess))
              for image_name, _ in image_summaries
              if image_filter(image_name)]
        )
        image_details = await asyncio.gather(*[job.wait()
                                               for job in jobs])
        table = []
        for image_detail, image_summary in zip(image_details, image_summaries):
            image_name, tag_digest_pairs = image_detail
            last_updated = image_summary[1][:19]
            for tag, digest in tag_digest_pairs:
                table.append((image_name, last_updated, tag, digest))
        table.sort(key=operator.itemgetter(1), reverse=True)

        print_format = '{0:40s} {1:20s} {2:30s} {3:32s}'
        print(print_format.format('Image', 'Last Updated', 'Tag', 'Digest'))
        for row in table:
            print(print_format.format(*row))

        await scheduler.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_all_public_images())


if __name__ == '__main__':
    main()
