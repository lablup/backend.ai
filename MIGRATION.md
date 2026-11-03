# Backend.AI Migration Guide

## General

* Run the migration while the managers and agents are shut down.
* This guide describes only the additional steps besides the code and package upgrades.

# 24.09 to 24.12
* `endpoints.desired_session_count` is renamed to `endpoints.replicas`. Update external components that locate the database column directly.
* Move the etcd config `config/network/overlay` to `config/plugins/network/overlay`.

# 24.03 to 24.09
* PostgreSQL was upgraded from 15.1 to 16.3. Create a data dump before the upgrade and restore the data after the upgrade completes.
* Upgrade the DB revision to `3596bc12ec09` **before** starting the Backend.AI manager Python package upgrade. Run `./backend.ai mgr schema apply-missing-revisions` after the package upgrade.

# 23.09 to 24.03
* Python was upgraded from 3.11 to 3.12. The patch version differs by Backend.AI release; check `pants.toml` in each release.
* Downgrade the DB revision to `85615e005fa3` **before** starting the Backend.AI manager Python package upgrade

# 23.03 to 23.09
* The webserver configuration scheme changed.
  - The `webserver`, `logging` and `debug` categories are added, all marked as required.
  - The `session.redis.host` and `session.redis.port` settings are now part of `session.redis.addr`

# 22.09 to 23.03
* Shut down all running containers before starting the 23.03 version of the Backend.AI Agent.
* Python was upgraded from 3.10 to 3.11. The patch version differs by Backend.AI release; check `pants.toml` in each release.
* The `scaling_groups.wsproxy_api_token` column is added.
  - The Model Service API requires it, so keeping the column blank is safe when you do not start Model Service from this resource group
* vfolder v3 folder structure migration
  - The vfolder v3 feature has landed in the release stream, so migrating the existing v2 structure to v3 is strongly recommended. The v2 structure is `/vfroot/<first two characters of uuid>/<second two characters of uuid>/<all other characters>` and the v3 structure is `/vfroot/<quota scope id>/<first two characters of uuid>/<second two characters of uuid>/<all other characters>`. A shell script generator (`ai.backend.storage.migration`) creates an automation script that transforms the structure. Run `python -m ai.backend.storage.migration -h` for more information.
## 21.09 to 22.03

* `alembic upgrade head` is required to migrate the PostgreSQL database schema.
  - The `keypairs.concurrency_used` column is dropped and Redis tracks it instead.
  - The `kernels.last_stat` column remains but updates only when the kernels terminate.
    The `debug.periodic-sync-stats` option in `manager.toml` restores the previous periodic sync behavior.

* Reconfigure the Redis container used with the manager to use a persistent database.
  In a high availability (HA) setup, we recommend enabling AOF with `appendonly yes` in the Redis configuration so it recovers
  after hardware failures.

  See [the official doc](https://redis.io/docs/manual/persistence/) for more details.

  - The Docker official image stores RDB and AOF files in `/data`. Configure an explicit
    bind-mount of a host directory. Without that configuration it creates an anonymous volume
    and mounts it by default.

* The image metadata database moves from etcd to PostgreSQL; the registry configuration remains
  in etcd.

  Run `backend.ai mgr image rescan` in the manager venv or `backend.ai admin image rescan` from clients
  with superadmin privilege to resync the image database. The old etcd image database is no longer
  used.

* The manager now has a distributed lock backend, configured by the key `manager.distributed-lock` in
  `manager.toml`. **The new default is "etcd".** "filelock" suits single-node manager deployments
  because it relies on POSIX file-level advisory locks. Change the value to "pg_advisory" to restore
  the behavior of previous versions. "redlock" is not currently supported because aioredis v2 has a
  limited implementation.

* TODO: Storage Proxy related work.

* Configure an explicit cron job that runs `backend.ai mgr clear-history -r {retention}` to trim old
  sessions' execution records from the PostgreSQL and Redis databases and keep disk and memory usage
  of the manager bounded.

  The retention argument accepts human-readable duration expressions such as `30m`, `6h`, `3d`,
  `2w`, `3mo` and `1yr`. Without a unit suffix, the value is interpreted as seconds.
  We recommend scheduling this command once a day.

## 21.03 to 21.09

* `alembic upgrade head` is required to migrate the PostgreSQL database schema.
