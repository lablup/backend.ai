Backend.AI Migration Guide
==========================

## General

* The migration should be done while the managers and agents are shut down.
* This guide only describes additional steps to follow other than the code/package upgrades.

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
