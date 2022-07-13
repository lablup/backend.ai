import json
from contextlib import closing
from typing import Tuple

from ...utils.cli import EOF, ClientRunnerFunc
from ..conftest import KeypairOption, User


def test_add_keypair(run: ClientRunnerFunc, users: Tuple[User], keypair_options: Tuple[KeypairOption]):
    """
    Test add keypair.
    This test should be execued first in test_keypair.py.
    """
    print("[ Add keypair ]")

    # Add test user
    for i, user in enumerate(users):
        arguments = [
            '--output=json',
            'admin', 'user', 'add',
            '-u', user.username,
            '-n', user.full_name,
            '-r', user.role,
            'default',
            user.email,
            user.password,
        ]
        with closing(run(arguments)) as p:
            p.expect(EOF)
            response = json.loads(p.before.decode())
            assert response.get('ok') is True, f'Account#{i+1} add error'

    # Create keypair
    for i, (user, keypair_option) in enumerate(zip(users, keypair_options)):
        keypair_add_arguments = [
            '--output=json',
            'admin', 'keypair', 'add',
            user.email,
            'default',
        ]
        if keypair_option.is_active is False:
            keypair_add_arguments.append('--inactive')
        if keypair_option.is_admin:
            keypair_add_arguments.append('--admin')
        if (rate_limit := keypair_option.rate_limit) is not None:
            keypair_add_arguments.extend(['--rate-limit', rate_limit])
        with closing(run(keypair_add_arguments)) as p:
            p.expect(EOF)
            response = json.loads(p.before.decode())
            assert response.get('ok') is True, f'Keypair#{i+1} add error'

    # Check if keypair is added
    with closing(run(['--output=json', 'admin', 'keypair', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        keypair_list = loaded.get('items')
        assert isinstance(keypair_list, list), 'List not printed properly!'

    for i, (user, keypair_option) in enumerate(zip(users, keypair_options)):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert 'access_key' in keypair, f'Keypair#{i+1} doesn\'t exist'
        assert keypair.get('is_active') is keypair_option.is_active, f'Keypair#{i+1} is_active mismatch'
        assert keypair.get('is_admin') is keypair_option.is_admin, f'Keypair#{i+1} is_admin mismatch'
        if (rate_limit := keypair_option.rate_limit) is not None:
            assert keypair.get('rate_limit') == rate_limit, f'Keypair#{i+1} rate_limit mismatch'
        assert keypair.get('resource_policy') == keypair_option.resource_policy, f'Keypair#{i+1} resource_policy mismatch'


def test_update_keypair(run: ClientRunnerFunc, users: Tuple[User], new_keypair_options: Tuple[KeypairOption]):
    """
    Test update keypair.
    This test must be executed after test_add_keypair.
    """
    print("[ Update keypair ]")

    # Get access key
    with closing(run(['--output=json', 'admin', 'keypair', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        keypair_list = loaded.get('items')
        assert isinstance(keypair_list, list), 'List not printed properly!'

    for i, (user, new_keypair_option) in enumerate(zip(users, new_keypair_options)):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert 'access_key' in keypair, f'Keypair#{i+1} info doesn\'t exist'

        keypair_update_arguments = [
            '--output=json',
            'admin', 'keypair', 'update',
            '--is-active', 'TRUE' if bool(new_keypair_option.is_active) else 'FALSE',
            '--is-admin', str(bool(new_keypair_option.is_admin)).upper(),
            '--rate-limit', new_keypair_option.rate_limit,
            keypair['access_key'],
        ]
        # Update keypair
        with closing(run(keypair_update_arguments)) as p:
            p.expect(EOF)
            response = json.loads(p.before.decode())
            assert response.get('ok') is True, f'Keypair#{i+1} update error'

    # Check if keypair is updated
    with closing(run(['--output=json', 'admin', 'keypair', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        updated_keypair_list = loaded.get('items')
        assert isinstance(updated_keypair_list, list), 'List not printed properly!'

    for i, (user, new_keypair_option) in enumerate(zip(users, new_keypair_options)):
        updated_keypair = get_keypair_from_list(updated_keypair_list, user.email)
        assert 'access_key' in updated_keypair, f'Keypair#{i+1} doesn\'t exist'
        assert updated_keypair.get('is_active') is new_keypair_option.is_active, f'Keypair#{i+1} is_active mismatch'
        assert updated_keypair.get('is_admin') is new_keypair_option.is_admin, f'Keypair#{i+1} is_admin mismatch'
        assert updated_keypair.get('rate_limit') == new_keypair_option.rate_limit, f'Keypair#{i+1} rate_limit mismatch'
        assert updated_keypair.get('resource_policy') == new_keypair_option.resource_policy, \
                                                                                f'Keypair#{i+1} resource_policy mismatch'


def test_delete_keypair(run: ClientRunnerFunc, users: Tuple[User]):
    """
    Test delete keypair.
    This test must be executed after test_add_keypair.
    """
    print("[ Delete keypair ]")

    # Get access key
    with closing(run(['--output=json', 'admin', 'keypair', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        keypair_list = loaded.get('items')
        assert isinstance(keypair_list, list), 'List not printed properly!'

    for i, user in enumerate(users):
        keypair = get_keypair_from_list(keypair_list, user.email)
        assert 'access_key' in keypair, f'Keypair#{i+1} info doesn\'t exist'

        # Delete keypair
        with closing(run(['admin', 'keypair', 'delete', keypair['access_key']])) as p:
            p.expect(EOF)

        # Delete test user
        with closing(run(['--output=json', 'admin', 'user', 'purge', user.email])) as p:
            p.sendline('y')
            p.expect(EOF)
            before = p.before.decode()
            response = json.loads(before[before.index('{'):])
            assert response.get('ok') is True, f'Account deletion failed: {user.username}'


def test_list_keypair(run: ClientRunnerFunc):
    """
    Test list keypair.
    """
    with closing(run(['--output=json', 'admin', 'keypair', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        keypair_list = loaded.get('items')
        assert isinstance(keypair_list, list), 'List not printed properly!'


def get_keypair_from_list(keypairs: list, userid: str) -> dict:
    for keypair in keypairs:
        if keypair.get('user_id', '') == userid:
            return keypair
    return {}
