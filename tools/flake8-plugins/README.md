# flake8-bai

Repository rules that ruff cannot express. `pants lint` runs them through flake8 with `.flake8`.

| Path | Content |
|---|---|
| `flake8_bai/codes.py` | Rule codes |
| `flake8_bai/rules/` | One module per rule |
| `flake8_bai/baseline.txt` | Violations in main when their rule was added |

Regenerate the baseline from the repository root:
`PYTHONPATH=tools/flake8-plugins python -m flake8_bai.write_baseline src > tools/flake8-plugins/flake8_bai/baseline.txt`
