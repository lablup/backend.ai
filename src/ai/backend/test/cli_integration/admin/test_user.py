import json
from contextlib import closing
from typing import Callable, Tuple

from ...utils.cli import EOF, ClientRunnerFunc, decode
from ..conftest import User


def test_add_user(run_admin: ClientRunnerFunc, users: Tuple[User, ...]):
    """
    Testcase for user addition.
    """
    print("[ Add user ]")

    # Add users
    for i, user in enumerate(users):
        add_arguments = [
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
            "-s",
            user.status,
            "default",
            user.email,
            user.password,
        ]
        if user.need_password_change:
            add_arguments.append("--need-password-change")
        with closing(run_admin(add_arguments)) as p:
            p.expect(EOF)
            response = json.loads(decode(p.before))
            assert response.get("ok") is True, f"Account creation failed: Account#{i + 1}"

    # Check if user is added
    with closing(run_admin(["--output=json", "admin", "user", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        user_list = loaded.get("items")

    assert isinstance(user_list, list), "Expected user list"
    added_users = tuple(get_user_from_list(user_list, user.username) for user in users)

    for i, (added_user, user) in enumerate(zip(added_users, users)):
        assert bool(added_user), f"Added account doesn't exist: Account#{i + 1}"
        assert added_user.get("email") == user.email, f"E-mail mismatch: Account#{i + 1}"
        assert added_user.get("full_name") == user.full_name, f"Full name mismatch: Account#{i + 1}"
        assert added_user.get("status") == user.status, f"User status mismatch: Account#{i + 1}"
        assert added_user.get("role") == user.role, f"Role mismatch: Account#{i + 1}"
        assert added_user.get("need_password_change") is user.need_password_change, (
            f"Password change status mismatch: Account#{i + 1}"
        )


def test_update_user(
    run_admin: ClientRunnerFunc,
    users: Tuple[User, ...],
    gen_username: Callable[[], str],
    gen_fullname: Callable[[], str],
):
    """
    Run this testcase after test_add_user.
    Testcase for user update.
    TODO: User update with roles is not fully covered yet.
    """
    print("[ Update user ]")

    # updated_users = [user.copy() for user in users]
    updated_users = (
        User(
            username=gen_username(),
            full_name=gen_fullname(),
            email=user.email,
            password=user.password,
            role=["user", "admin", "monitor"][i % 3],
            status=["inactive", "active", "active"][i % 3],
            domain_name="default",
            need_password_change=[False, True, False][i % 3],
        )
        for i, user in enumerate(users)
    )

    # Update user
    for updated_user, user in zip(updated_users, users):
        update_arguments = [
            "--output=json",
            "admin",
            "user",
            "update",
            "-u",
            updated_user.username,
            "-n",
            updated_user.full_name,
            "-s",
            updated_user.status,
            "-r",
            updated_user.role,
            "-d",
            updated_user.domain_name,
            user.email,
        ]
        if updated_user.need_password_change:
            update_arguments.append("--need-password-change")
        with closing(run_admin(update_arguments)) as p:
            p.expect(EOF)

    # Check if user is updated correctly
    with closing(run_admin(["--output=json", "admin", "user", "list"])) as p:
        p.expect(EOF)
        after_update_decoded = decode(p.before)
        after_update_loaded = json.loads(after_update_decoded)
        updated_user_list = after_update_loaded.get("items")
        assert isinstance(updated_user_list, list), "Expected user list"

    for i, updated_user in enumerate(updated_users):
        user_dict: dict = get_user_from_list(updated_user_list, updated_user.username)
        assert bool(user_dict), f"Account not found - Account#{i + 1}"
        assert user_dict.get("full_name") == updated_user.full_name, (
            f"Full name mismatch: Account#{i + 1}"
        )
        assert user_dict.get("status") == updated_user.status, (
            f"User status mismatch: Account#{i + 1}"
        )
        assert user_dict.get("role") == updated_user.role, f"Role mismatch: Account#{i + 1}"
        assert user_dict.get("need_password_change") is updated_user.need_password_change, (
            f"Password change status mismatch: Account#{i + 1}"
        )
        assert user_dict.get("domain_name") == updated_user.domain_name, (
            f"Domain mismatch: Account#{i + 1}"
        )


def test_delete_user(run_admin: ClientRunnerFunc, users: Tuple[User, ...]):
    """
    !!Run this testcase after running test_add_user
    Testcase for user deletion.
    """
    print("[ Delete user ]")

    for i, fake_user in enumerate(users):
        with closing(run_admin(["--output=json", "admin", "user", "purge", fake_user.email])) as p:
            p.sendline("y")
            p.expect(EOF)
            before = decode(p.before)
            response = json.loads(before[before.index("{") :])
            assert response.get("ok") is True, f"Account deletion failed: Account#{i + 1}"


def test_list_user(run_admin: ClientRunnerFunc):
    """
    Testcase for user listing.
    """
    with closing(run_admin(["--output=json", "admin", "user", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        user_list = loaded.get("items")
        assert isinstance(user_list, list)


def get_user_from_list(users: list, username: str) -> dict:
    for user in users:
        if user.get("username") == username:
            return user
    return {}
