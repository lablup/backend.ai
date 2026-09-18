from __future__ import annotations

import asyncio
import dataclasses
import enum
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import click
from tabulate import tabulate

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.registry.types import WiredProcessor
from ai.backend.manager.actions.types import ActionGate
from ai.backend.manager.cli.role_fixture import RoleFixture
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.seed.check import RoleSeedChecker
from ai.backend.manager.data.permission.seed.kinds import PermissionKinds
from ai.backend.manager.data.permission.seed.loader import RoleSeedLoader
from ai.backend.manager.data.permission.seed.role import RoleSeed
from ai.backend.manager.services.catalog import load_wiring_catalog

if TYPE_CHECKING:
    from ai.backend.manager.cli.context import CLIContext

# The letters a mask prints as, in the order a cell spells them.
_LETTERS: Final[tuple[tuple[Permission, str], ...]] = (
    (Permission.READ, "R"),
    (Permission.UPDATE, "U"),
    (Permission.CREATE, "C"),
    (Permission.SOFT_DELETE, "S"),
    (Permission.HARD_DELETE, "H"),
)
_LEGEND: Final[str] = "R read  U update  C create  S soft-delete  H hard-delete"
# Stands for a column a wiring leaves unset, so every line has the same shape.
_ABSENT: Final[str] = "-"
# The entity type of a global operation, which the superadmin gate covers.
_GLOBAL: Final[str] = "global"
_OPERATION_COLUMNS: Final[tuple[str, ...]] = (
    "entity_type",
    "field_type",
    "action_name",
    "required",
    "held",
    "verdict",
)


def _cell(mask: Permission) -> str:
    return "".join(letter if mask & bit else "_" for bit, letter in _LETTERS)


class Verdict(enum.StrEnum):
    """The result of reading one wired operation against a role's grant."""

    ALLOWED = "allowed"
    DENIED = "denied"
    ANYONE = "anyone"
    SUPERADMIN = "superadmin"
    RUNTIME = "runtime"

    def describe(self) -> str:
        match self:
            case Verdict.ALLOWED:
                return "the role holds the mask the operation requires"
            case Verdict.DENIED:
                return "the role is short of the mask the operation requires"
            case Verdict.ANYONE:
                return "the operation requires no permission"
            case Verdict.SUPERADMIN:
                return "the operation is behind the superadmin gate"
            case Verdict.RUNTIME:
                return "the operation resolves its target at run time"


@dataclasses.dataclass(frozen=True)
class OperationReading:
    """One wired operation, read against one role."""

    entity_type: str
    field_type: str
    action_name: str
    required: Permission
    held: Permission
    verdict: Verdict

    def values(self) -> tuple[str, ...]:
        return (
            self.entity_type,
            self.field_type,
            self.action_name,
            _cell(self.required),
            _cell(self.held),
            str(self.verdict),
        )


class RoleOperations:
    """Reads the wiring catalog against one role's grant.

    A permission-gated operation requires a mask on the entity it names; a field
    operation requires it on the entity owning the row. Not covered, because they are
    resolved at run time: whether the role's scope governs the target, object
    permissions, and shares.
    """

    _seed: RoleSeed
    _catalog: Sequence[WiredProcessor]

    def __init__(self, seed: RoleSeed, catalog: Sequence[WiredProcessor]) -> None:
        self._seed = seed
        self._catalog = catalog

    def readings(self) -> list[OperationReading]:
        readings = [self._read(wiring) for wiring in self._catalog]
        readings.sort(key=lambda reading: (reading.entity_type, reading.action_name))
        return readings

    def _read(self, wiring: WiredProcessor) -> OperationReading:
        entity_type = str(wiring.entity_type) if wiring.entity_type is not None else _ABSENT
        field_type = str(wiring.field_type) if wiring.field_type is not None else _ABSENT
        required = wiring.action_cls.operation_type().to_permission()
        held = self._seed.permissions.get(entity_type, Permission.NONE)
        return OperationReading(
            entity_type=entity_type,
            field_type=field_type,
            action_name=wiring.action_cls.action_name(),
            required=required,
            held=held,
            verdict=self._verdict(wiring, entity_type, required, held),
        )

    def _verdict(
        self, wiring: WiredProcessor, entity_type: str, required: Permission, held: Permission
    ) -> Verdict:
        if wiring.gate is not ActionGate.PERMISSION:
            return Verdict.ANYONE
        if wiring.entity_type is None:
            return Verdict.RUNTIME
        if entity_type == _GLOBAL:
            return Verdict.SUPERADMIN
        return Verdict.ALLOWED if held.covers(required) else Verdict.DENIED


def _load() -> list[RoleSeed]:
    return RoleSeedLoader().load()


def _column(seed: RoleSeed) -> str:
    """The role's column header, naming the scope a scoped role is created in."""
    return seed.name if seed.scope is None else f"{seed.name}@{seed.scope}"


def _rows(seeds: Sequence[RoleSeed], entity: str | None, granted_only: bool) -> list[str]:
    kinds = sorted({kind for seed in seeds for kind in seed.permissions})
    if entity is not None:
        kinds = [kind for kind in kinds if kind == entity]
    if granted_only:
        kinds = [kind for kind in kinds if any(seed.permissions.get(kind) for seed in seeds)]
    return kinds


@click.group()
def cli() -> None:
    """Command set for the seed role declaration."""


@cli.command(name="show")
@click.option("--role", default=None, help="Keep only this role's column.")
@click.option("--entity", default=None, help="Keep only this kind's row.")
@click.option("--granted-only", is_flag=True, help="Drop the rows no role is granted.")
@click.option(
    "-o",
    "--output",
    default="table",
    type=click.Choice(["table", "json", "tsv"]),
    help="Set the output style of the command results.",
)
def show(role: str | None, entity: str | None, granted_only: bool, output: str) -> None:
    """
    Print the seed roles as a grid: one row per kind, one column per role.

    The role files are the declaration; this prints them side by side, which is where
    two roles are compared. A role created in one named scope is headed `name@scope`.

    Examples:

        $ backend.ai mgr permissions show --granted-only
    """
    seeds = _load()
    if role is not None:
        seeds = [seed for seed in seeds if seed.name == role]
        if not seeds:
            raise click.ClickException(f"No role is named {role}.")
    kinds = _rows(seeds, entity, granted_only)
    match output:
        case "json":
            print(
                json.dumps(
                    [
                        {
                            "entity_type": kind,
                            **{
                                _column(seed): _cell(seed.permissions.get(kind, Permission.NONE))
                                for seed in seeds
                            },
                        }
                        for kind in kinds
                    ],
                    indent=2,
                )
            )
        case "tsv":
            print("\t".join(["entity_type", *(_column(seed) for seed in seeds)]))
            for kind in kinds:
                cells = (_cell(seed.permissions.get(kind, Permission.NONE)) for seed in seeds)
                print("\t".join([kind, *cells]))
        case _:
            width = max((len(kind) for kind in kinds), default=0)
            width = max(width, len("entity type"))
            header = "  ".join(_column(seed) for seed in seeds)
            print(f"{'entity type':<{width}}  {header}")
            for kind in kinds:
                row = "  ".join(
                    _cell(seed.permissions.get(kind, Permission.NONE)).ljust(len(_column(seed)))
                    for seed in seeds
                )
                print(f"{kind:<{width}}  {row}")
            print()
            print(_LEGEND)
            granted = sum(1 for kind in kinds if any(seed.permissions.get(kind) for seed in seeds))
            print(f"{len(kinds)} kinds x {len(seeds)} roles, {granted} granted")


@cli.command(name="check")
def check() -> None:
    """
    Compare the role files with the entity types this build defines.

    Every role states every entity type, with an empty list where it is granted nothing.
    A type left out, a name that is no entity type, or a member holding what its admin
    does not, is reported and fails the command.

    Examples:

        $ backend.ai mgr permissions check
    """
    kinds = PermissionKinds()
    findings = RoleSeedChecker(kinds, _load()).findings()
    print(f"{len(kinds.declared())} entity types stated by each role.")
    if not findings:
        print("The declaration answers for every kind.")
        return
    print()
    for finding in findings:
        print(finding.render())
    raise SystemExit(len(findings))


@cli.command(name="operations")
@click.argument("role")
@click.option(
    "--verdict",
    default=None,
    type=click.Choice([verdict.value for verdict in Verdict]),
    help="Keep only the operations read this way.",
)
@click.option("--entity", default=None, help="Keep only the operations on this entity type.")
@click.option(
    "-o",
    "--output",
    default="table",
    type=click.Choice(["table", "json", "tsv"]),
    help="Set the output style of the command results.",
)
def operations(role: str, verdict: str | None, entity: str | None, output: str) -> None:
    """
    Read every wired operation against ROLE's grant.

    A permission-gated operation requires a mask on the entity it names, and a field
    operation requires it on the entity owning the row. Not covered: whether the role's
    scope governs the target, object permissions, shares, and any processor still wired
    outside the registry.

    Examples:

    \b
      $ backend.ai mgr permissions operations project_member --verdict denied
      $ backend.ai mgr permissions operations domain_admin --entity vfolder
    """
    seeds = [seed for seed in _load() if seed.name == role]
    if not seeds:
        raise click.ClickException(f"No role is named {role}.")
    catalog = asyncio.run(load_wiring_catalog())
    readings = RoleOperations(seeds[0], catalog).readings()
    if verdict is not None:
        readings = [reading for reading in readings if reading.verdict == verdict]
    if entity is not None:
        readings = [reading for reading in readings if reading.entity_type == entity]
    match output:
        case "json":
            print(
                json.dumps(
                    [
                        dict(zip(_OPERATION_COLUMNS, reading.values(), strict=True))
                        for reading in readings
                    ],
                    indent=2,
                )
            )
        case "tsv":
            print("\t".join(_OPERATION_COLUMNS))
            for reading in readings:
                print("\t".join(reading.values()))
        case _:
            print(tabulate([reading.values() for reading in readings], headers=_OPERATION_COLUMNS))
            print()
            print(_LEGEND)
            counted = Counter(reading.verdict for reading in readings)
            for member in Verdict:
                if counted[member]:
                    print(f"{counted[member]:5d} {member:<11} {member.describe()}")
            print(f"{len(readings)} operations read against {role}")


# The checkout this command writes the seed to.
_REPOSITORY: Final[Path] = Path(__file__).resolve().parents[5]
# The installer fixture of the same name is a symlink to this one.
_PRESETS_TARGET: Final[Path] = Path("fixtures/manager/example-role-presets.json")


def _render(seeds: Sequence[RoleSeed]) -> dict[Path, dict[str, Any]]:
    return {_PRESETS_TARGET: RoleFixture(seeds).render_presets()}


@cli.command(name="emit")
@click.option(
    "--repository",
    default=None,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Write the seed into this checkout.",
)
@click.option("--check", is_flag=True, help="Report whether the files are current, write nothing.")
def emit(repository: Path | None, check: bool) -> None:
    """
    Write the preset fixture from the role files.

    The written file is generated: edit the role files and run this, never the JSON.
    The roles the presets call for are created in each scope by `provision`.

    Examples:

    \b
      $ backend.ai mgr permissions emit
      $ backend.ai mgr permissions emit --check
    """
    root = repository if repository is not None else _REPOSITORY
    rendered = _render(_load())
    for tables in rendered.values():
        for table, rows in tables.items():
            if not table.startswith("__"):
                print(f"{len(rows):5d} {table}")
    bodies = {target: json.dumps(tables, indent=4) + "\n" for target, tables in rendered.items()}
    stale = [
        target
        for target, body in bodies.items()
        if not (root / target).exists() or (root / target).read_text(encoding="utf-8") != body
    ]
    if check:
        if stale:
            for target in stale:
                print(f"stale: {target}")
            raise SystemExit(len(stale))
        print("The written fixtures are what the declaration renders.")
        return
    for target, body in bodies.items():
        (root / target).write_text(body, encoding="utf-8")
        print(f"wrote {target}")


# The preset whose role a project's creator holds while still on its roster.
_CREATOR_PRESET: Final[str] = "project_admin"


@cli.command(name="provision")
@click.pass_obj
def provision(cli_ctx: CLIContext) -> None:
    """
    Instantiate the presets in every domain, project and user that lacks their role.

    A preset whose role file names a scope is pointed at that scope's id first and
    instantiated there alone. Grants what each scope assigns on its own, and the project
    admin role to a project's creator still on its roster. Running it again changes nothing.

    Examples:

    \b
      $ backend.ai mgr permissions provision
    """
    from ai.backend.manager.models.base import ensure_all_tables_registered
    from ai.backend.manager.repositories.db.engine import connect_database
    from ai.backend.manager.repositories.global_entity.loader import GlobalEntityIDLoader
    from ai.backend.manager.repositories.ops.v2.role_preset.provider import RolePresetOpsProvider
    from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository

    seeds = _load()
    creator_preset_ids = [seed.id for seed in seeds if seed.name == _CREATOR_PRESET]

    async def _provision() -> None:
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        # A standalone CLI process has not imported the full model tree.
        ensure_all_tables_registered()
        async with connect_database(bootstrap_config.db) as db:
            await GlobalEntityIDLoader(db).load()
            preset_scopes = {
                seed.id: global_entity_id(seed.scope) for seed in seeds if seed.scope is not None
            }
            repository = RolePresetRepository(RolePresetOpsProvider(db))
            await repository.provision_roles(creator_preset_ids, preset_scopes)

    asyncio.run(_provision())
    print("Provisioned the preset roles.")


if __name__ == "__main__":
    sys.exit(cli())
