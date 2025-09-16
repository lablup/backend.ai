import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc, decode


def test_add_keypair_resource_policy(run_admin: ClientRunnerFunc, keypair_resource_policy: str):
    print("[ Add keypair resource policy ]")

    vfolder_volume_name = "local:volume1"
    vfolder_host_perms_obj = {
        vfolder_volume_name: [
            "create-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
        ]
    }

    # Add keypair resource policy
    add_arguments = [
        "--output=json",
        "admin",
        "keypair-resource-policy",
        "add",
        "--default-for-unspecified",
        "LIMITED",
        "--total-resource-slots",
        "{}",
        "--max-concurrent-sessions",
        "20",
        "--max-containers-per-session",
        "2",
        "--vfolder-host-perms",
        f"{json.dumps(vfolder_host_perms_obj)}",
        "--idle-timeout",
        "1200",
        keypair_resource_policy,
    ]
    with closing(run_admin(add_arguments)) as p:
        p.expect(EOF)
        response = json.loads(decode(p.before))
        assert response.get("ok") is True, "Keypair resource policy creation not successful"

    # Check if keypair resource policy is created
    with closing(run_admin(["--output=json", "admin", "keypair-resource-policy", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        krp_list = loaded.get("items")
        assert isinstance(krp_list, list), "Keypair resource policy list not printed properly"

    test_krp = get_keypair_resource_policy_from_list(krp_list, keypair_resource_policy)
    allowed_vfolder_hosts_str = str(test_krp.get("allowed_vfolder_hosts"))
    allowed_vfolder_hosts_json = json.loads(allowed_vfolder_hosts_str)

    assert bool(test_krp), "Test keypair resource policy doesn't exist"
    assert test_krp.get("total_resource_slots") == "{}", (
        "Test keypair resource policy total resource slot mismatch"
    )
    assert test_krp.get("max_concurrent_sessions") == 20, (
        "Test keypair resource policy max concurrent session mismatch"
    )
    assert test_krp.get("idle_timeout") == 1200, (
        "Test keypair resource policy idle timeout mismatch"
    )
    assert test_krp.get("max_containers_per_session") == 2, (
        "Test keypair resouce policy max containers per session mismatch"
    )

    assert vfolder_volume_name in allowed_vfolder_hosts_json, (
        f"allowed_vfolder_hosts_json {vfolder_volume_name} is None"
    )
    assert vfolder_volume_name in vfolder_host_perms_obj, (
        f"vfolder_host_perms_obj {vfolder_volume_name} is None"
    )

    assert set(allowed_vfolder_hosts_json[vfolder_volume_name]) == set(
        vfolder_host_perms_obj[vfolder_volume_name]
    ), "Test keypair resource policy allowed vfolder hosts mismatch"


def test_update_keypair_resource_policy(run_admin: ClientRunnerFunc, keypair_resource_policy: str):
    print("[ Update keypair resource policy ]")

    vfolder_volume_name = "local:volume2"
    vfolder_host_perms_obj = {
        vfolder_volume_name: [
            "create-vfolder",
            "delete-vfolder",
            "mount-in-session",
            "upload-file",
            "download-file",
        ]
    }

    # Update keypair resource policy
    add_arguments = [
        "--output=json",
        "admin",
        "keypair-resource-policy",
        "update",
        "--default-for-unspecified",
        "UNLIMITED",
        "--total-resource-slots",
        "{}",
        "--max-concurrent-sessions",
        "30",
        "--max-containers-per-session",
        "1",
        "--vfolder-host-perms",
        f"{json.dumps(vfolder_host_perms_obj)}",
        "--idle-timeout",
        "1800",
        keypair_resource_policy,
    ]
    with closing(run_admin(add_arguments)) as p:
        p.expect(EOF)
        response = json.loads(decode(p.before))
        assert response.get("ok") is True, "Keypair resource policy update not successful"

    # Check if keypair resource policy is updated
    with closing(run_admin(["--output=json", "admin", "keypair-resource-policy", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        krp_list = loaded.get("items")
        assert isinstance(krp_list, list), "Keypair resource policy list not printed properly"

    test_krp = get_keypair_resource_policy_from_list(krp_list, keypair_resource_policy)
    allowed_vfolder_hosts_str = str(test_krp.get("allowed_vfolder_hosts"))
    allowed_vfolder_hosts_json = json.loads(allowed_vfolder_hosts_str)

    assert bool(test_krp), "Test keypair resource policy doesn't exist"
    assert test_krp.get("total_resource_slots") == "{}", (
        "Test keypair resource policy total resource slot mismatch"
    )
    assert test_krp.get("max_concurrent_sessions") == 30, (
        "Test keypair resource policy max concurrent session mismatch"
    )
    assert test_krp.get("idle_timeout") == 1800, (
        "Test keypair resource policy idle timeout mismatch"
    )
    assert test_krp.get("max_containers_per_session") == 1, (
        "Test keypair resouce policy max containers per session mismatch"
    )

    assert vfolder_volume_name in allowed_vfolder_hosts_json, (
        f"allowed_vfolder_hosts_json {vfolder_volume_name} is None"
    )
    assert vfolder_volume_name in vfolder_host_perms_obj, (
        f"vfolder_host_perms_obj {vfolder_volume_name} is None"
    )
    assert set(allowed_vfolder_hosts_json[vfolder_volume_name]) == set(
        vfolder_host_perms_obj[vfolder_volume_name]
    ), "Test keypair resource policy allowed vfolder hosts mismatch"


def test_delete_keypair_resource_policy(run_admin: ClientRunnerFunc, keypair_resource_policy: str):
    print("[ Delete keypair resource policy ]")

    # Delete keypair resource policy
    with closing(
        run_admin([
            "--output=json",
            "admin",
            "keypair-resource-policy",
            "delete",
            keypair_resource_policy,
        ])
    ) as p:
        p.sendline("y")
        p.expect(EOF)
        before = decode(p.before)
        response = json.loads(before[before.index("{") :])
        assert response.get("ok") is True, "Keypair resource policy deletion failed"


def test_list_keypair_resource_policy(run_admin: ClientRunnerFunc):
    print("[ List keypair resource policy ]")
    with closing(run_admin(["--output=json", "admin", "keypair-resource-policy", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        krp_list = loaded.get("items")
        assert isinstance(krp_list, list), "Keypair resource policy list not printed properly"


def get_keypair_resource_policy_from_list(krps: list, name: str) -> dict:
    for krp in krps:
        if krp.get("name") == name:
            return krp
    return {}
