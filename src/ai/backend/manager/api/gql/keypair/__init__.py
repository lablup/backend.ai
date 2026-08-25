"""Keypair GraphQL API package."""

from .resolver import (
    admin_create_keypair_v2,
    admin_delete_keypair_v2,
    admin_delete_ssh_keypair_v2,
    admin_keypair_v2,
    admin_keypairs_v2,
    admin_register_ssh_keypair_v2,
    admin_ssh_keypair_v2,
    admin_update_keypair_v2,
    issue_my_keypair,
    my_keypairs,
    revoke_my_keypair,
    switch_my_main_access_key,
    update_my_keypair,
)

__all__ = [
    "admin_create_keypair_v2",
    "admin_delete_keypair_v2",
    "admin_delete_ssh_keypair_v2",
    "admin_keypair_v2",
    "admin_keypairs_v2",
    "admin_register_ssh_keypair_v2",
    "admin_ssh_keypair_v2",
    "admin_update_keypair_v2",
    "issue_my_keypair",
    "my_keypairs",
    "revoke_my_keypair",
    "switch_my_main_access_key",
    "update_my_keypair",
]
