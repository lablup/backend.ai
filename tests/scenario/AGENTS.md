# Scenario tests: Guardrails

Background and rationale are in `KNOWLEDGE.md` in this directory, the layout in `README.md`.

## What to write

- Scenarios live in this tree. Read them in the `report.md` (English) and `report.ko.md` (Korean) of the
  entity package. Do not write them in `KNOWLEDGE.md`.
- Work from the `adapter.py` of the entity. Write scenarios for every call it exposes.
- Do not write scenarios for what every entity handles the same way: AND, OR and NOT filter combinations,
  pagination, default sort direction. Entity scenarios cover the filters and sorts of that entity's fields.
- After writing, generate the reports of the entity package from the run with `--split`. `--verify` reports
  when either file disagrees with the run.

## What a row says

A scenario is one class. It defines its name, what it guarantees, and three steps.

| Part | Meaning |
|---|---|
| `summary` | Short kebab-case summary in English. Also the pytest parameter id |
| `describe` | One sentence on what this row guarantees |
| `given` | Sets up what must be true at request time and returns what it set up |
| `when` | Calls with only that value and the adapter |
| `then` | Takes what was seeded and the response or exception, and checks them |

- `given` runs first and returns real values, so nothing defers a value. Do not use deferred calls or lambdas
  that refer to fields.
- The component sets the type `given` returns. Later steps receive that type as is.
- `when` names the adapter call with `operation`. The report uses it to count the adapter calls no scenario
  called.
- If the response wraps a node, `when` unwraps it, so several rows share one checker.
- A row that runs with changed config also implements `Configured`. It is the only place that names a config path.
- Write `describe` with `Says` from `ai.backend.testutils.scenario_steps`: the Korean sentence and the English
  one. Both are required; the English report refuses a sentence whose English is missing.
- Do not put identifiers in `describe`: field names, exception classes, file paths.

## How to seed rows

- Create rows only with write specs from src. Touch the database only through the eight entries of `TestSeeder`:
  `creating`, `provisioning`, `adding`, `adding_with_nested`, `linking`, `accepting`, `granting`, `joining`.
  `accepting` uses the whole operation in which the receiver accepts a share offer. `joining` adds a user to a
  project member list. `adding` seeds a field row. Write rows the manager creates with `TestSeedFieldCreator`, rows it
  upserts with `TestSeedFieldUpserter`. `adding_with_nested` seeds a field row and the rows it owns (such as an
  audit record and its scope rows) in one write. A seed that reads earlier rows uses the entry for that count
  (`creating_from`, `creating_from_two`, `creating_from_three`).
- One seed is one class. It implements the `TestSeedRow` family and defines what it is (`kind`), what it sets up
  (`detail`), the name it appears under (`name`), and what it writes (`seed`).
- For a row whose name the manager fixes, `name` returns that name and takes no number from the seeder. Read
  that name from src. Do not repeat it as a literal in a test.
- Group rows that form one premise with `TestSeedNest`. `kind` says what it prepares, and rows seeded with
  `seed.within` are indented under that group in the report. A group that builds on another group also uses
  `within`.
- Seed a row that must exist only once in a scenario with `seed.once`. Sameness is decided by the seed type.
- Do not use constants for values that link tables. Read policy names, domain names and owner ids from the values
  earlier steps created.
- The only exception is a name src fixes. State that fact in the spec.
- Names are built from a hint and a number. Do not repeat a seeded name as a literal in a request. Read it from
  the created row.
- Where src writes several rows in one operation, use the whole operation. Do not imitate it in pieces.
- Write in `detail` what the row sets up. A name alone does not tell a report reader the situation. Write what
  later steps depend on, such as an allowance, and leave out the rest. Write only what that seed knows itself. Do
  not put the rows it builds on in the sentence.

## Permissions

- Seed only the permissions needed. Do not depend on shipped role presets.
- Pair a row with the permission and a row without it. With only one, you cannot tell whether the permission was
  too broad.
- The requesting user of a row that checks permissions must not be superadmin. The checker passes superadmin
  first, so such a row proves nothing about permissions. The exception is an operation gated by the global role.
  State that fact in `description` then.

## Seeding with fixtures

- A scenario table pairs rows around one call. Write a test that checks what the setup itself creates with the
  `seeding` fixture.
- `seeding` uses the same seeds, the same `TestSeeder` and the same write paths as the table. The only difference
  is when it writes. The row is already written when the fixture returns.
- One fixture handles one row, and rows it builds on come in as fixture arguments. Do not declare rows and write
  them together at the end, because that depends on fixture creation order.
- Tests written this way do not appear in the report, because they do not say what they guarantee, what they call
  and what they expect. Write anything that must count as coverage in the table.

## Shape of the table

- One scenario is one builder function. It takes `TestSeeder`, seeds its rows and returns the scenario.
- The parameter name is fixed as `scenario`. The report picks rows by that name.
- Split test modules by behavior. One module holds one behavior of one component.
- Put the fixture that assembles the adapter in the conftest of those modules. It is the only place that knows the
  component.

## Checks

- Do not write checks that check part of a response. Checking one field passes even when the rest changes
  silently. Do not add helpers that make such checks easy to write.
- Always check the whole response. `then` returns one of three for each field. Report sentences are written
  in both languages; the English report refuses a sentence whose English is missing.

  | What | When | Report text |
  |---|---|---|
  | `Same` | The scenario can state the value | `name = 'host-1'` |
  | `Held` | The value cannot be stated, only a condition | `created_at: time written by this run` |
  | `Skipped` | It cannot be checked, and the reason can be stated | `id: skipped: the database generates it` |

- No field is left without one. A field left out passes silently.
- The condition of `Held` is a `Condition` implementation. The condition says what it is, and that text does not
  include the actual value.
- Do not use a generated id as the expected value of `Same`. It differs per run and makes the report unstable. For
  a field that must equal a value from another field, use the `SameAs` condition. It then states where the value
  came from: `ownership.user_id: same as the creator`.
- With the same behavior, the reports of two runs must match to the character. CI checks this.
- Do not check implementation details. Do not check again what the type already guarantees.

## Reading failures

On a rejection, first check that the premise was actually seeded. A rule was once invented from a rejection whose
premise had not been seeded.

## Package boundaries

- `seeds/` does not import `components`, `runner` or the execution environment modules. It knows only write specs
  and their data types.
- Do not add per-component registries. A test module imports only what it uses.
