import asyncio
import aiohttp
import aiojobs
from collections import namedtuple


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


async def get_all_image_names(sess):
    result = await fetch(DOCKER_HUB_URL,
                         sess)
    return [f'lablup/{image["name"]}' for image in result['results']]


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


def print_image_details(image_details):
    print_format = '{0:40s} {1:30s} {2:32s}'
    print(print_format.format('Image', 'Tag', 'Digest'))
    for image_detail in image_details:
        image_name, tag_digest_pairs = image_detail
        for tag, digest in tag_digest_pairs:
            print(print_format.format(image_name, tag, digest))


async def list_all_public_images():
    scheduler = await aiojobs.create_scheduler()
    async with aiohttp.ClientSession() as sess:
        image_names = await get_all_image_names(sess)
        jobs = await asyncio.gather(
            *[scheduler.spawn(get_image_detail(image_name, sess))
              for image_name in image_names]
        )
        image_details = await asyncio.gather(*[job.wait()
                                               for job in jobs])
        print_image_details(image_details)

        await scheduler.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_all_public_images())


if __name__ == '__main__':
    main()
