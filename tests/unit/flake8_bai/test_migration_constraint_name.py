from collections.abc import Callable

import pytest

type Lint = Callable[[str, str], list[tuple[int, str]]]

MIGRATION_FILE = "src/ai/backend/manager/models/alembic/versions/a1b2c3d4e5f6_add_keys.py"

UNRELEASED_HEADER = 'revision = "a1b2c3d4e5f6"  # Part of: NEXT_RELEASE_VERSION\n'
RELEASED_HEADER = 'revision = "a1b2c3d4e5f6"  # Part of: 26.9.0\n'


class TestMigrationConstraintNameRule:
    @pytest.mark.parametrize(
        "call",
        [
            'op.create_foreign_key("fk_keys_user_id_users", "keys", "users", ["user_id"], ["uuid"])',
            'op.create_unique_constraint("uq_keys_name", "keys", ["name"])',
            'op.create_index("ix_keys_name", "keys", ["name"])',
            'op.create_primary_key("pk_keys", "keys", ["id"])',
            'op.create_check_constraint("ck_keys_positive", "keys", "size > 0")',
            'op.create_index(index_name="ix_keys_name", table_name="keys", columns=["name"])',
        ],
    )
    def test_bare_convention_name_fails(self, lint: Lint, call: str) -> None:
        assert lint(MIGRATION_FILE, f"{UNRELEASED_HEADER}{call}\n") == [(2, "BAI303")]

    @pytest.mark.parametrize(
        "constraint",
        [
            'sa.ForeignKeyConstraint(["user_id"], ["users.uuid"], name="fk_keys_user_id_users")',
            'sa.UniqueConstraint("name", name="uq_keys_name")',
            'sa.PrimaryKeyConstraint("id", name="pk_keys")',
            'sa.CheckConstraint("size > 0", name="ck_keys_positive")',
            'sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.uuid", name="fk_keys_user_id_users"))',
        ],
    )
    def test_bare_convention_name_in_create_table_fails(self, lint: Lint, constraint: str) -> None:
        source = f'{UNRELEASED_HEADER}op.create_table(\n    "keys",\n    {constraint},\n)\n'
        assert lint(MIGRATION_FILE, source) == [(4, "BAI303")]

    def test_wrapped_convention_name_passes(self, lint: Lint) -> None:
        source = f"""{UNRELEASED_HEADER}op.create_index(op.f("ix_keys_name"), "keys", ["name"])
op.create_table("keys", sa.PrimaryKeyConstraint("id", name=op.f("pk_keys")))
"""
        assert lint(MIGRATION_FILE, source) == []

    @pytest.mark.parametrize(
        "call",
        [
            'op.create_index("ix_keys_name_owner", "keys", ["name", "owner"])',
            'op.create_unique_constraint("uq_keys_owner", "keys", ["name", "owner"])',
            'op.create_foreign_key("fk_keys_owner", "keys", "users", ["user_id"], ["uuid"])',
        ],
    )
    def test_explicit_name_other_than_convention_passes(self, lint: Lint, call: str) -> None:
        assert lint(MIGRATION_FILE, f"{UNRELEASED_HEADER}{call}\n") == []

    def test_drop_passes(self, lint: Lint) -> None:
        source = f'{UNRELEASED_HEADER}op.drop_constraint("pk_keys", "keys", type_="primary")\n'
        assert lint(MIGRATION_FILE, source) == []

    def test_released_migration_passes(self, lint: Lint) -> None:
        source = f'{RELEASED_HEADER}op.create_index("ix_keys_name", "keys", ["name"])\n'
        assert lint(MIGRATION_FILE, source) == []

    def test_file_outside_versions_passes(self, lint: Lint) -> None:
        source = f'{UNRELEASED_HEADER}op.create_index("ix_keys_name", "keys", ["name"])\n'
        assert lint("src/ai/backend/manager/models/alembic/table_rebuild.py", source) == []
