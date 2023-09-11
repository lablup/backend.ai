Changes
=======

<!--
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.

    To add a new change log entry, please refer
    https://pip.pypa.io/en/latest/development/contributing/#news-entries

    We named the news folder "changes".

    WARNING: Don't drop the last line!
-->

<!-- towncrier release notes start -->

## 23.09.0a4 (2023-09-09)

### Features
* Add support for handling OpenID Connect authentication responses ([#1545](https://github.com/lablup/backend.ai/issues/1545))
* Update both agent socket listener and metadata server to let container check what kind of sandbox it is being executed ([#1549](https://github.com/lablup/backend.ai/issues/1549))
* Periodically scan and update available slots of all compute plugins ([#1551](https://github.com/lablup/backend.ai/issues/1551))
* Add `task_name` to all `GlobalTimer._tick_task` for better debugging. ([#1553](https://github.com/lablup/backend.ai/issues/1553))

### Fixes
* Fix storage proxy watcher process always being started event if it is not enabled ([#1547](https://github.com/lablup/backend.ai/issues/1547))
* Fix install-dev.sh failing to run when both trying to run the script from main branch and Node.js is not installed on the system ([#1548](https://github.com/lablup/backend.ai/issues/1548))
* Let `RedisLock` raise `LockError` when it fails to acquire a lock instead of skipping lock. ([#1554](https://github.com/lablup/backend.ai/issues/1554))
* Fix metadata server not started with given port number ([#1555](https://github.com/lablup/backend.ai/issues/1555))


## 23.09.0a3 (2023-09-07)
### Fixes
* Hotfix: DB migration failing ([#1544](https://github.com/lablup/backend.ai/issues/1544))

## 23.09.0a2 (2023-09-06)

### Features
* Preserve the GlobalTimer tick termination logs in task monitoring. ([#1541](https://github.com/lablup/backend.ai/issues/1541))

### Fixes
* Fix service not created when trying to use name of already destroyed one ([#1539](https://github.com/lablup/backend.ai/issues/1539))
* Fix token not stored on database when character count of the token is greater than 1024 ([#1540](https://github.com/lablup/backend.ai/issues/1540))


## 23.09.0a1 (2023-09-06)

### Breaking Changes
* Bump the manager API version to v7.20230615, as it includes a breaking change for quota management APIs ([#1375](https://github.com/lablup/backend.ai/issues/1375))

### Features
* Automate force-termination of hanging sessions, which have been stuck in `PREPARING` or `TERMINATING` status for a long period ([#670](https://github.com/lablup/backend.ai/issues/670))
* Implement `container_pid_to_host_pid()` function ([#955](https://github.com/lablup/backend.ai/issues/955))
* Add `project` field to Keypair graphene object and cmd, update minilang to query multiple rows from joined tables in one aggregated value. ([#1022](https://github.com/lablup/backend.ai/issues/1022))
* Use case-insensitive matching when applying the query filter for enum-based fields ([#1036](https://github.com/lablup/backend.ai/issues/1036))
* Introduce the vfolder structure v3 to handle per-user/per-project quota in a more sensible and compatible way ([#1191](https://github.com/lablup/backend.ai/issues/1191))
* Use `zsh` as the default shell with minimal configs, but including smart auto-completion, when the binary is available in a kernel image. ([#1267](https://github.com/lablup/backend.ai/issues/1267))
* Add basic support for model service ([#1278](https://github.com/lablup/backend.ai/issues/1278))
* Add failure reason to the CLI login process in case of login failure. ([#1305](https://github.com/lablup/backend.ai/issues/1305))
* Implement Dummy agent for easy integration test. ([#1313](https://github.com/lablup/backend.ai/issues/1313))
* upgrade miniling to filter and order by JSON column. ([#1334](https://github.com/lablup/backend.ai/issues/1334))
* Enable to filter and order by agent id when listing sessions. ([#1337](https://github.com/lablup/backend.ai/issues/1337))
* Print migration steps as shell script instead of executing migration directly from python script ([#1345](https://github.com/lablup/backend.ai/issues/1345))
* Issue a signed token to X-BackendAI-SSO header to authorize an user from the pipeline service ([#1350](https://github.com/lablup/backend.ai/issues/1350))
* Add new GraphQL queries and mutations which can manipulate vFolder quota scope ([#1354](https://github.com/lablup/backend.ai/issues/1354))
* Add a `directory_based_usage` config on webserver to show/hide Capacity column in each directory in data & storage page in Client-side. ([#1364](https://github.com/lablup/backend.ai/issues/1364))
* Add the OOM event and the details of potentially affected processes explicitly to the container logs for easier inspection for both users and admins ([#1373](https://github.com/lablup/backend.ai/issues/1373))
* Improve backward compatibility for filtering and querying the agent IDs assigned for a comptue session in the GraphQL API ([#1382](https://github.com/lablup/backend.ai/issues/1382))
* Add `OptionalType` class as a new parameter type wrapper, allowing the client CLI to manage arguments of the `undefined` type. ([#1393](https://github.com/lablup/backend.ai/issues/1393))
* Add more agent selection scheduling strategies ([#1394](https://github.com/lablup/backend.ai/issues/1394))
* Refactor `SessionRow` ORM queries by introducing `KernelLoadingStrategy` to generalize and reuse `SessionRow.get_session()` ([#1396](https://github.com/lablup/backend.ai/issues/1396))
* Update the open-source version of CUDA plugin to use CUDA 12.0, 12.1, and 12.2 versions and add missing pretty string representation of CUDA device objects ([#1419](https://github.com/lablup/backend.ai/issues/1419))
* Add a status-check handler to the storage-proxy's client-facing API ([#1430](https://github.com/lablup/backend.ai/issues/1430))
* Add new GraphQL queries and CLI commands to support paginated vfolder listing ([#1437](https://github.com/lablup/backend.ai/issues/1437))
* Support setting the `wsproxy_addr` and `wsproxy_api_token` option of scaling group in the client-py. ([#1460](https://github.com/lablup/backend.ai/issues/1460))
* Add manager redis ping command: `./backend.ai mgr redis ping` ([#1462](https://github.com/lablup/backend.ai/issues/1462))
* implement basic `ping_kernel()` API on agent side. ([#1467](https://github.com/lablup/backend.ai/issues/1467))
* Improve logging when the agent fails to allocate resource slots ([#1472](https://github.com/lablup/backend.ai/issues/1472))
* Add a `max_count_for_preopen_ports` config on webserver to limit the number of session `preopen_ports` settings. ([#1477](https://github.com/lablup/backend.ai/issues/1477))
* Allow token login with body parameters, along with previous cookie-based way, by passing body to Manager's authorize handler. ([#1478](https://github.com/lablup/backend.ai/issues/1478))
* Add support for displaying `preopen_ports` when executing `session info` CLI command. ([#1479](https://github.com/lablup/backend.ai/issues/1479))
* Implement a storage backend that works with a specific proxy API server in Openstack Manila. ([#1480](https://github.com/lablup/backend.ai/issues/1480))
* - Update storage proxy to be also eligible as an event producer / dispatcher
  - Add event dispatcher at agent ([#1481](https://github.com/lablup/backend.ai/issues/1481))
* Reduce the start-up delay for inference session containers by deferring the initial health check ([#1488](https://github.com/lablup/backend.ai/issues/1488))
* Enable to mount volumes on agents and storage proxies through events.
  Remove kmanila storage backend as it has been migrated to plugins.
  Implement a storage proxy watcher that is delegated root privileges and executes privileged tasks. ([#1495](https://github.com/lablup/backend.ai/issues/1495))
* Set the sleep argument of `AsyncRedisLock` to preevnt flooding the Redis server due to a high rate of polling requests ([#1501](https://github.com/lablup/backend.ai/issues/1501))
* Add GraphQL queries to track down generated endpoint tokens ([#1509](https://github.com/lablup/backend.ai/issues/1509))
* Add a simple storage backend plugin interface to retrieve volume classes from separately install packages ([#1516](https://github.com/lablup/backend.ai/issues/1516))
* Update `ContainerRegistry`-related mutations to respond with affected node ([#1521](https://github.com/lablup/backend.ai/issues/1521))
* Change to allow webserver to save logs to a file, similar to manager and agents. ([#1528](https://github.com/lablup/backend.ai/issues/1528))
* Add session show-graph command to visualize session dependencies ([#1532](https://github.com/lablup/backend.ai/issues/1532))
* Store timestamp of user's last API call date in Unix epoch format on redis ([#1533](https://github.com/lablup/backend.ai/issues/1533))

### Fixes
* Add filters and touch up on vfolder sharing fail
  * Add `is_active` filter on querying from keypair when sharing both user and group(project) vfolder
  * Touch-up message about handling group folder sharing results to display the failed account list properly. ([#1204](https://github.com/lablup/backend.ai/issues/1204))
* Handle buggy ORM field loading when destroy session. ([#1312](https://github.com/lablup/backend.ai/issues/1312))
* Use a more sensible value for the warning threshold for the number of concurrent generic/read-only transactions within a manager process ([#1320](https://github.com/lablup/backend.ai/issues/1320))
* Check `None` value of config argument's `resources` key when enqueue session. ([#1322](https://github.com/lablup/backend.ai/issues/1322))
* Fix to check type of `agent_id` strictly when schedule multi-node session. ([#1325](https://github.com/lablup/backend.ai/issues/1325))
* Set session status `PULLING` when any sibling kernel is pulling image. ([#1326](https://github.com/lablup/backend.ai/issues/1326))
* Fix agent refusing to send heartbeat when `public-host` is set ([#1332](https://github.com/lablup/backend.ai/issues/1332))
* Fix some of manager's vFolder API raising error ([#1333](https://github.com/lablup/backend.ai/issues/1333))
* Update storage proxy's `list_files()` API to only scan files in current directory, instead of scanning recursively ([#1335](https://github.com/lablup/backend.ai/issues/1335))
* Fix vFolder v3 migration script failing ([#1336](https://github.com/lablup/backend.ai/issues/1336))
* Fix agent not reading available krunner volumes when host's docker has untagged image ([#1341](https://github.com/lablup/backend.ai/issues/1341))
* * Resolve regression which `ComputeSessionList` GraphQL query raises HTTP 400 error due to missing conversion of VFolder IDs in the mount history after introduction of Quota Scope IDs, by trying to update kernels and sessions table with appropriate quota scope ID
  * Update VFolderID validator to also allow null vFolder ID in case of older session data with unknown quota scope ID ([#1343](https://github.com/lablup/backend.ai/issues/1343))
* Return None for `sessions.status_changed` when `sessions.status_history` is None ([#1344](https://github.com/lablup/backend.ai/issues/1344))
* Prevent scanning every sub-directories for listing vfolder files for requests with non-`recursive` option. ([#1355](https://github.com/lablup/backend.ai/issues/1355))
* Enhance vfolder v3 directory migration script. ([#1357](https://github.com/lablup/backend.ai/issues/1357))
* Add `groups_name` aggregated field in querying keypairs by email or access key to prevent field reference error. ([#1358](https://github.com/lablup/backend.ai/issues/1358))
* Removing trailling comma from container's `service-ports` label. ([#1359](https://github.com/lablup/backend.ai/issues/1359))
* Fix `get_fs_usage()` API reporting capacity as usage and usage as capacity on GPFS and Weka backend ([#1376](https://github.com/lablup/backend.ai/issues/1376))
* Enable to order or filter by `image` when list sessions. ([#1378](https://github.com/lablup/backend.ai/issues/1378))
* Finalize per-kernel scheduling results using the correct kernel IDs. ([#1380](https://github.com/lablup/backend.ai/issues/1380))
* Avoid returning `NaN` values with undefined capacity and percentage values to prevent calculation errors but just set them zeros. ([#1385](https://github.com/lablup/backend.ai/issues/1385))
* Add `session_name` to aliased key of `session_name` ([#1395](https://github.com/lablup/backend.ai/issues/1395))
* Allow projcet vfolder creation regardless of the user (keypair) vfolder count limit ([#1397](https://github.com/lablup/backend.ai/issues/1397))
* Prevent creating/cloning vfolders with duplicate names on different hosts by deleting conditions checking host. ([#1398](https://github.com/lablup/backend.ai/issues/1398))
* Fix redundant vfolder creation while cloning and avoid checking `max_vfolder_count` when the admin has requested cloning of project type vfolders ([#1400](https://github.com/lablup/backend.ai/issues/1400))
* Fix getting psutil.Process synchronously for catching psutil.NoSuchProcess error leak ([#1408](https://github.com/lablup/backend.ai/issues/1408))
* Enable transit session status from `PULLING` to `CANCELLED` or `TERMINATED`. ([#1412](https://github.com/lablup/backend.ai/issues/1412))
* Make the parsing routine of PostgreSQL version strings more robust with additional build tags ([#1415](https://github.com/lablup/backend.ai/issues/1415))
* Allow storing an empty string (list) in the `project` field of container registry configurations for better compatibility with the GUI behavior and share the same input validation logic in both manager configuration loader and `set_config` API ([#1422](https://github.com/lablup/backend.ai/issues/1422))
* Allow termination of a compute session even when the configured wsproxy address is invalid or inaccessible ([#1423](https://github.com/lablup/backend.ai/issues/1423))
* Update `concurrency_used` by scanning the Redis fully when there is no `Session` data. ([#1429](https://github.com/lablup/backend.ai/issues/1429))
* Add shell script codes to setup `version.txt` including vfolder version in `install-dev.sh`. ([#1438](https://github.com/lablup/backend.ai/issues/1438))
* Ensure the interpretation of the `project` field to be a list when adding/updating container registries, even with empty strings ([#1447](https://github.com/lablup/backend.ai/issues/1447))
* Support CRUD API for container registry using graphQL to deprecate the raw etcd access API from backend.AI WebUI ([#1450](https://github.com/lablup/backend.ai/issues/1450))
* Add None check to out of scoped variable for correct error response to user. ([#1464](https://github.com/lablup/backend.ai/issues/1464))
* Add the mininum page size check when paginating in the client CLI ([#1465](https://github.com/lablup/backend.ai/issues/1465))
* Fix a regression that client-set environment variables were not properly passed to the session containers ([#1470](https://github.com/lablup/backend.ai/issues/1470))
* Update outdated distro selection algorithm of Kubernetes agent backend ([#1474](https://github.com/lablup/backend.ai/issues/1474))
* Provides improved logging of delete operations. ([#1490](https://github.com/lablup/backend.ai/issues/1490))
* Correct null check when migrate `role` column in `kernels` table. ([#1500](https://github.com/lablup/backend.ai/issues/1500))
* Fix a regression of unpickling code runner objects when restoring the last-saved kernel registry while restarting the agents ([#1502](https://github.com/lablup/backend.ai/issues/1502))
* Separate consumer groups of event dispatcher for each service to not intercept other service's event. ([#1503](https://github.com/lablup/backend.ai/issues/1503))
* Fix drifting of the agent allocation maps due to missing rollback mechanism when there is an allocation failure (e.g., `InsufficientResource`) ([#1510](https://github.com/lablup/backend.ai/issues/1510))
* Add missing update of the etcd port in `storage-proxy.toml` by the `install-dev.sh` script ([#1514](https://github.com/lablup/backend.ai/issues/1514))
* Enforce the VFolder `delete_by_id()` handler to validate `id` parameter to be an UUID ([#1517](https://github.com/lablup/backend.ai/issues/1517))
* - Remove rows of sessions table associated with user to purge along with records under tables (error_logs, endpoints) which has foreign key constraint to `sessions.id` 
  - Fix buggy user vfolder fetching query when purging user ([#1531](https://github.com/lablup/backend.ai/issues/1531))
* Fix invalid redis key being set when rescanning resource usage ([#1534](https://github.com/lablup/backend.ai/issues/1534))
* Fix Internal server error (500) raised on situations when Method not allowed (405) should be returned ([#1535](https://github.com/lablup/backend.ai/issues/1535))

### Documentation Updates
* Improve formatting and trafaret compatibility error reporting of the OpenAPI-based Manager REST API reference ([#1452](https://github.com/lablup/backend.ai/issues/1452))
* Add predicate-checking plugin hook to enable validate resource request by plugin. ([#1454](https://github.com/lablup/backend.ai/issues/1454))
* Update the environment setting command in `development-setup` document for verifying the installation ([#1463](https://github.com/lablup/backend.ai/issues/1463))

### External Dependency Updates
* Update etcetra version to 0.1.17 ([#1537](https://github.com/lablup/backend.ai/issues/1537))

### Miscellaneous
* Due to reduced readability due to numerous decorators, duplicate decorators are integrated and managed, and related modules are separated into `session` subpackages. ([#537](https://github.com/lablup/backend.ai/issues/537))
* Bump the base Python version from 3.11.3 to 3.11.4 to resolve potential upstream bugs ([#1431](https://github.com/lablup/backend.ai/issues/1431))
* Auto-enable `--editable-webui` option when running `install-dev.sh` from the main branch to ensure the latest version of it ([#1441](https://github.com/lablup/backend.ai/issues/1441))
* Add `--show-guide` option to `install-dev.sh` for redisplaying the after-setup instructions ([#1442](https://github.com/lablup/backend.ai/issues/1442))
* Replaced Flake8 and isort with Ruff for faster linting and formatting ([#1475](https://github.com/lablup/backend.ai/issues/1475))


## 23.03 and earlier

Please refer the following per-package changelogs.

* [Unified changelog for the core components](https://github.com/lablup/backend.ai/blob/23.03/CHANGELOG.md)
