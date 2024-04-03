from __future__ import annotations

import os
import re
import secrets
from collections import namedtuple
from contextlib import closing
from io import TextIOWrapper
from pathlib import Path
from typing import Callable, Generator, Iterator, Sequence, Tuple

import pexpect
import pytest
from faker import Faker

from ai.backend.plugin.entrypoint import find_build_root
from ai.backend.test.utils.cli import EOF, ClientRunnerFunc, run

_rx_env_export = re.compile(r"^(export )?(?P<key>\w+)=(?P<val>.*)$")

User = namedtuple(
    "User",
    (
        "username",
        "full_name",
        "email",
        "password",
        "role",
        "status",
        "domain_name",
        "need_password_change",
    ),
)
KeypairOption = namedtuple(
    "KeypairOption", ("is_active", "is_admin", "rate_limit", "resource_policy")
)


@pytest.fixture(scope="session")
def client_bin() -> Path:
    return find_build_root(Path(__file__)) / "backend.ai"


def make_run_fixture(profile_env: str) -> Callable[[Path], Iterator[ClientRunnerFunc]]:
    @pytest.fixture(scope="session")
    def run_given_profile(
        client_bin: Path,
    ) -> Iterator[ClientRunnerFunc]:
        env_from_file = get_env_from_profile(profile_env)

        def run_impl(cmdargs: Sequence[str | Path], *args, **kwargs) -> pexpect.spawn:
            return run([client_bin, *cmdargs], *args, **kwargs, env={**os.environ, **env_from_file})

        yield run_impl

    return run_given_profile


def get_env_from_profile(profile_env: str) -> dict[str, str]:
    if not (file_path_env := os.environ.get(profile_env)):
        raise RuntimeError(f"Missing {profile_env} enviroment variable!")
    file_path = Path(file_path_env)

    envs = {}
    lines = file_path.read_text().splitlines()
    for line in lines:
        if m := _rx_env_export.search(line.strip()):
            envs[m.group("key")] = m.group("val")
    return envs


@pytest.fixture
def domain_name() -> str:
    return f"testing-{secrets.token_hex(8)}"


@pytest.fixture
def temp_domain(domain_name: str, run: ClientRunnerFunc) -> Iterator[str]:
    run(["admin", "domains", "add", domain_name])
    print("==== temp_domain created ====")
    try:
        yield domain_name
    finally:
        with closing(run(["admin", "domains", "purge", domain_name])) as p:
            p.expect_exact("Are you sure?")
            p.sendline("Y")
            p.expect(EOF)


@pytest.fixture(scope="module")
def users(n: int = 3) -> Tuple[User, ...]:
    fake = Faker()
    return tuple(
        User(
            username=fake.user_name(),
            full_name=fake.name(),
            email=fake.email(),
            password=fake.password(8),
            role=["user", "admin", "monitor"][i % 3],
            status=["active", "inactive", "before-verification", "deleted"][i % 4],
            domain_name="default",
            need_password_change=[True, False, True][i % 3],
        )
        for i in range(3)
    )


@pytest.fixture
def gen_username() -> Callable[[], str]:
    return lambda: Faker().user_name()


@pytest.fixture
def gen_fullname() -> Callable[[], str]:
    return lambda: Faker().name()


@pytest.fixture(scope="module")
def keypair_options() -> Tuple[KeypairOption, ...]:
    return (
        KeypairOption(is_active=False, is_admin=True, rate_limit=25000, resource_policy="default"),
        KeypairOption(is_active=True, is_admin=False, rate_limit=None, resource_policy="default"),
        KeypairOption(is_active=True, is_admin=True, rate_limit=30000, resource_policy="default"),
    )


@pytest.fixture(scope="module")
def new_keypair_options() -> Tuple[KeypairOption, ...]:
    return (
        KeypairOption(is_active=True, is_admin=False, rate_limit=15000, resource_policy="default"),
        KeypairOption(is_active=False, is_admin=True, rate_limit=15000, resource_policy="default"),
        KeypairOption(
            is_active=False, is_admin=False, rate_limit=100000, resource_policy="default"
        ),
    )


@pytest.fixture(scope="module")
def keypair_resource_policy() -> str:
    fake = Faker()
    return fake.unique.word()


@pytest.fixture
def txt_file() -> Generator[TextIOWrapper, None, None]:
    filepath = "test.txt"
    with open(filepath, "w") as f:
        f.write("This file is for testing.")
    yield f

    os.remove(filepath)


run_user = make_run_fixture("user_file")
run_user2 = make_run_fixture("user2_file")
run_admin = make_run_fixture("admin_file")
