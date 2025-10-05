import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc, decode


def test_alias_image(run_admin: ClientRunnerFunc):
    pass


def test_dealias_image(run_admin: ClientRunnerFunc):
    pass


def test_list_image(run_admin: ClientRunnerFunc):
    print("[ List image ]")
    with closing(run_admin(["--output=json", "admin", "image", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        image_list = loaded.get("items")
        assert isinstance(image_list, list), "Image list not printed properly"
