# flake8-bai

Repository rules that ruff cannot express. The `lint` group of `pyproject.toml` installs this package with flake8; CI and the pre-commit hook run `flake8` (`BUILDING.md`).

| Code | Rule | On |
|---|---|---|
| `BAI001` | A manager `__init__.py` holds no import | Yes |
| `BAI101` | A dataclass under `manager/data` is `@dataclass(frozen=True)` | No |
| `BAI102` | An Action or ActionResult under `manager/services` is `@dataclass(frozen=True)` | No |
| `BAI103` | A file under `manager/services` holds at most one Action and one ActionResult | No |
| `BAI201` | A class under `common/dto` is not a `@dataclass` | No |
| `BAI202` | A class under `common/dto/manager/v2` does not inherit `BackendAISchema` directly | No |
| `BAI203` | A class under `common/dto/manager/v2` has no `to_*` or `from_*` method | No |
| `BAI204` | A module under `client/cli/v2` imports `ai.backend.common.dto` only inside a function or under `if TYPE_CHECKING:` | No |
| `BAI301` | A public method of a class in `manager/repositories` `repository.py` or `repositories.py` returns no Row, also inside a generic or a union | No |
| `BAI302` | A Row class under `manager/models` holds only `to_*`/`from_*` methods and dunder methods | No |
| `BAI303` | A migration with `# Part of: NEXT_RELEASE_VERSION` wraps in `op.f()` a constraint name equal to the naming convention of `manager/models/base.py` (`op.create_*` calls and constraints in `op.create_table`) | No |
| `BAI401` | The module file and top-level name a `LazyGroup` `import_name` points at exist (read from source, not imported) | Yes |
| `BAI402` | A decorated `admin_*` resolver under `manager/api/gql` calls `check_admin_only()` first | No |
| `BAI403` | Storage `api/` has no module-level `async def` handler taking only a `Request` | No |
| `BAI404` | An App Proxy `mapped_column()` or `Column()` type is not `EnumType`, `ENUM` or SQLAlchemy `Enum` | No |

- A rule is on when `[tool.flake8]` in `pyproject.toml` lists its code in `select`. Turn a rule on once main has no violation of it.
- Codes: `flake8_bai/codes.py`. One module per rule: `flake8_bai/rules/`.
