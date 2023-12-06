import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_domain(run_admin: ClientRunnerFunc):
    print("[ Add domain ]")

    vfolder_host_perms_obj = {
        "local:volume1": [
            "create-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
        ]
    }
    # Add domain
    add_arguments = [
        "--output=json",
        "admin",
        "domain",
        "add",
        "-d",
        "Test domain",
        "--inactive",
        "--total-resource-slots",
        "{}",
        "--vfolder-host-perms",
        f"{json.dumps(vfolder_host_perms_obj)}",
        "--allowed-docker-registries",
        "cr.backend.ai",
        "test",
    ]
    with closing(run_admin(add_arguments)) as p:
        p.expect(EOF)
        response = json.loads(p.before.decode())
        assert response.get("ok") is True, "Domain creation not successful"

    # Check if domain is added
    with closing(run_admin(["--output=json", "admin", "domain", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get("items")
        assert isinstance(domain_list, list), "Domain list not printed properly"

    test_domain = get_domain_from_list(domain_list, "test")

    allowed_vfolder_hosts_str = str(test_domain.get("allowed_vfolder_hosts"))
    allowed_vfolder_hosts_json = json.loads(allowed_vfolder_hosts_str)

    assert bool(test_domain), "Test domain doesn't exist"
    assert test_domain.get("description") == "Test domain", "Domain description mismatch"
    assert test_domain.get("is_active") is False, "Domain active status mismatch"
    assert test_domain.get("total_resource_slots") == {}, "Domain total resource slots mismatch"
    assert allowed_vfolder_hosts_json.get("local:volume1")
    assert set(allowed_vfolder_hosts_json.get("local:volume1")) == set(
        vfolder_host_perms_obj.get("local:volume1")
    )
    "Domain allowed vfolder hosts mismatch"
    assert test_domain.get("allowed_docker_registries") == [
        "cr.backend.ai"
    ], "Domain allowed docker registries mismatch"


def test_update_domain(run_admin: ClientRunnerFunc):
    print("[ Update domain ]")

    # vfolder
    vfolder_host_perms_obj = {
        "local:volume2": [
            "create-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
        ]
    }

    # Update domain
    add_arguments = [
        "--output=json",
        "admin",
        "domain",
        "update",
        "--new-name",
        "test123",
        "--description",
        "Test domain updated",
        "--is-active",
        "TRUE",
        "--total-resource-slots",
        "{}",
        "--vfolder-host-perms",
        f"{json.dumps(vfolder_host_perms_obj)}",
        "--allowed-docker-registries",
        "cr1.backend.ai",
        "test",
    ]
    with closing(run_admin(add_arguments)) as p:
        p.expect(EOF)
        response = json.loads(p.before.decode())
        assert response.get("ok") is True, "Domain update not successful"

    # Check if domain is updated
    with closing(run_admin(["--output=json", "admin", "domain", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get("items")
        assert isinstance(domain_list, list), "Domain list not printed properly"

    test_domain = get_domain_from_list(domain_list, "test123")

    allowed_vfolder_hosts_str = str(test_domain.get("allowed_vfolder_hosts"))
    allowed_vfolder_hosts_json = json.loads(allowed_vfolder_hosts_str)

    assert bool(test_domain), "Test domain doesn't exist"
    assert test_domain.get("description") == "Test domain updated", "Domain description mismatch"
    assert test_domain.get("is_active") is True, "Domain active status mismatch"
    assert test_domain.get("total_resource_slots") == {}, "Domain total resource slots mismatch"
    assert allowed_vfolder_hosts_json.get("local:volume2")
    assert set(allowed_vfolder_hosts_json.get("local:volume2")) == set(
        vfolder_host_perms_obj.get("local:volume2")
    ), "Domain allowed vfolder hosts mismatch"
    assert test_domain.get("allowed_docker_registries") == [
        "cr1.backend.ai"
    ], "Domain allowed docker registries mismatch"


def test_delete_domain(run_admin: ClientRunnerFunc):
    print("[ Delete domain ]")

    # Delete domain
    with closing(run_admin(["--output=json", "admin", "domain", "purge", "test123"])) as p:
        p.sendline("y")
        p.expect(EOF)
        before = p.before.decode()
        response = json.loads(before[before.index("{") :])
        assert response.get("ok") is True, "Domain deletion failed"


def test_list_domain(run_admin: ClientRunnerFunc):
    with closing(run_admin(["--output=json", "admin", "domain", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        domain_list = loaded.get("items")
        assert isinstance(domain_list, list), "Domain list not printed properly"


def get_domain_from_list(domains: list, name: str) -> dict:
    for domain in domains:
        if domain.get("name") == name:
            return domain
    return {}
