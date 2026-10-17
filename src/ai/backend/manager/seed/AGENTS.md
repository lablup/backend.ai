# Seed kind — Guardrails

## References to other entities

- A seed item that refers to another entity takes that entity's UUID in a `<entity>_id` field, not its name.
- Where the DB column holds a name as the FK (`users.resource_policy` and others), the upserter fills it with a subquery looking the name up by the id. An id naming no row leaves the NOT NULL column empty, which refuses the item.
- Exception: an app config is referred to by `config_name`, the FK and unique key of the allow list and the fragments.
- In a seed file, a line stating another entity's UUID ends with that entity's name as a comment (`# <name>`). It is for readers; `seed check` does not verify it.
