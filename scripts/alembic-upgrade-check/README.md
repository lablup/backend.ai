# alembic upgrade check

Seeds a released tag's schema with scenario data, runs `alembic upgrade` with the manager
migrations of this checkout (or of the git ref given by `--target`), and prints the results
as a table.

## Running

```bash
dist/export/python/virtualenvs/python-default/*/bin/python \
    scripts/alembic-upgrade-check/check.py --start 26.4.8 --start 25.15.12
```

| Option | Meaning |
|---|---|
| `--start <tag>` | Start release. Repeatable |
| `--scenario <name>` | Scenario to run; all when omitted. `--list` prints them |
| `--target <ref>` | Upgrade with the migrations of this ref. Reproduces the behavior before a fix |
| `--pg <url>` | Postgres address. Defaults to halfstack (`postgresql://postgres:develove@localhost:8101`) |
| `--prefix <name>` | Prefix of the databases it creates. Only databases with this prefix are created and dropped |
| `--logs <dir>` | Per-scenario logs. Defaults to a temporary directory |
| `--keep` | Keep the databases afterwards |

| Environment variable | Default | Used by |
|---|---|---|
| `UPGRADE_CHECK_ROWS` | 100000 | `scale`: rows of sessions, kernels and audit_logs (five times as many kernel_usage_records) |
| `UPGRADE_CHECK_USERS` | 6000 | `many_users`: number of users |

The exit code is 0 when every scenario ends as expected.

## How it works

1. Extracts the start tag's `src`, `requirements.txt` and `fixtures/manager` into `--cache`
   (default `~/.cache/bai-alembic-upgrade-check`) and builds a venv from that
   `requirements.txt`.
2. Builds the head schema with that release's code the way `schema oneshot` does, adds the
   fixtures that release's `install-dev.sh` populates, and keeps it as a template database.
3. For each scenario, clones the template, seeds it, runs `alembic upgrade` through the
   revisions in `steps`, and checks the result.

A scenario is skipped when the start tag has already applied the revisions it covers.

## Value combinations (`values_*`)

Every table gets rows holding values the start schema accepts (`schema_values.py`).

| Scenario | Values |
|---|---|
| `values_nulls` | NULL in every nullable column |
| `values_json_null` | JSON `null` in every json column |
| `values_empty_values` | `''` in free text, `{}` and `[]` in json, `'{}'` in arrays |
| `values_dangling_refs` | An id no row holds in uuid and reference-named columns without a foreign key |
| `values_every_enum_value` | Every value of the database enums and of the Python enums in the release code |
| `values_duplicates` | A copy of one row per table, with new values in unique columns only |

- A row the schema rejects with all targeted columns set is retried one column at a time.
  Values still rejected are listed under `seed notes` in the log.
- Text columns the runtime writes in one format only are listed in `UUID_TEXT` with the reason.
- Relations the runtime always keeps (route owner = deployment owner, permission bit =
  operation) are restored after seeding.
- Data a migration refuses on purpose (a custom role's rows in another scope, folders of the
  same name) is not seeded. Dedicated scenarios cover it.

## Adding a scenario

Add a `Scenario` to `SCENARIOS` in `scenarios.py`.

| Field | Meaning |
|---|---|
| `seed` | Inserts rows through `Seeder`. NOT NULL columns left out get the first row of their foreign key target or a value of their type |
| `steps` | Revisions to upgrade to in order. Defaults to `("head",)` |
| `checks_after` | Checks to run after a given step |
| `verify` | Check after the last step. Returns the problems as strings |
| `expect_error` | For a scenario expected to fail, a string the error message must contain |
| `requires` | Revisions the scenario covers. Skipped for a start tag that has applied them |

## Limits

- The start schema is built with `metadata.create_all`. Constraint names and enum types may
  differ from a production database that went through the migrations one by one.
- Timings of the scaled scenarios are local halfstack timings. Production timings depend on
  disk and lock contention.
