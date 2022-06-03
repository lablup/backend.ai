import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_domain(run: ClientRunnerFunc):
    print("[ Add domain ]")

    # Add domain
    add_arguments = [
        'admin', 'domain', 'add',
        '-d', 'Test domain',
        '-i',
        '--total-resource-slots', '{}',
        '--allowed-vfolder-hosts', 'local:volume1',
        '--allowed-docker-registries', 'cr.backend.ai',
        'test',
    ]
    with closing(run(add_arguments)) as p:
        p.expect(EOF)
        assert 'Domain name test is created.' in p.before.decode(), 'Domain creation not successful'

    # Check if domain is added
    with closing(run(['--output=json', 'admin', 'domain', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get('items')
        assert isinstance(domain_list, list), 'Domain list not printed properly'

    test_domain = get_domain_from_list(domain_list, 'test')

    assert bool(test_domain), 'Test domain doesn\'t exist'
    assert test_domain.get('description') == 'Test domain', 'Domain description mismatch'
    assert test_domain.get('is_active') is False, 'Domain active status mismatch'
    assert test_domain.get('total_resource_slots') == {}, 'Domain total resource slots mismatch'
    assert test_domain.get('allowed_vfolder_hosts') == ['local:volume1'], 'Domain allowed vfolder hosts mismatch'
    assert test_domain.get('allowed_docker_registries') == ['cr.backend.ai'], 'Domain allowed docker registries mismatch'


def test_update_domain(run: ClientRunnerFunc):
    print("[ Update domain ]")

    # Update domain
    add_arguments = [
        'admin', 'domain', 'update',
        '--new-name', 'test123',
        '--description', 'Test domain updated',
        '--is-active', 'TRUE',
        '--total-resource-slots', '{}',
        '--allowed-vfolder-hosts', 'local:volume2',
        '--allowed-docker-registries', 'cr1.backend.ai',
        'test',
    ]
    with closing(run(add_arguments)) as p:
        p.expect(EOF)
        assert 'Domain test is updated.' in p.before.decode(), 'Domain update not successful'

    # Check if domain is updated
    with closing(run(['--output=json', 'admin', 'domain', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get('items')
        assert isinstance(domain_list, list), 'Domain list not printed properly'

    test_domain = get_domain_from_list(domain_list, 'test123')

    assert bool(test_domain), 'Test domain doesn\'t exist'
    assert test_domain.get('description') == 'Test domain updated', 'Domain description mismatch'
    assert test_domain.get('is_active') is True, 'Domain active status mismatch'
    assert test_domain.get('total_resource_slots') == {}, 'Domain total resource slots mismatch'
    assert test_domain.get('allowed_vfolder_hosts') == ['local:volume2'], 'Domain allowed vfolder hosts mismatch'
    assert test_domain.get('allowed_docker_registries') == ['cr1.backend.ai'], \
        'Domain allowed docker registries mismatch'


def test_delete_domain(run: ClientRunnerFunc):
    print("[ Delete domain ]")

    # Delete domain
    with closing(run(['admin', 'domain', 'purge', 'test123'])) as p:
        p.sendline('y')
        p.expect(EOF)
        assert 'Domain is deleted:' in p.before.decode(), 'Domain deletion failed'


def test_list_domain(run: ClientRunnerFunc):
    with closing(run(['--output=json', 'admin', 'domain', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get('items')
        assert isinstance(domain_list, list), 'Domain list not printed properly'


def get_domain_from_list(domains: list, name: str) -> dict:
    for domain in domains:
        if domain.get('name') == name:
            return domain
    return {}
