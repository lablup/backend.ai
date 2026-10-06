python_tests(
    dependencies=[
        # The kind catalog is a runtime scan of the entity package, which dependency
        # inference cannot see. Without this the sandbox holds only part of it.
        "src/ai/backend/common:src",
        # `ensure_all_tables_registered` imports every model by name.
        "src/ai/backend/manager:src",
        # The generated fixture and the account fixtures it is rendered from.
        "fixtures/manager:json",
        "src/ai/backend/install:resources",
        # The revisions are read by path: `versions/` is not a package, so nothing infers
        # them.
        "src/ai/backend/manager/models/alembic/versions/f4a1c9d20b73_sync_seed_roles_with_their_declaration.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/dc61fa027fc1_assign_every_user_their_user_owner_role.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/e7d2a9c41b60_assign_every_user_their_domain_member_role.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/a0f597deb5e5_grant_project_members_read_on_their_project.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/c4a71e0d5b38_grant_domain_members_read_on_their_domain.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/a3f60d2b7c19_grant_domain_members_read_on_resource_presets.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/c3e8a1f05b27_add_preset_scope_and_public_member_role.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/a1f6b7c4d902_grant_image_and_project_reads_to_members.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/b8e0c1f4a276_grant_seed_roles_read_on_their_own_policy.py:../../../src",
    ],
)
