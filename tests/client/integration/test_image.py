import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session

# module-level marker
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_list_images_by_admin():
    with Session() as sess:
        images = sess.Image.list()
        image = images[0]
    assert len(images) > 0
    assert "name" in image
    assert "tag" in image
    assert "hash" in image


@pytest.mark.asyncio
async def test_list_images_by_user(userconfig):
    with Session() as sess:
        images = sess.Image.list()
        image = images[0]
    assert len(images) > 0
    assert "name" in image
    assert "tag" in image
    assert "hash" in image


@pytest.mark.asyncio
async def test_alias_dealias_image_by_admin():
    with Session() as sess:

        def get_test_image_info():
            items = sess.Image.list(fields=("name", "registry", "tag", "aliases"))
            for item in items:
                if "lua" in item["name"] and "5.1-alpine3.8" in item["tag"]:
                    return item

        img_info = get_test_image_info()
        test_alias = "testalias-b9f1ce136f584ca892d5fef3e78dd11d"
        test_target = img_info["registry"] + "/" + img_info["name"] + ":" + img_info["tag"]
        sess.Image.aliasImage(test_alias, test_target)
        assert get_test_image_info()["aliases"] == [test_alias]

        sess.Image.dealiasImage(test_alias)
        assert len(get_test_image_info()["aliases"]) == 0


@pytest.mark.asyncio
async def test_user_cannot_mutate_alias_dealias(userconfig):
    with Session() as sess:
        test_alias = "testalias-b9f1ce136f584ca892d5fef3e78dd11d"
        with pytest.raises(BackendAPIError):
            sess.Image.aliasImage(test_alias, "lua:5.1-alpine3.8")
        with pytest.raises(BackendAPIError):
            sess.Image.dealiasImage(test_alias)
