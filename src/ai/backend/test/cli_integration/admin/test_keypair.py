import json
from contextlib import closing
from typing import Tuple

from ...utils.cli import EOF, ClientRunnerFunc, decode
from ..conftest import KeypairOption, User


def test_add_keypair(
    run_admin: ClientRunnerFunc, users: Tuple[User], keypair_options: Tuple[KeypairOption]
):
    """
    Test add keypair.
    This test should be execued first in test_keypair.py.
    """
    print("[ Add keypair ]")

    # Add test user
    user_ids = []
    for i, user in enumerate(users):
        arguments = [
            "--output=json",
            "admin",
            "user",
            "add",
            "-u",
            user.username,
            "-n",
            user.full_name,
            "-r",
            user.role,
            "default",
            user.email,
            user.password,
        ]
        with closing(run_admin(arguments)) as p:
            p.expect(EOF)
            response = json.loads(decode(p.before))
            assert response.get("ok") is True, f"Account#{i + 1} add error"
            user_ids.append(response["user"]["uuid"])

    # find group
    arguments = [
        "--output=json",
        "admin",
        "group",
        "list",
    ]
    with closing(run_admin(arguments)) as p:
        p.expect(EOF)
        response = json.loads(decode(p.before))
        group_id = response.get("items")[0]["id"]

    # FIXME: Delete the following code
    #  When the bug, where a keypair owned by a user not added to a group is not found, is fixed.

    # add created users to group
    arguments = [
        "--output=json",
        "admin",
        "group",
        "add-users",
        group_id,
        *user_ids,
    ]
    with closing(run_admin(arguments)) as p:
        p.expect(EOF)
        response = json.loads(decode(p.before))
        assert response.get("ok") is True, "cannot add users to group"

    # Create keypair
    for i, (user, keypair_option) in enumerate(zip(users, keypair_options)):
        keypair_add_arguments = [
            "--output=json",
            "admin",
            "keypair",
            "add",
            user.email,
            "default",
        ]
        if keypair_option.is_active is False:
            keypair_add_arguments.append("--inactive")
        if keypair_option.is_admin:
            keypair_add_arguments.append("--admin")
        if (rate_limit := keypair_option.rate_limit) is not None:
            keypair_add_arguments.extend(["--rate-limit", rate_limit])
        with closing(run_admin(keypair_add_arguments)) as p:
            p.expect(EOF)
            response = json.loads(decode(p.before))
            assert response.get("ok") is True, f"Keypair#{i + 1} add error"
    # Check if keypair is added
    with closing(run_admin(["--output=json", "admin", "keypair", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        keypair_list = loaded.get("items")
        assert isinstance(keypair_list, list), "List not printed properly!"

    for i, (user, keypair_option) in enumerate(zip(users, keypair_options)):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert "access_key" in keypair, f"Keypair#{i + 1} doesn't exist"
        assert keypair.get("is_active") is keypair_option.is_active, (
            f"Keypair#{i + 1} is_active mismatch"
        )
        assert keypair.get("is_admin") is keypair_option.is_admin, (
            f"Keypair#{i + 1} is_admin mismatch"
        )
        if (rate_limit := keypair_option.rate_limit) is not None:
            assert keypair.get("rate_limit") == rate_limit, f"Keypair#{i + 1} rate_limit mismatch"
        assert keypair.get("resource_policy") == keypair_option.resource_policy, (
            f"Keypair#{i + 1} resource_policy mismatch"
        )


def test_update_keypair(
    run_admin: ClientRunnerFunc, users: Tuple[User], new_keypair_options: Tuple[KeypairOption]
):
    """
    Test update keypair.
    This test must be executed after test_add_keypair.
    """
    print("[ Update keypair ]")

    # Get access key
    with closing(run_admin(["--output=json", "admin", "keypair", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        keypair_list = loaded.get("items")
        assert isinstance(keypair_list, list), "List not printed properly!"

    for i, (user, new_keypair_option) in enumerate(zip(users, new_keypair_options)):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert "access_key" in keypair, f"Keypair#{i + 1} info doesn't exist"

        keypair_update_arguments = [
            "--output=json",
            "admin",
            "keypair",
            "update",
            "--is-active",
            "TRUE" if bool(new_keypair_option.is_active) else "FALSE",
            "--is-admin",
            str(bool(new_keypair_option.is_admin)).upper(),
            "--rate-limit",
            new_keypair_option.rate_limit,
            keypair["access_key"],
        ]
        # Update keypair
        with closing(run_admin(keypair_update_arguments)) as p:
            p.expect(EOF)
            response = json.loads(decode(p.before))
            assert response.get("ok") is True, f"Keypair#{i + 1} update error"

    # Check if keypair is updated
    with closing(run_admin(["--output=json", "admin", "keypair", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        updated_keypair_list = loaded.get("items")
        assert isinstance(updated_keypair_list, list), "List not printed properly!"

    for i, (user, new_keypair_option) in enumerate(zip(users, new_keypair_options)):
        updated_keypair = get_keypair_from_list(updated_keypair_list, user.email)
        assert "access_key" in updated_keypair, f"Keypair#{i + 1} doesn't exist"
        assert updated_keypair.get("is_active") is new_keypair_option.is_active, (
            f"Keypair#{i + 1} is_active mismatch"
        )
        assert updated_keypair.get("is_admin") is new_keypair_option.is_admin, (
            f"Keypair#{i + 1} is_admin mismatch"
        )
        assert updated_keypair.get("rate_limit") == new_keypair_option.rate_limit, (
            f"Keypair#{i + 1} rate_limit mismatch"
        )
        assert updated_keypair.get("resource_policy") == new_keypair_option.resource_policy, (
            f"Keypair#{i + 1} resource_policy mismatch"
        )


def test_delete_keypair(run_admin: ClientRunnerFunc, users: Tuple[User]):
    """
    Test delete keypair.
    This test must be executed after test_add_keypair.
    """
    print("[ Delete keypair ]")
    return
    # Get access key
    with closing(run_admin(["--output=json", "admin", "keypair", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        keypair_list = loaded.get("items")
        assert isinstance(keypair_list, list), "List not printed properly!"

    for i, user in enumerate(users):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert "access_key" in keypair, f"Keypair#{i + 1} info doesn't exist"

        # Delete keypair
        with closing(run_admin(["admin", "keypair", "delete", keypair["access_key"]])) as p:
            p.expect(EOF)

        # Delete test user
        with closing(run_admin(["--output=json", "admin", "user", "purge", user.email])) as p:
            p.sendline("y")
            p.expect(EOF)
            before = decode(p.before)
            response = json.loads(before[before.index("{") :])
            assert response.get("ok") is True, f"Account deletion failed: {user.username}"


def test_list_keypair(run_admin: ClientRunnerFunc):
    """
    Test list keypair.
    """
    with closing(run_admin(["--output=json", "admin", "keypair", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        keypair_list = loaded.get("items")
        assert isinstance(keypair_list, list), "List not printed properly!"


def test_delete_keypair_on_running_session(run_admin: ClientRunnerFunc):
    admin_find_command = [
        "--output=json",
        "admin",
        "user",
        "list",
        "--filter",
        'username == "admin"',
    ]
    with closing(run_admin(admin_find_command)) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        item = loaded.get("items")
        assert len(item) == 1, "admin user not found"
        admin_user_info = item[0]
        assert admin_user_info.get("username") == "admin"
        assert admin_user_info.get("email")

    # create keypair
    keypair_add_arguments = [
        "--output=json",
        "admin",
        "keypair",
        "add",
        admin_user_info.get("email"),
        "default",
        "--admin",
    ]
    with closing(run_admin(keypair_add_arguments)) as p:
        p.expect(EOF)
        response = json.loads(decode(p.before))
        access_key = response.get("access_key")
        assert access_key
        assert response.get("ok") is True, "Admin keypair add error"

    # find image
    with closing(run_admin(["--output=json", "admin", "image", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        image_list = loaded.get("items")
        assert isinstance(image_list, list), "Image list not printed properly"
        assert len(image_list) > 0, "No image found"

        target_image = image_list[0]
        assert target_image.get("name")
        assert target_image.get("registry")
        assert target_image.get("tag")

    image_name = target_image.get("name")
    image_registry = target_image.get("registry")
    image_tag = target_image.get("tag")

    session_image_name = f"{image_registry}/{image_name}:{image_tag}"

    # create session
    session_name = f"test_session_{access_key}"
    create_session_command = [
        "--output=json",
        "session",
        "create",
        session_image_name,
        "-o",
        access_key,
        "--enqueue-only",
        "--name",
        session_name,
    ]

    with closing(run_admin(create_session_command)) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        assert "is enqueued for scheduling." in decoded, "Session creation failed"

    with closing(run_admin(["--output=json", "admin", "session", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        session_list = loaded.get("items")
        assert isinstance(session_list, list), "Session list not printed properly"
        assert len(session_list) > 0, "No session found"
        session_name_list = [session.get("name") for session in session_list]
        assert session_name in session_name_list, f"Session name {session_name} creation failed"

    # delete keypair
    with closing(run_admin(["--output=json", "admin", "keypair", "delete", access_key])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        print("delete keypair response", loaded)
        assert loaded.get("ok") is False, "Keypair should not be deleted"

    # delete session
    with closing(
        run_admin(["--output=json", "session", "rm", session_name, "-o", access_key])
    ) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        assert "Done" in decoded, "Session deletion failed"

    # delete keypair
    with closing(run_admin(["--output=json", "admin", "keypair", "delete", access_key])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        assert loaded.get("ok") is True, "Keypair deletion failed"


def get_keypair_from_list(keypairs: list, userid: str) -> dict:
    for keypair in keypairs:
        if keypair.get("user_id", "") == userid:
            return keypair
    return {}
