# Coding Guidelines for AI Coding Agents

This file contains core rules for AI coding agents. For detailed patterns and workflows, use skills and documentation below.

## Documentation Index

**Core Documents (Read directly):**
- `tests/CLAUDE.md` - Testing guidelines and strategies
- `BUILDING.md` - Build system, quality enforcement, BUILD policies
- `README.md` - Project overview and architecture
- `proposals/README.md` - BEP (Backend.AI Enhancement Proposals)

**Skills (Invoke with `/skill-name`):**

Design: `/bep-guide`
Development: `/repository-guide`, `/service-guide`, `/api-guide`, `/tdd-guide`
Utilities: `/cli-executor`, `/db-status`, `/db-migrate`

Skills are in `.claude/skills/{name}/SKILL.md`. See `.claude/skills/README.md` for complete documentation.

## Absolute Rules

**NEVER bypass quality enforcement:**
- Do NOT use `# noqa` to suppress linter warnings
- Do NOT use `# type: ignore` to suppress type errors
- Fix all quality issues immediately, even if unrelated to your change

**Python critical rules:**
- **Async-first**: All I/O operations MUST use async/await
- **Exceptions**: All exceptions MUST inherit from `BackendAIError` (never raise built-in exceptions in business logic)
- **Imports**: NEVER use parent relative imports (`from ..module`) - use absolute imports instead

**BUILD files:**
- ❌ NEVER add BUILD files to `src/` directory
- ✅ MUST add BUILD files to new test directories
- Use `python_tests()` for test modules, `python_testutils()` for utilities

## Before Committing

Always run these commands and fix all errors:

```bash
pants fmt ::
pants fix ::
pants lint --changed-since=HEAD~1
```

The pre-commit hook runs `pants fmt` and `pants lint` automatically.
Type checking (`pants check`) and tests (`pants test`) are enforced by CI only — do **not** run them locally.

**Fix all lint errors - never suppress or skip.**

## Development Guidelines

**README-First:** Always read component README (`src/ai/backend/{component}/README.md`) before making changes.

**BEP-First:** For significant features, use `/bep-guide` skill. Check `proposals/README.md` for existing BEP or create new one.

**TDD:** Write tests first. Use `/tdd-guide` skill for workflow. See `tests/CLAUDE.md` for test strategies.

**Implementation Patterns:** Use skills for detailed guidance:
- Repository layer → `/repository-guide`
- Service layer → `/service-guide`
- API/GraphQL → `/api-guide`
