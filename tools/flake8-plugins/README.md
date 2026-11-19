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

- A rule is on when `[tool.flake8]` in `pyproject.toml` lists its code in `select`. Turn a rule on once main has no violation of it.
- Codes: `flake8_bai/codes.py`. One module per rule: `flake8_bai/rules/`.
