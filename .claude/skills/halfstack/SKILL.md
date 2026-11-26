---
name: halfstack
description: Start the PostgreSQL for local database tests from docker-compose.halfstack-main.yml and connect to it with TEST_DATABASE_URL. Use when running Go tests that need a database locally.
tags:
  - dev
  - docker
  - halfstack
---

> Step 4 of the workflow (the "Workflow" table in AGENTS.md).

# halfstack

Run the Go tests that need a database (`dbtest.New`) locally against the PostgreSQL of `docker-compose.halfstack-main.yml` (repository root).

## Use when

- Running `go test -race ./...` against a local database through `TEST_DATABASE_URL`
- Looking at the state of the local PostgreSQL directly

## Start only PostgreSQL

Run from the repository root. Always name the service `backendai-half-db`.

```bash
docker compose -f docker-compose.halfstack-main.yml up -d --wait backendai-half-db
```

- `up` without a service name also starts Valkey, etcd and Prometheus.
- `backendai-half-db` is `postgres:16.3-alpine` and opens host port `8100`. It is created with database `backend`, user `postgres` and password `develove`.
- The data stays in `volumes/postgres-data` (relative to the compose file: `./volumes/${DATADIR_PREFIX:-.}/postgres-data`).

## Run the tests

```bash
TEST_DATABASE_URL='postgres://postgres:develove@localhost:8100/postgres?sslmode=disable' go test -race ./...
```

- `dbtest.New(t)` connects to this address, creates a temporary database for each test and deletes it when the test ends. The connected user must be able to create a database (the `postgres` user can).
- The template database with the migrations applied (named `tmpl_<hash>`) stays on the server and is built again when a migration file changes.
- The conditions under which a test skips the database follow `/test-guide`.

## Check the state and clean up

```bash
docker compose -f docker-compose.halfstack-main.yml ps
docker compose -f docker-compose.halfstack-main.yml logs backendai-half-db
docker compose -f docker-compose.halfstack-main.yml exec backendai-half-db psql -U postgres
docker compose -f docker-compose.halfstack-main.yml stop backendai-half-db
```

## Other services

Besides PostgreSQL, `docker-compose.halfstack-main.yml` has Valkey (`backendai-half-redis`), etcd (`backendai-half-etcd`), Prometheus and the services the profiles `observability` and `telemetry` turn on. The only service the Go tests need now is `backendai-half-db`.
