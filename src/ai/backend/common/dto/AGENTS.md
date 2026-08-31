# Common DTO — Guardrails

> This package is shared by all components. Changes here affect manager, agent, storage, and client SDK
> at the same time — check all callers before modifying fields.

## Purpose

DTOs shared by multiple backend.ai components (manager, agent, storage, client SDK). DTOs used by only a
single component belong in that component's `dto/` directory.

## Directory structure

Organized by target component: `common/dto/{manager|agent|storage|clients|internal}/`.

## Rules

- All DTOs must inherit from `BaseRequestModel` (Pydantic v2).
- No business logic — validation and serialization only.
- Check all callers across components before modifying fields.
- Use only `v2/` DTOs (e.g., `common/dto/manager/v2/`). DTOs outside `v2/` are deprecated and must not be used in new code.

## Bulk mutation payloads

| Operation | Payload fields |
|---|---|
| Soft delete | `items: list[<Entity>Node]`, `failed: list[<Operation><Entity>Error]` |
| Hard delete (purge) | `successes: list[UUID]`, `failed: list[<Operation><Entity>Error]` |
