# Manager GraphQL Layer — Guardrails

> For full implementation patterns, see the `/api-guide` skill (GraphQL Patterns section).

## Type Naming

- Every Strawberry type MUST carry a `GQL` suffix: `DomainGQL`, `DomainFilterGQL`, `DomainScopeGQL`.
- Applies to all `@strawberry.type`, `@strawberry.input`, and `@strawberry.enum` classes.

## Imports

- NEVER import Strawberry types inside `TYPE_CHECKING` blocks — Strawberry evaluates types at
  runtime and will fail silently or raise errors.
- Always import Strawberry types at module level.

## Cross-Entity References

- Use `strawberry.lazy()` for cross-entity node references to avoid circular imports —
  see `/api-guide` skill for the correct `Annotated[T, lazy(...)] | None` syntax.

## N+1 Prevention

- Never call individual fetch functions inside resolvers for related entities.
- Always use `info.context.data_loaders.*` for cross-entity data loading.

## Admin Check

- Superadmin-only resolvers: call `check_admin_only(info)` as the first statement.

## Calling Services

- Resolvers MUST invoke services through a Processor — never call service methods directly.

## Legacy Code

- Do NOT copy patterns from `gql_legacy/` (Graphene) — it is being migrated to Strawberry.
