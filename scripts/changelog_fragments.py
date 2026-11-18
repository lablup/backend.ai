"""Module, not a command: the rules for the files in the news fragment directory.

Names and front matter are described in `changes/README.md`.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

NUMBERED_RE = re.compile(r"^\d+\.(?P<type>[a-z]+)(\.\d+)?\.md$")
UNNUMBERED_RE = re.compile(r"^\d{8}-\d{6}-[a-z0-9]{6}\.(?P<type>[a-z]+)\.md$")
ISSUE_KEY_RE = re.compile(r"^(BA|BAI)-\d+$")
# towncrier skips these names in the fragment directory besides `template` and `ignore`.
TOWNCRIER_IGNORED = {".gitignore", ".gitkeep", ".keep", "readme", "readme.md", "readme.rst"}
EPIC_DIR_NAME = "epics"
FRONT_MATTER_DELIMITER = "---"


class FragmentError(Exception):
    pass


@dataclass(frozen=True)
class UnnumberedFragment:
    path: Path
    type: str
    issue: str | None
    epic: str | None
    body: str


class FragmentDirectory:
    repo_root: Path
    path: Path
    types: list[str]
    ignored: set[str]

    def __init__(self, repo_root: Path) -> None:
        with (repo_root / "pyproject.toml").open("rb") as f:
            config = tomllib.load(f)["tool"]["towncrier"]
        self.repo_root = repo_root
        self.path = repo_root / config["directory"]
        self.types = [entry["directory"] for entry in config["type"]]
        self.ignored = (
            TOWNCRIER_IGNORED
            | {Path(config["template"]).name.lower()}
            | {name.lower() for name in config.get("ignore", [])}
        )

    def is_ignored(self, name: str) -> bool:
        return any(fnmatch(name.lower(), pattern) for pattern in self.ignored)

    @property
    def epic_dir(self) -> Path:
        return self.path / EPIC_DIR_NAME

    def has_numbered_fragments(self) -> bool:
        return any(NUMBERED_RE.match(p.name) for p in self.path.iterdir() if p.is_file())

    def unnumbered_fragments(self) -> list[UnnumberedFragment]:
        """Parse every unnumbered fragment; raise `FragmentError` listing every broken file."""
        errors = self.check()
        if errors:
            raise FragmentError("\n".join(errors))
        return [
            self.parse_unnumbered(p)
            for p in sorted(self.path.iterdir())
            if p.is_file() and UNNUMBERED_RE.match(p.name)
        ]

    def check(self) -> list[str]:
        """Return one message per file that breaks the rules."""
        errors: list[str] = []
        for path in sorted(self.path.iterdir()):
            if path.is_dir():
                if path.name != EPIC_DIR_NAME or not self.is_ignored(path.name):
                    errors.append(f"{self.rel(path)}: unexpected directory")
                continue
            try:
                self.check_file(path)
            except FragmentError as e:
                errors.append(f"{self.rel(path)}: {e}")
        if self.epic_dir.is_dir():
            for path in sorted(self.epic_dir.iterdir()):
                try:
                    self.check_epic_file(path)
                except FragmentError as e:
                    errors.append(f"{self.rel(path)}: {e}")
        return errors

    def check_file(self, path: Path) -> None:
        name = path.name
        if self.is_ignored(name):
            return
        match = NUMBERED_RE.match(name) or UNNUMBERED_RE.match(name)
        if match is None:
            raise FragmentError(
                "not `<PR-number>.<type>.md` nor `<YYYYMMDD>-<HHMMSS>-<6 chars>.<type>.md`"
            )
        if match.group("type") not in self.types:
            raise FragmentError(
                f"unknown type {match.group('type')!r}; expected one of: {', '.join(self.types)}"
            )
        if UNNUMBERED_RE.match(name):
            fragment = self.parse_unnumbered(path)
            if fragment.epic is not None and not (self.epic_dir / f"{fragment.epic}.md").is_file():
                raise FragmentError(
                    f"epic {fragment.epic} has no `{EPIC_DIR_NAME}/{fragment.epic}.md`"
                )

    def parse_unnumbered(self, path: Path) -> UnnumberedFragment:
        match = UNNUMBERED_RE.match(path.name)
        assert match is not None
        if path.read_text().startswith(FRONT_MATTER_DELIMITER):
            fields, body = self.split_front_matter(path, allowed={"issue", "epic"})
            if not fields:
                raise FragmentError("front matter has neither `issue` nor `epic`")
        else:
            fields, body = {}, path.read_text().strip()
            if not body:
                raise FragmentError("is empty")
        for key in ("issue", "epic"):
            if key in fields and not ISSUE_KEY_RE.match(fields[key]):
                raise FragmentError(f"`{key}: {fields[key]}` is not a `BA-N` or `BAI-N` key")
        return UnnumberedFragment(
            path=path,
            type=match.group("type"),
            issue=fields.get("issue"),
            epic=fields.get("epic"),
            body=body,
        )

    def check_epic_file(self, path: Path) -> None:
        key = path.name.removesuffix(".md").removesuffix(".ko")
        if not path.is_file() or not path.name.endswith(".md") or not ISSUE_KEY_RE.match(key):
            raise FragmentError("not `<BA-N or BAI-N>.md` nor `<BA-N or BAI-N>.ko.md`")
        pair = path.with_name(f"{key}.ko.md" if path.name == f"{key}.md" else f"{key}.md")
        if not pair.is_file():
            raise FragmentError(f"missing its pair `{pair.name}`")
        fields, _ = self.split_front_matter(path, allowed={"title"})
        if "title" not in fields:
            raise FragmentError("front matter has no `title`")

    def split_front_matter(self, path: Path, allowed: set[str]) -> tuple[dict[str, str], str]:
        lines = path.read_text().splitlines()
        if not lines or lines[0] != FRONT_MATTER_DELIMITER:
            raise FragmentError(f"does not start with front matter (`{FRONT_MATTER_DELIMITER}`)")
        try:
            end = lines.index(FRONT_MATTER_DELIMITER, 1)
        except ValueError:
            raise FragmentError("front matter is not closed") from None
        fields: dict[str, str] = {}
        for line in lines[1:end]:
            key, sep, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if not sep or key not in allowed or not value or key in fields:
                raise FragmentError(
                    f"front matter line {line!r}: expected one `<key>: <value>` per key in {sorted(allowed)}"
                )
            fields[key] = value
        body = "\n".join(lines[end + 1 :]).strip()
        if not body:
            raise FragmentError("has no text after the front matter")
        return fields, body

    def rel(self, path: Path) -> str:
        return path.relative_to(self.repo_root).as_posix()
