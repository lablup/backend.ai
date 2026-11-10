# Adapters: Guardrails

Background is in `KNOWLEDGE.md` in this directory.

## Scenarios are scenario tests

- Write the scenarios of an entity in `tests/scenario/`. The rules are in `AGENTS.md` there.
- Read the scenarios of an entity in the `report.md` of its package. Do not write them in `KNOWLEDGE.md`.

## Operation names

- Adapter operations, processor fields and service methods use the same name.

  | Target | Name |
  |---|---|
  | Read several ids | `bulk_get_ids` |
  | Read several natural keys | `bulk_lookup_names`. When the natural key is not a name, `bulk_lookup_<key>` |
  | Find an id from one natural key | `lookup_name`. Each entity exposes it from its own adapter |
  | Global search | `global_search` |
  | Scoped search | `scoped_search` |
  | Write | `create` / `update` / `delete` / `restore` / `purge` |

- Do not prefix `admin_`.
- Do not put `node` in adapter operations, processor fields or Action names.
- This rule does not rename DTOs, REST paths, handler names or GQL fields.

## An adapter takes only the processor of its own entity

- An adapter takes only the processor of its own entity.
- The name of its own entity is resolved inside the operation whose DTO carries that name.
- The adapter does not resolve names of other entities. The REST handler and GQL resolver call the `lookup_name`
  of that entity's adapter first and pass the id.

## An adapter does not read current_user()

- An adapter does not read `current_user()`. It provides only operations that take a scope as input
  (`scoped_search` and others).
- Do not put `my_*` operations on an adapter.
- For a lookup of the caller's own data, the REST handler and GQL resolver put the user id from `current_user()`
  in the scope value and call the scoped operation of the adapter.
- The validator decides permissions with `current_user()` from the request context. Do not pass `UserInfo` for
  permission decisions as an adapter argument.

## Response nodes carry the identifier of their row

- A response node built from `EntityData` carries `entity_id`, one built from `FieldData` carries `field_id`.
  The type is `UUID` and the value comes from the data class as is. Do not parse `id` again.
- Do not use `uuid` in the name of a new identifier field.
- Data classes with no id of their own are outside this rule. The test that checks this rule holds the list.

## Results go in `report.md`

- The `report.md` of an entity package is the output of a run. Do not write its sentences by hand.
- After changing a scenario, run the scenarios and generate the file.

  ```bash
  BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
  python scripts/scenario-report.py dist/scenarios.jsonl --split src/ai/backend/manager/api/adapters
  ```

- When `report.md` disagrees with a run, report it. Do not overwrite it silently.

  ```bash
  python scripts/scenario-report.py dist/scenarios.jsonl --verify src/ai/backend/manager/api/adapters
  ```

- When told they disagree, read what changed first. If a scenario was changed, generate the file again. If no
  scenario was changed, the behavior changed.
- `report.md` also lists the adapter calls that no scenario calls. Do not delete that list.
