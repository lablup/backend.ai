import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_keypair_resource_policy(run: ClientRunnerFunc):
    print("[ Add keypair resource policy ]")

    # Add keypair resource policy
    add_arguments = [
        'admin', 'keypair-resource-policy', 'add',
        '--default-for-unspecified', 'LIMITED',
        '--total-resource-slots', '{}',
        '--max-concurrent-sessions', '20',
        '--max-containers-per-session', '2',
        '--max-vfolder-count', '15',
        '--max-vfolder-size', '0',
        '--allowed-vfolder-hosts', 'local:volume1',
        '--idle-timeout', '1200',
        'test_krp',
    ]
    with closing(run(add_arguments)) as p:
        p.expect(EOF)
        assert 'Keypair resource policy test_krp is created.' in p.before.decode(), \
            'Keypair resource policy creation not successful'

    # Check if keypair resource policy is created
    with closing(run(['--output=json', 'admin', 'keypair-resource-policy', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        krp_list = loaded.get('items')
        assert isinstance(krp_list, list), 'Keypair resource policy list not printed properly'

    test_krp = get_keypair_resource_policy_from_list(krp_list, 'test_krp')

    assert bool(test_krp), 'Test keypair resource policy doesn\'t exist'
    assert test_krp.get('total_resource_slots') == '{}', 'Test keypair resource policy total resource slot mismatch'
    assert test_krp.get('max_concurrent_sessions') == 20, 'Test keypair resource policy max concurrent session mismatch'
    assert test_krp.get('max_vfolder_count') == 15, 'Test keypair resource policy max vfolder count mismatch'
    assert test_krp.get('max_vfolder_size') == '0 Bytes', 'Test keypair resource policy max vfolder size mismatch'
    assert test_krp.get('idle_timeout') == 1200, 'Test keypair resource policy idle timeout mismatch'
    assert test_krp.get('max_containers_per_session') == 2,\
        'Test keypair resouce policy max containers per session mismatch'
    assert test_krp.get('allowed_vfolder_hosts') == ['local:volume1'], \
        'Test keypair resource policy allowed vfolder hosts mismatch'


def test_update_keypair_resource_policy(run: ClientRunnerFunc):
    print("[ Update keypair resource policy ]")

    # Update keypair resource policy
    add_arguments = [
        'admin', 'keypair-resource-policy', 'update',
        '--default-for-unspecified', 'UNLIMITED',
        '--total-resource-slots', '{}',
        '--max-concurrent-sessions', '30',
        '--max-containers-per-session', '1',
        '--max-vfolder-count', '10',
        '--max-vfolder-size', '0',
        '--allowed-vfolder-hosts', 'local:volume2',
        '--idle-timeout', '1800',
        'test_krp',
    ]
    with closing(run(add_arguments)) as p:
        p.expect(EOF)
        assert 'Update succeeded.' in p.before.decode(), 'Keypair resource policy update not successful'

    # Check if keypair resource policy is updated
    with closing(run(['--output=json', 'admin', 'keypair-resource-policy', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        krp_list = loaded.get('items')
        assert isinstance(krp_list, list), 'Keypair resource policy list not printed properly'

    test_krp = get_keypair_resource_policy_from_list(krp_list, 'test_krp')

    assert bool(test_krp), 'Test keypair resource policy doesn\'t exist'
    assert test_krp.get('total_resource_slots') == '{}', 'Test keypair resource policy total resource slot mismatch'
    assert test_krp.get('max_concurrent_sessions') == 30, 'Test keypair resource policy max concurrent session mismatch'
    assert test_krp.get('max_vfolder_count') == 10, 'Test keypair resource policy max vfolder count mismatch'
    assert test_krp.get('max_vfolder_size') == '0 Bytes', 'Test keypair resource policy max vfolder size mismatch'
    assert test_krp.get('idle_timeout') == 1800, 'Test keypair resource policy idle timeout mismatch'
    assert test_krp.get('max_containers_per_session') == 1,\
        'Test keypair resouce policy max containers per session mismatch'
    assert test_krp.get('allowed_vfolder_hosts') == ['local:volume2'], \
        'Test keypair resource policy allowed vfolder hosts mismatch'


def test_delete_keypair_resource_policy(run: ClientRunnerFunc):
    print("[ Delete keypair resource policy ]")

    # Delete keypair resource policy
    with closing(run(['admin', 'keypair-resource-policy', 'delete', 'test_krp'])) as p:
        p.sendline('y')
        p.expect(EOF)
        assert 'Resource policy test_krp is deleted.' in p.before.decode(), 'Keypair resource policy deletion failed'


def test_list_keypair_resource_policy(run: ClientRunnerFunc):
    print("[ List keypair resource policy ]")
    with closing(run(['--output=json', 'admin', 'keypair-resource-policy', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        krp_list = loaded.get('items')
        assert isinstance(krp_list, list), 'Keypair resource policy list not printed properly'


def get_keypair_resource_policy_from_list(krps: list, name: str) -> dict:
    for krp in krps:
        if krp.get('name') == name:
            return krp
    return {}
