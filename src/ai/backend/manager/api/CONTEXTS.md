# Manager API layer — Contexts

> For rules, see `AGENTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Adapter `my_` pattern

For self-service (`my_`) endpoints, authentication is handled inside the Adapter. The Adapter calls `current_user()`
to obtain the user context and builds the `SearchScope` from it. The GQL resolver / REST handler does not pass the scope —
it only passes the search input DTO. This is to gather the auth logic into the adapter instead of scattering it across every resolver.

## v2 endpoint verification

Verify new API endpoints against the live server before committing. For server restart, `./bai` commands, and log checks, see
the `/local-dev`, `/bai-cli`, and `/observability` skills.
