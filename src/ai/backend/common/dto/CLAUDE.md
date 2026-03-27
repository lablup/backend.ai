# Common DTO — Guardrails

> This package is shared across all components. Any change here affects manager, agent, storage,
> and the client SDK simultaneously — verify all callers before modifying a field.

## Purpose

DTOs shared across multiple backend.ai components (manager, agent, storage, client SDK).
If a DTO is only used within a single component, put it in that component's own `dto/` directory.

## Directory Structure

Organize by target component: `common/dto/{manager|agent|storage|clients|internal}/`.

## Rules

- All DTOs MUST inherit from `BaseRequestModel` (Pydantic v2).
- Only import from Python stdlib and `common/types` — never from component-specific packages
  (`manager/`, `agent/`, `storage/`).
- No business logic — validation and serialization only.
- Before modifying any field, verify all callers across components.
