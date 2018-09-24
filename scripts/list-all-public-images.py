import asyncio
import aiohttp
import aiojobs


DOCKER_HUB_URL = 'https://hub.docker.com/v2/repositories/lablup/?page_size=100'
AUTH_TOKEN_URL = 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:{0}:pull'
TAG_LIST_URL = 'https://registry-1.docker.io/v2/{0}/tags/list'
REGISTRY_URL = 'https://registry-1.docker.io/v2/{0}/manifests/{1}'


async def fetch(url, sess, is_json=False, headers=None):
    if not headers:
        headers = {}
    async with sess.get(url, headers=headers) as resp:
        assert resp.status == 200, resp.status
        if is_json:
            return await resp.json()
        else:
            return await resp.text()


async def get_all_image_names(sess):
    result = await fetch(DOCKER_HUB_URL,
                         sess,
                         is_json=True)
    return [f'lablup/{image["name"]}' for image in result['results']]


async def get_auth_token(image_name, sess):
    result = await fetch(AUTH_TOKEN_URL.format(image_name),
                         sess,
                         is_json=True)
    return result['token']


async def get_all_tags(image_name, sess, token):
    try:
        result = await fetch(TAG_LIST_URL.format(image_name),
                             sess,
                             is_json=True,
                             headers={'Authorization': f'Bearer {token}'})
    except AssertionError as e:
        if f'{e}' == '404':
            return []
        else:
            raise e
    return result['tags']


async def list_all_tags_for_image(image_name, sess):
    token = await get_auth_token(image_name, sess)
    tags = await get_all_tags(image_name, sess, token)
    return [f'{image_name}:{tag}' for tag in tags]


async def list_all_public_images():
    scheduler = await aiojobs.create_scheduler()
    async with aiohttp.ClientSession() as sess:
        image_names = await get_all_image_names(sess)
        jobs = await asyncio.gather(*[scheduler.spawn(list_all_tags_for_image(image_name, sess))
                                      for image_name in image_names])
        images_with_tags = await asyncio.gather(*[job.wait()
                                                  for job in jobs])
        all_image_names = [image_with_tag
                           for image_with_tags in images_with_tags
                           for image_with_tag in image_with_tags]
        print(all_image_names)

        await scheduler.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_all_public_images())


if __name__ == '__main__':
    main()
