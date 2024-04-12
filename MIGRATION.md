Backend.AI Migration Guide
==========================

## General

* The migration should be done while the managers and agents are shut down.
* This guide only describes additional steps to follow other than the code/package upgrades.

# 23.09 to 24.03
* Python version upgraded from 3.11 to 3.12. Actual patch version may differ by every Backend.AI release, so please make sure to check `pants.toml` of each release.
* DB revision must be downgraded to `85615e005fa3` **before** initiating Backend.AI manager Python package upgrade

# 23.03 to 23.09
* webserver configuration scheme updated
  - `webserver`, `logging` and `debug` categories added, with all of those marked as required.
  - `session.redis.host` and `session.redis.port` settings are now part of `session.redis.addr`

# 22.09 to 23.03
* All running containers **MUST** be shut down before starting 23.03 version of Backend.AI Agent.
* Python version upgraded from 3.10 to 3.11. Actual patch version may differ by every Backend.AI release, so please make sure to check `pants.toml` of each release.
* `scaling_groups.wsproxy_api_token` column added
  - Required when calling Model Service API, so it is safe to leave column as blank when you're not starting Model Service from this scaling group
* vFolder v3 folder structure migration
  - since vFolder v3 feature is landed at the release stream, it is strongly recommended to migrate existing v2 (/vfroot/<first two characters of uuid>/<second two characters of uuid>/<all other characters>) structure to v3 (/vfroot/<quota scope id>/<first two characters of uuid>/<second two characters of uuid>/<all other characters>). There is a shell script generator (ai.backend.storage.migration) to create an automation script to transform the structure. Please check out `python -m ai.backend.storage.migration -h` for more information.
## 21.09 to 22.03

* `alembic upgrade head` is required to migrate the PostgreSQL database schema.
  - The `keypairs.concurrency_used` column is dropped and it will use Redis to keep track of it.
  - The `kernels.last_stat` column is still there but it will get updated only when the kernels terminate.
    There is a backup option to restore prior behavior of periodic sync: `debug.periodic-sync-stats` in
    `manager.toml`, though.

* The Redis container used with the manager should be reconfigured to use a persistent database.
  In HA setup, it is recommended to enable AOF by `appendonly yes` in the Redis configuration to make it
  recoverable after hardware failures.

  Consult [the official doc](https://redis.io/docs/manual/persistence/) for more details.

  - FYI: The Docker official image uses `/data` as the directory to store RDB/AOF files.  It may be
    configured to use an explicit bind-mount of a host directory.  If not configured, by default it will
    create an anonymous volume and mount it.

* The image metadata database is migrated from etcd to PostgreSQL while the registry configuration is
  still inside the etcd.

  Run `backend.ai mgr image rescan` in the manager venv or `backend.ai admin image rescan` from clients
  with the superadmin privilege to resync the image database.  The old etcd image database will no longer
  be used.

* The manager now has replacible distributed lock backend, configured by the key `manager.distributed-lock` in
  `manager.toml`.  **The new default is "etcd".**  "filelock" is suitable for single-node manager deployments
  as it relies on POSIX file-level advisory locks.  Change this value to "pg_advisory" to restore the behavior
  of previous versions.  "redlock" is not currently supported as aioredis v2 has a limited implementation.

* (TODO) storage-proxy related stuffs

* Configure an explicit cron job to execute `backend.ai mgr clear-history -r {retention}` which trims old
  sessions' execution records from the PostgreSQL and Redis databases to avoid indefinite grow of disk
  and memory usage of the manager.

  The retention argument may be given as human-readable duration expressions, such as `30m`, `6h`, `3d`,
  `2w`, `3mo`, and `1yr`.  If there is no unit suffix, the value is interpreted as seconds.
  It is recommended to schedule this command once a day.

## 21.03 to 21.09

* `alembic upgrade head` is required to migrate the PostgreSQL database schema.
