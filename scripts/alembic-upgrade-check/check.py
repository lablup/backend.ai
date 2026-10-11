"""Upgrade a released schema seeded with scenario data to this checkout's alembic head.

For each start tag: the release's source and venv are prepared under the cache directory,
its head schema and install fixtures go into a template database, and each scenario runs
in a clone of that template. Nothing touches databases outside the ``--prefix`` names.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import asyncpg
from scenarios import SCENARIOS, Scenario, SkipScenario, Verify
from seeding import Seeder

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURE_LINE = re.compile(r"fixture populate (fixtures/manager/[\w.-]+\.json)")
ERROR_LINE = re.compile(r"^[\w.]*(Error|Exception)\b")
STEP_LINE = re.compile(r"^(\S+ \S+) .*Running upgrade (\S+) -> (\w+)")

ALEMBIC_INI = """\
[alembic]
script_location = ai.backend.manager.models:alembic
sqlalchemy.url = {url}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %Y-%m-%d %H:%M:%S
"""


@dataclass
class StepResult:
    target: str
    ok: bool
    seconds: float
    error: str = ""
    slowest: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class ScenarioResult:
    start: str
    scenario: str
    steps: list[StepResult]
    problems: list[str]
    passed: bool
    seed_notes: list[str] = field(default_factory=list)


def _run(
    cmd: Sequence[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, capture_output=True, cwd=cwd, env=env)
    if proc.returncode != 0:
        raise SystemExit(f"{' '.join(cmd[:2])} failed:\n{proc.stderr[-4000:]}")
    return proc


def prepare_release(tag: str, cache: Path) -> tuple[Path, Path, list[Path]]:
    """Return the release's source root, interpreter and install fixtures, building them once."""
    root = cache / tag
    src = root / "tree"
    python = root / "venv" / "bin" / "python"
    if not (src / "src").is_dir():
        shutil.rmtree(src, ignore_errors=True)
        src.mkdir(parents=True)
        archive = subprocess.run(
            [
                "git",
                "-C",
                str(REPO),
                "archive",
                "--format=tar",
                tag,
                "src/ai/backend",
                "VERSION",
                "requirements.txt",
                "fixtures/manager",
                "scripts/install-dev.sh",
            ],
            check=True,
            capture_output=True,
        )
        with tempfile.TemporaryFile() as fp:
            fp.write(archive.stdout)
            fp.seek(0)
            with tarfile.open(fileobj=fp) as tar:
                tar.extractall(src, filter="data")
    if not python.exists():
        _run(["uv", "venv", "-q", "--python", "3.13", str(root / "venv")])
        _run(
            ["uv", "pip", "install", "-q", "-r", str(src / "requirements.txt")],
            env={**os.environ, "VIRTUAL_ENV": str(root / "venv")},
        )
    install = (src / "scripts" / "install-dev.sh").read_text()
    fixtures = list(dict.fromkeys(src / m for m in FIXTURE_LINE.findall(install)))
    return src, python, fixtures


def prepare_target(ref: str, cache: Path) -> Path:
    """Return the ``src`` of ``ref`` to run its migrations with this checkout's interpreter."""
    root = cache / f"target-{_slug(ref)}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    archive = subprocess.run(
        ["git", "-C", str(REPO), "archive", "--format=tar", ref, "src/ai/backend", "VERSION"],
        check=True,
        capture_output=True,
    )
    with tempfile.TemporaryFile() as fp:
        fp.write(archive.stdout)
        fp.seek(0)
        with tarfile.open(fileobj=fp) as tar:
            tar.extractall(root, filter="data")
    return root / "src"


async def admin_exec(base_url: str, *statements: str) -> None:
    conn = await asyncpg.connect(f"{base_url}/postgres")
    try:
        for statement in statements:
            await conn.execute(statement)
    finally:
        await conn.close()


async def build_template(tag: str, base_url: str, prefix: str, cache: Path) -> str:
    db = f"{prefix}_{_slug(tag)}_base"
    src, python, fixtures = prepare_release(tag, cache)
    await admin_exec(base_url, f'DROP DATABASE IF EXISTS "{db}"', f'CREATE DATABASE "{db}"')
    _run(
        [
            str(python),
            str(HERE / "build_start_schema.py"),
            _async_url(base_url, db),
            *map(str, fixtures),
        ],
        cwd=src / "src",
        env={**os.environ, "PYTHONPATH": str(src / "src")},
    )
    return db


PENDING_SCRIPT = """
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config()
cfg.set_main_option("script_location", "ai.backend.manager.models:alembic")
for rev in ScriptDirectory.from_config(cfg).iterate_revisions("heads", sys.argv[1]):
    print(rev.revision)
"""


def pending_revisions(src: Path, start: str) -> set[str]:
    """The revisions ``upgrade head`` applies from ``start`` in this checkout."""
    out = _run(
        [sys.executable, "-c", PENDING_SCRIPT, start],
        cwd=src,
        env={**os.environ, "PYTHONPATH": str(src)},
    ).stdout
    return set(out.split()) - {start}


def run_alembic(src: Path, base_url: str, db: str, target: str, log_path: Path) -> StepResult:
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as ini:
        ini.write(ALEMBIC_INI.format(url=_async_url(base_url, db)))
    began = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", ini.name, "upgrade", target],
        cwd=src,
        env={**os.environ, "PYTHONPATH": str(src)},
        text=True,
        capture_output=True,
    )
    seconds = time.monotonic() - began
    Path(ini.name).unlink()
    with log_path.open("a") as fp:
        fp.write(f"### upgrade {target}\n{proc.stderr}\n{proc.stdout}\n")
    error = ""
    if proc.returncode != 0:
        errors = [line for line in proc.stderr.splitlines() if ERROR_LINE.match(line)]
        tail = [line for line in proc.stderr.strip().splitlines() if line.strip()]
        error = (errors or tail or [f"exit {proc.returncode}"])[-1][:300]
        failed_at = [m.group(3) for m in map(STEP_LINE.match, proc.stderr.splitlines()) if m]
        if failed_at:
            error = f"at {failed_at[-1]}: {error}"
    return StepResult(target, proc.returncode == 0, seconds, error, _slowest(proc.stderr))


def _slowest(stderr: str, top: int = 3) -> list[tuple[str, float]]:
    """Seconds between consecutive ``Running upgrade`` lines (one-second log resolution)."""
    stamps: list[tuple[str, datetime.datetime]] = []
    for line in stderr.splitlines():
        m = STEP_LINE.match(line)
        if m:
            stamps.append((m.group(3), datetime.datetime.fromisoformat(m.group(1))))
    durations = [
        (rev, (stamps[i + 1][1] - at).total_seconds()) for i, (rev, at) in enumerate(stamps[:-1])
    ]
    return sorted(durations, key=lambda d: -d[1])[:top]


async def run_scenario(
    src: Path,
    tag: str,
    template: str,
    scenario: Scenario,
    base_url: str,
    prefix: str,
    logs: Path,
    keep: bool,
) -> ScenarioResult:
    db = f"{prefix}_{_slug(tag)}_{scenario.name}"
    await admin_exec(
        base_url, f'DROP DATABASE IF EXISTS "{db}"', f'CREATE DATABASE "{db}" TEMPLATE "{template}"'
    )
    log_path = logs / f"{_slug(tag)}-{scenario.name}.log"
    log_path.unlink(missing_ok=True)
    seeder = await Seeder.connect(_plain_url(base_url, db))
    seed_result: ScenarioResult | None = None
    try:
        await scenario.seed(seeder)
    except SkipScenario as e:
        seed_result = ScenarioResult(tag, scenario.name, [], [f"skipped: {e}"], True)
    except Exception as e:
        seed_result = ScenarioResult(tag, scenario.name, [], [f"seed failed: {e!r}"[:300]], False)
    finally:
        await seeder.close()
    if seeder.notes:
        with log_path.open("a") as fp:
            fp.write("### seed notes\n" + "\n".join(seeder.notes) + "\n")
    if seed_result is not None:
        if not keep:
            await admin_exec(base_url, f'DROP DATABASE IF EXISTS "{db}"')
        return seed_result
    steps: list[StepResult] = []
    problems: list[str] = []
    for target in scenario.steps:
        step = run_alembic(src, base_url, db, target, log_path)
        steps.append(step)
        if not step.ok:
            break
        check = scenario.checks_after.get(target)
        if check is not None:
            problems += [f"after {target}: {p}" for p in await _verify(base_url, db, check)]
    upgraded = all(s.ok for s in steps)
    if upgraded:
        problems += await _verify(base_url, db, scenario.verify)
    if scenario.expect_error is None:
        passed = upgraded and not problems
    else:
        passed = not upgraded and scenario.expect_error in steps[-1].error
    if not keep:
        await admin_exec(base_url, f'DROP DATABASE IF EXISTS "{db}"')
    return ScenarioResult(tag, scenario.name, steps, problems, passed, seeder.notes)


async def _verify(base_url: str, db: str, verify: Verify) -> list[str]:
    conn = await asyncpg.connect(_plain_url(base_url, db))
    try:
        return await verify(conn)
    finally:
        await conn.close()


def _out(*parts: object) -> None:
    sys.stdout.write(" ".join(map(str, parts)) + "\n")
    sys.stdout.flush()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _plain_url(base_url: str, db: str) -> str:
    return f"{base_url}/{db}"


def _async_url(base_url: str, db: str) -> str:
    return f"{base_url.replace('postgresql://', 'postgresql+asyncpg://', 1)}/{db}"


def _format(results: list[ScenarioResult]) -> str:
    lines = [
        "| start | scenario | result | steps (seconds) | error / problems | slowest revisions |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        steps = ", ".join(f"{s.target}={'ok' if s.ok else 'FAIL'} {s.seconds:.1f}" for s in r.steps)
        detail = "; ".join(r.problems) or next((s.error for s in r.steps if s.error), "")
        if r.seed_notes:
            detail = f"{detail} (seed notes: {len(r.seed_notes)}, see log)".strip()
        slow = ", ".join(f"{rev} {sec:.0f}s" for s in r.steps for rev, sec in s.slowest if sec >= 1)
        lines.append(
            f"| {r.start} | {r.scenario} | {'PASS' if r.passed else 'FAIL'} | {steps} "
            f"| {detail.replace('|', '/')} | {slow} |"
        )
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="append", required=True, help="release tag, repeatable")
    parser.add_argument(
        "--scenario", action="append", help="scenario name, repeatable (default: all)"
    )
    parser.add_argument("--pg", default="postgresql://postgres:develove@localhost:8101")
    parser.add_argument("--prefix", default="upgrade_check")
    parser.add_argument(
        "--cache", type=Path, default=Path.home() / ".cache" / "bai-alembic-upgrade-check"
    )
    parser.add_argument(
        "--logs", type=Path, default=Path(tempfile.gettempdir()) / "bai-alembic-upgrade-check"
    )
    parser.add_argument(
        "--target", help="upgrade with the migrations of this git ref (default: the working tree)"
    )
    parser.add_argument("--keep", action="store_true", help="keep the scenario databases")
    parser.add_argument("--list", action="store_true", help="list the scenarios and exit")
    args = parser.parse_args()
    if args.list:
        for s in SCENARIOS.values():
            _out(f"{s.name}: {s.description}")
        return 0
    names = args.scenario or list(SCENARIOS)
    unknown = set(names) - set(SCENARIOS)
    if unknown:
        parser.error(f"unknown scenario(s): {sorted(unknown)}")
    args.logs.mkdir(parents=True, exist_ok=True)
    results: list[ScenarioResult] = []
    target_src = REPO / "src"
    if args.target:
        target_src = prepare_target(args.target, args.cache)
    for tag in args.start:
        template = await build_template(tag, args.pg, args.prefix, args.cache)
        conn = await asyncpg.connect(_plain_url(args.pg, template))
        start_rev = await conn.fetchval("SELECT version_num FROM alembic_version")
        await conn.close()
        pending = pending_revisions(target_src, start_rev)
        for name in names:
            scenario = SCENARIOS[name]
            if not set(scenario.requires) <= pending:
                _out(f"| {tag} | {name} | SKIP (already applied: {scenario.requires}) |")
                continue
            result = await run_scenario(
                target_src, tag, template, scenario, args.pg, args.prefix, args.logs, args.keep
            )
            results.append(result)
            _out(_format([result]).splitlines()[-1])
        if not args.keep:
            await admin_exec(args.pg, f'DROP DATABASE IF EXISTS "{template}"')
    _out()
    _out(_format(results))
    _out(f"\nlogs: {args.logs}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
