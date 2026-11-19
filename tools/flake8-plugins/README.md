# flake8-bai

Repository rules that ruff cannot express. `pants lint` runs them through flake8 with `.flake8`.

| Code | Rule | On |
|---|---|---|
| `BAI001` | A manager `__init__.py` holds no import | Yes |
| `BAI101` | A dataclass under `manager/data` is `@dataclass(frozen=True)` | No |
| `BAI102` | An Action or ActionResult under `manager/services` is `@dataclass(frozen=True)` | No |
| `BAI103` | A file under `manager/services` holds at most one Action and one ActionResult | No |

- A rule is on when `.flake8` lists its code in `select`. Turn a rule on once main has no violation of it.
- Codes: `flake8_bai/codes.py`. One module per rule: `flake8_bai/rules/`.
