#!/usr/bin/env python3
"""Standalone script to rebase alembic migrations when heads are diverged.

This script allows you to rebase one migration branch onto another when
working with diverged alembic heads in a git repository.

The rebasing process follows the 4-phase approach described in SPEC.md:
1. Analysis and Validation
2. Downgrade to Common Ancestor
3. History Rewriting
4. Apply Linearized History
"""

import argparse
import asyncio
import functools
import logging
import re
import sys
from collections.abc import Callable
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from yarl import URL

logger = logging.getLogger(__name__)


class AlembicRebaseError(Exception):
    """Custom exception for alembic rebase operations."""


class AlembicRebase:
    """Main class for handling alembic migration rebasing.

    This class implements the 4-phase rebasing algorithm described in SPEC.md:
    - Phase 1: Analysis and Validation (configuration, revision validation, chain analysis)
    - Phase 2: Downgrade to Common Ancestor
    - Phase 3: History Rewriting (file modification with integrity validation)
    - Phase 4: Apply Linearized History
    """

    def __init__(self, alembic_ini_path: str | None = None) -> None:
        """Load alembic configuration from alembic.ini file.

        Part of Phase 1: Analysis and Validation.
        Parses alembic.ini to extract script_location and sqlalchemy.url,
        converts database URL to async format, and initializes alembic objects.
        """
        self.alembic_ini_path = alembic_ini_path or "alembic.ini"
        if not Path(self.alembic_ini_path).exists():
            raise AlembicRebaseError(f"Alembic config file not found: {self.alembic_ini_path}")

        # Initialize alembic config
        self.config = Config(self.alembic_ini_path)

        # Get database URL
        db_url = self.config.get_main_option("sqlalchemy.url")
        if db_url is None:
            raise AlembicRebaseError("No sqlalchemy.url found in the config file")

        # Convert sync postgres URL to async if needed
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql+psycopg2://"):
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        self.db_url = db_url
        db_url_for_logging = URL(db_url).with_password("***")
        logger.info(f"Loaded alembic config from {self.alembic_ini_path}")
        logger.info(f"Database URL: {db_url_for_logging}")

        self.script_dir = ScriptDirectory.from_config(self.config)
        logger.info(f"Script location: {self.script_dir.dir}")

        self._async_engine = None

    def _get_async_engine(self) -> AsyncEngine:
        """Get or create async engine for database operations."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(self.db_url)
        return self._async_engine

    async def _run_sync(self, func: Callable[[], None]) -> None:
        """Run alembic command APIs in async contexts."""

        @functools.wraps(func)
        def _run_sync_inner(conn: Connection) -> None:
            self.config.attributes["connection"] = conn
            match func:
                case functools.partial():
                    func_name = func.func.__name__
                case _:
                    func_name = func.__name__
            try:
                func()
            except Exception as e:
                print(f"Error while running alembic command: {func_name}(): {e!r}", file=sys.stderr)
                raise

        engine = self._get_async_engine()
        async with engine.begin() as conn:
            await conn.run_sync(_run_sync_inner)

    def _get_current_heads_from_files(self) -> list[str]:
        """Get current heads from migration files using alembic API.

        Uses alembic's ScriptDirectory to properly resolve package paths
        and get heads from migration files.
        """
        assert self.script_dir is not None, "Script directory not initialized"

        try:
            # Use alembic's built-in method to get heads
            heads = self.script_dir.get_heads()
            logger.info(f"Found {len(heads)} heads in migration files: {heads}")

            # Debug information
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Script directory: {self.script_dir.dir}")
                logger.debug(f"Version locations: {self.script_dir.version_locations}")

                # Count total revisions
                all_revisions = list(self.script_dir.walk_revisions())
                logger.debug(f"Total revisions found: {len(all_revisions)}")

                if all_revisions:
                    revision_ids = [rev.revision for rev in all_revisions]
                    logger.debug(f"All revision IDs: {sorted(revision_ids)}")

            return heads

        except Exception as e:
            logger.error(f"Error getting heads from migration files: {e}")
            logger.debug(f"Script directory path: {self.script_dir.dir}")
            return []

    def _validate_revisions(self, top_head: str, base_head: str) -> None:
        """Validate that the provided revision IDs exist and are valid for rebasing.

        Part of Phase 1: Analysis and Validation.
        Validates that both revisions exist in migration files and checks their
        relationship to current database heads.
        """
        current_heads = self._get_current_heads_from_files()

        # Check if revisions are the same
        if top_head == base_head:
            raise AlembicRebaseError("Top head and base head cannot be the same")

        # Check if revisions exist in migration files
        if not self._find_migration_file(top_head):
            raise AlembicRebaseError(
                f"Top head '{top_head}' does not exist in migration files. "
                f"Current migration file heads: {current_heads}"
            )

        if not self._find_migration_file(base_head):
            raise AlembicRebaseError(
                f"Base head '{base_head}' does not exist in migration files. "
                f"Current migration file heads: {current_heads}"
            )

        # For a rebase to make sense, we need to check the relationship between revisions
        # and current heads. The tool is designed to work with diverged migration histories.

        # Check if we have any current heads at all
        if not current_heads:
            raise AlembicRebaseError(
                "No current heads found in migration files. Please check your migration files."
            )

        # More flexible validation: At least one of the revisions should be reachable
        # from current heads or be a current head itself
        top_chain = set(self._get_migration_chain(top_head))
        base_chain = set(self._get_migration_chain(base_head))
        current_head_chains = set()

        for head in current_heads:
            current_head_chains.update(self._get_migration_chain(head))

        # Check if both revisions are reachable from current database state
        top_reachable = top_head in current_head_chains or any(
            head in top_chain for head in current_heads
        )
        base_reachable = base_head in current_head_chains or any(
            head in base_chain for head in current_heads
        )

        if not top_reachable and not base_reachable:
            raise AlembicRebaseError(
                f"Neither revision is reachable from current database state.\n"
                f"Top head '{top_head}' and base head '{base_head}' are not in the history of current file heads: {current_heads}\n"
                f"This usually means the provided revisions are not current heads in the migration files.\n"
                f"Please check your migration files and ensure the revisions are valid heads."
            )

        logger.info(f"Validation passed. Current migration file heads: {current_heads}")
        logger.info(f"Top head reachable: {top_reachable}, Base head reachable: {base_reachable}")

    def _get_migration_chain(self, revision: str) -> list[str]:
        """Get the chain of migrations leading to a specific revision.

        Part of Phase 1: Analysis and Validation.
        Builds migration chains by following down_revision links from the given
        revision back to the root, then returns the chain in chronological order.
        """
        assert self.script_dir is not None, "Script directory not initialized"

        script = self.script_dir.get_revision(revision)
        chain = []

        while script:
            chain.append(script.revision)
            if script.down_revision:
                if isinstance(script.down_revision, (list, tuple)):
                    # Handle merge points - take the first parent for simplicity
                    script = self.script_dir.get_revision(script.down_revision[0])
                else:
                    script = self.script_dir.get_revision(script.down_revision)
            else:
                break

        return list(reversed(chain))

    def _find_common_ancestor(self, top_head: str, base_head: str) -> str | None:
        """Find the common ancestor of two migration heads.

        Part of Phase 1: Analysis and Validation.
        Identifies the last migration that both branches share by comparing
        their migration chains.
        """
        top_chain = self._get_migration_chain(top_head)
        base_chain = self._get_migration_chain(base_head)

        # Convert to sets for faster lookup
        top_chain_set = set(top_chain)

        # Iterate through base_chain in reverse order to find the most recent common ancestor
        for revision in reversed(base_chain):
            if revision in top_chain_set:
                return revision

        return None

    def _find_migration_file(self, revision: str) -> Path | None:
        """Find the migration file for a given revision using alembic API."""
        assert self.script_dir is not None, "Script directory not initialized"

        try:
            # Use alembic's built-in method to get the revision
            revision_obj = self.script_dir.get_revision(revision)
            if revision_obj and revision_obj.path:
                return Path(revision_obj.path)

            logger.debug(f"Revision {revision} not found in script directory")
            return None

        except Exception as e:
            logger.debug(f"Error finding migration file for {revision}: {e}")
            return None

    def _parse_migration_file(self, file_path: Path) -> tuple[str, str | None, str]:
        """Parse migration file to extract revision, down_revision, and content."""
        content = file_path.read_text()

        # Extract revision ID
        revision_match = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
        if not revision_match:
            raise AlembicRebaseError(f"Could not find revision in {file_path}")
        revision = revision_match.group(1)

        # Extract down_revision
        down_revision_match = re.search(
            r"^down_revision\s*=\s*(['\"]([^'\"]*)['\"]|None)",
            content,
            re.MULTILINE,
        )
        down_revision = None
        if down_revision_match and down_revision_match.group(1) != "None":
            down_revision = down_revision_match.group(2)

        return revision, down_revision, content

    def _update_migration_file(
        self,
        file_path: Path,
        old_revision: str,
        new_revision: str,
        new_down_revision: str | None,
    ) -> None:
        """Update migration file with new revision IDs."""

        content = file_path.read_text()

        # Update revision
        content = re.sub(
            r"^revision\s*=\s*['\"]([^'\"]+)['\"]",
            f'revision = "{new_revision}"',
            content,
            flags=re.MULTILINE,
        )

        # Update down_revision
        if new_down_revision:
            content = re.sub(
                r"^down_revision\s*=\s*(['\"]([^'\"]*)['\"]|None)",
                f'down_revision = "{new_down_revision}"',
                content,
                flags=re.MULTILINE,
            )
        else:
            content = re.sub(
                r"^down_revision\s*=\s*(['\"]([^'\"]*)['\"]|None)",
                "down_revision = None",
                content,
                flags=re.MULTILINE,
            )

        # Write updated content back to the same file (revision ID unchanged)
        file_path.write_text(content)

        logger.info(f"Updated migration file linkage: {file_path.name}")

    def _rewrite_migration_files(
        self, migrations_to_rebase: list[str], last_base_migration: str
    ) -> None:
        """Update migration files to reflect new parent relationships after rebase.

        Part of Phase 3: History Rewriting.
        Modifies migration files to reflect the new linearized revision history
        by updating down_revision fields while preserving all other content.
        """
        logger.info("Updating migration file linkage for rebase...")

        # Update migration files (keeping original revision IDs)
        for i, revision in enumerate(migrations_to_rebase):
            file_path = self._find_migration_file(revision)
            if not file_path:
                raise AlembicRebaseError(f"Could not find migration file for revision {revision}")

            # Determine new down_revision
            if i == 0:
                # First migration in rebase should point to last_base_migration
                new_down_revision = last_base_migration
            else:
                # Subsequent migrations point to previous migration in the rebased chain
                new_down_revision = migrations_to_rebase[i - 1]

            # Update only the down_revision, keep original revision ID
            self._update_migration_file(file_path, revision, revision, new_down_revision)

    def _validate_migration_file_integrity(self, revision: str) -> bool:
        """Validate that a migration file has proper structure and syntax.

        Part of Phase 3: History Rewriting - Integrity Validation.
        Validates Python syntax and ensures all required alembic elements are present.
        """
        file_path = self._find_migration_file(revision)
        if not file_path:
            return False

        try:
            content = file_path.read_text()

            # Check for required elements
            required_patterns = [
                r"^revision\s*=\s*['\"][^'\"]+['\"]",  # revision = 'xxx'
                r"^down_revision\s*=\s*(['\"][^'\"]*['\"]|None)",  # down_revision = 'xxx' or None
                r"def upgrade\(\)",  # upgrade function
                r"def downgrade\(\)",  # downgrade function
            ]

            for pattern in required_patterns:
                if not re.search(pattern, content, re.MULTILINE):
                    logger.error(f"Migration file {file_path} missing required pattern: {pattern}")
                    return False

            # Try to compile the Python code
            compile(content, str(file_path), "exec")

            return True

        except Exception as e:
            logger.error(f"Migration file {file_path} validation failed: {e}")
            return False

    def _validate_migration_chain_integrity(self, migrations: list[str]) -> bool:
        """Validate that the migration chain has proper linkage.

        Part of Phase 3: History Rewriting - Integrity Validation.
        Verifies migration chain linkage is correct and there is only a single
        head revision in the history.
        """
        for i, revision in enumerate(migrations):
            file_path = self._find_migration_file(revision)
            if not file_path:
                logger.error(f"Migration file not found for revision: {revision}")
                return False

            _, down_revision, _ = self._parse_migration_file(file_path)

            if i == 0:
                # First migration can have any down_revision
                continue
            # Subsequent migrations should point to previous migration
            expected_down_revision = migrations[i - 1]
            if down_revision != expected_down_revision:
                logger.error(
                    f"Migration chain broken: {revision} points to {down_revision}, expected {expected_down_revision}"
                )
                return False

        return True

    async def _downgrade_to_revision(self, revision: str) -> None:
        """Downgrade database to a specific revision.

        Part of Phase 2: Downgrade to Common Ancestor.
        Uses alembic to downgrade database to the common ancestor revision,
        removing all migrations from both diverged branches.
        """
        logger.info(f"Downgrading to revision: {revision}")
        await self._run_sync(functools.partial(command.downgrade, self.config, revision))

    async def _upgrade_to_head(self, head: str) -> None:
        """Upgrade database to a specific head.

        Part of Phase 4: Apply Linearized History.
        Runs the regular alembic upgrade procedure using the new history chain.
        """
        logger.info(f"Upgrading to head: {head}")
        await self._run_sync(functools.partial(command.upgrade, self.config, head))

    def _print_dry_run_analysis(
        self,
        base_head: str,
        top_head: str,
        common_ancestor: str,
        migrations_to_rebase: list[str],
        last_base_migration: str,
    ) -> None:
        """Print detailed analysis results for dry-run mode."""
        print("\n" + "=" * 60)
        print("DRY RUN - Migration Rebase Analysis")
        print("=" * 60)
        print(f"Base head (to be ancestor): {base_head}")
        print(f"Top head (to be descendat): {top_head}")
        print(f"Common ancestor:            {common_ancestor}")
        print()

        print("Migrations to rebase:")
        for i, migration in enumerate(migrations_to_rebase, 1):
            print(f"  {i}. {migration}")
        print()

        print("Planned history after rebase:")
        print("  Current base chain will remain:")
        top_chain = self._get_migration_chain(base_head)
        for i, migration in enumerate(top_chain, 1):
            if migration == common_ancestor:
                print(f"    {i}. {migration} (common ancestor)")
            else:
                print(f"    {i}. {migration}")

        print("  Rebased migrations will be appended:")
        for i, migration in enumerate(migrations_to_rebase, len(top_chain) + 1):
            print(f"    {i}. {migration} (rebased)")
        print()

        print("Migration file changes that would be made:")
        for i, revision in enumerate(migrations_to_rebase):
            new_down_rev = last_base_migration if i == 0 else migrations_to_rebase[i - 1]

            file_path = self._find_migration_file(revision)
            if file_path:
                _, current_down_rev, _ = self._parse_migration_file(file_path)
                if current_down_rev != new_down_rev:
                    print(f"  {file_path.name}:")
                    print(f"    down_revision: {current_down_rev} → {new_down_rev}")
        print()

        print("Database operations that would be performed:")
        if len(migrations_to_rebase) == 1:
            print(f"  1. Downgrade to: {common_ancestor} (rolling back {migrations_to_rebase[0]})")
        else:
            print(
                f"  1. Downgrade to: {common_ancestor} (rolling back {migrations_to_rebase[0]}..{migrations_to_rebase[-1]})"
            )
        print(f"  2. Upgrade to: ..{base_head}")
        print(f"  3. Upgrade to: ..{top_head}")
        print()
        print("=" * 60)
        print("DRY RUN COMPLETE - No actual changes were made")
        print("=" * 60)

    async def rebase(self, base_head: str, top_head: str, dry_run: bool = False) -> None:
        """Rebase migrations by putting base_head below top_head in history.

        The rebasing process consists of four main phases:
        1. Analysis and Validation
        2. Downgrade to Common Ancestor
        3. History Rewriting
        4. Apply Linearized History

        Args:
            base_head: The revision that will be moved below top_head
            top_head: The revision that will remain at the top

        """
        logger.info(f"Starting rebase: base_head={base_head}, top_head={top_head}")

        # === Phase 1: Analysis and Validation ===
        logger.info("Phase 1: Analysis and Validation")

        # Revision Validation
        self._validate_revisions(top_head, base_head)

        # Chain Analysis
        common_ancestor = self._find_common_ancestor(top_head, base_head)
        if not common_ancestor:
            raise AlembicRebaseError("No common ancestor found between the two heads")

        logger.info(f"Common ancestor: {common_ancestor}")

        # Get the migrations to rebase (from base_head back to common ancestor)
        base_chain = self._get_migration_chain(base_head)
        top_chain = self._get_migration_chain(top_head)

        # Find where the base chain diverged from top
        common_index = None
        for i, rev in enumerate(top_chain):
            if rev == common_ancestor:
                common_index = i
                break

        if common_index is None:
            raise AlembicRebaseError("Could not find common ancestor in base chain")

        migrations_to_rebase = top_chain[common_index + 1 :]
        logger.info(f"Migrations to rebase: {migrations_to_rebase}")

        # Find the rebasing point
        # Get the revision ID of the last migration in the top_head chain after the common ancestor
        base_chain_after_ancestor = [rev for rev in base_chain if rev != common_ancestor]
        if not base_chain_after_ancestor:
            raise AlembicRebaseError("No migrations found in top chain after common ancestor")

        # Get the last migration in the top chain after the common ancestor
        last_base_migration = base_chain_after_ancestor[-1]

        # === DRY RUN MODE ===
        if dry_run:
            logger.info("DRY RUN MODE: Printing analysis results without making changes")
            self._print_dry_run_analysis(
                base_head,
                top_head,
                common_ancestor,
                migrations_to_rebase,
                last_base_migration,
            )
            return

        # === Phase 2: Downgrade to Common Ancestor ===
        logger.info("Phase 2: Downgrade to Common Ancestor")
        await self._downgrade_to_revision(common_ancestor)

        # === Phase 3: History Rewriting ===
        logger.info("Phase 3: History Rewriting")

        # File Rewriting - update migration file linkage for rebase
        self._rewrite_migration_files(migrations_to_rebase, last_base_migration)

        # Integrity Validation
        logger.info("Validating migration file integrity after rebase...")
        for revision in migrations_to_rebase:
            if not self._validate_migration_file_integrity(revision):
                raise AlembicRebaseError(
                    f"Migration file integrity validation failed for {revision}"
                )

        # Validate migration chain integrity (with updated linkage)
        if not self._validate_migration_chain_integrity(migrations_to_rebase):
            raise AlembicRebaseError("Migration chain integrity validation failed")

        logger.info("Migration file integrity validation passed")

        # === Phase 4: Apply Linearized History ===
        logger.info("Phase 4: Apply Linearized History")

        # Apply rebased migrations
        await self._upgrade_to_head(top_head)  # implies base_head

        logger.info("Rebase completed successfully!")


async def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Rebase alembic migrations when heads are diverged",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1000a1b2c3d4e5 2000f6e7d8c9ba
  %(prog)s -f ./configs/alembic.ini 1000a1b2c3d4e5 2000f6e7d8c9ba
  %(prog)s --config ./configs/alembic.ini 1000a1b2c3d4e5 2000f6e7d8c9ba
        """,
    )
    parser.add_argument(
        "base_head",
        help="The revision ID that will be moved below the top head",
    )
    parser.add_argument(
        "top_head",
        help="The revision ID that will remain at the top of the history",
    )
    parser.add_argument(
        "-f",
        "--config",
        default="alembic.ini",
        help="Path to alembic.ini file (default: alembic.ini)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform analysis without executing database migrations (dry run mode)",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        rebase = AlembicRebase(args.config)
        await rebase.rebase(args.base_head, args.top_head, args.dry_run)
    except AlembicRebaseError as e:
        logger.error(f"Rebase failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
