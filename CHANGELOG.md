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

## 24.03.0a1 (2023-11-14)

### Features
* Add vfolder purge API for permanent vfolder removal and change original vfolder delete API to update vfolder status only. ([#835](https://github.com/lablup/backend.ai/issues/835))
* Support session-based usage stats for period. ([#962](https://github.com/lablup/backend.ai/issues/962))
* Add `max_vfolder_count` to `ProjectResourcePolicy` and migrate the same option to `UserResourcePolicy` ([#1417](https://github.com/lablup/backend.ai/issues/1417))
* Refactor initiating logic of model session DB models so that errors while creating the session can be also stored and expressed to user ([#1599](https://github.com/lablup/backend.ai/issues/1599))
* Check health status of model service actively ([#1606](https://github.com/lablup/backend.ai/issues/1606))
* expose `max_ipu_devices_per_container` key to `config.toml` ([#1629](https://github.com/lablup/backend.ai/issues/1629))
* Detailed Docker container creation failure log. ([#1649](https://github.com/lablup/backend.ai/issues/1649))
* Allow privileged access for other's VFolder to superadmin ([#1652](https://github.com/lablup/backend.ai/issues/1652))
* Add a `allow_app_download_panel` config to webserver to show/hide the webui app download panel on the summary page. ([#1664](https://github.com/lablup/backend.ai/issues/1664))
* Add a `allow_custom_resource_allocation` config to webserver to show/hide the custom allocation on the session launcher. ([#1666](https://github.com/lablup/backend.ai/issues/1666))
* Allow explicit `null` and empty string to ContainerRegistry mutations. ([#1670](https://github.com/lablup/backend.ai/issues/1670))
* Add `proxy` and `name` fields to `StorageVolume` graphene object. ([#1675](https://github.com/lablup/backend.ai/issues/1675))
* Add pex + scie based single-file self-contained self-bootstrapping bindary distributions that can be executed on any modern Linux/macOS machines using the standalone Python builds (thanks to @sureshjoshi) ([#1680](https://github.com/lablup/backend.ai/issues/1680))
* Add the --output option to the function that outputs gql and openapi and unify the output format. ([#1691](https://github.com/lablup/backend.ai/issues/1691))
* Add `pipeline.frontend-endpoint` and `pipeline.hide-side-menu-button` configs to webserver. ([#1692](https://github.com/lablup/backend.ai/issues/1692))
* Add a community installer to replace and upgrade `install-dev.sh`, providing a full GUI experience in terminals ([#1694](https://github.com/lablup/backend.ai/issues/1694))
* Add option to control maximum number of NPU per session ([#1696](https://github.com/lablup/backend.ai/issues/1696))
* Limit the size of the scratch directory by using loop mounted sparse file ([#1704](https://github.com/lablup/backend.ai/issues/1704))
* webserver: Include the feature flag `service.is_directory_size_visible` in `/config.toml` which provides an option whether to show/hide directory size in folder explorer ([#1710](https://github.com/lablup/backend.ai/issues/1710))
* Implement per-image metadata sync in the `mgr image rescan` command and deprecate scanning a whole Docker Hub account to avoid the API rate limit ([#1712](https://github.com/lablup/backend.ai/issues/1712))

### Improvements
* Upgrade Graphene and GraphQL core (v2 -> v3) for better support of Relay, security rules, and other improvements ([#1632](https://github.com/lablup/backend.ai/issues/1632))
* Use the explicit `graphql.Undefined` value to fill the unspecified fields of GraphQL mutation input objects ([#1674](https://github.com/lablup/backend.ai/issues/1674))

### Fixes
* Wrong exception handling logics of `SchedulerDispatcher` ([#1401](https://github.com/lablup/backend.ai/issues/1401))
* Use "m" as the default suffix if not specified in the resource slots when creating sessions via the client CLI ([#1518](https://github.com/lablup/backend.ai/issues/1518))
* Update the default API endpoint of the client SDK (`api.cloud.backend.ai`) ([#1610](https://github.com/lablup/backend.ai/issues/1610))
* Fix the mock accelerator plugin to properly set the environment variables without removing existing ones such as `LOCAL_USER_ID`. Also add explicit logging and warning about such situations. ([#1612](https://github.com/lablup/backend.ai/issues/1612))
* Clean up `entrypoint.sh` (our custom container entrypoint), including fixes to avoid non-mandatory recursive file operations on `/home/work` ([#1613](https://github.com/lablup/backend.ai/issues/1613))
* Update GPFS storage client for compatibility. ([#1616](https://github.com/lablup/backend.ai/issues/1616))
* Enable exhaustive search for recursive session termination irrelevant to each session's status ([#1617](https://github.com/lablup/backend.ai/issues/1617))
* Remove legacy name-based container image exclusion filter to prevent unexpected exclusion of user-built images with names containing "base-" or "common" ([#1619](https://github.com/lablup/backend.ai/issues/1619))
* Improve logging when retrying redis connections during failover and use explicit names for all redis connection pools ([#1620](https://github.com/lablup/backend.ai/issues/1620))
* Allow sessions to have dependencies on stale sessions during the `_post_enqueue()` process. ([#1624](https://github.com/lablup/backend.ai/issues/1624))
* Mask sensitive fields when reading the container registry information via the manager GraphQL API ([#1627](https://github.com/lablup/backend.ai/issues/1627))
* Use `ContainerRegistry.hostname` as ID to provide an unique identifier for each GraphQL node. ([#1631](https://github.com/lablup/backend.ai/issues/1631))
* Allow admins to restart other's session by setting an optional parameter `owner_access_key`. ([#1635](https://github.com/lablup/backend.ai/issues/1635))
* Unify each `project` field in GraphQL types `ContainerRegistry` to be a list of string. ([#1636](https://github.com/lablup/backend.ai/issues/1636))
* Update GPFS storage client's Quota API parameters and queries. ([#1637](https://github.com/lablup/backend.ai/issues/1637))
* Lower limit of maximum available characters to name of model service to fix model service session refuses to be created when service name is longer than 28 characters ([#1642](https://github.com/lablup/backend.ai/issues/1642))
* To resolve the type mismatch between DB and schema, changed all schema types of `max_vfolder_count` to int. ([#1643](https://github.com/lablup/backend.ai/issues/1643))
* Set deprecation message to `max_vfolder_size` graphene field. Set `max_vfolder_count` and `max_quota_scope_size` graphene fields optional. Update VFolder update API to use renewed column name `max_quota_scope_size`. ([#1644](https://github.com/lablup/backend.ai/issues/1644))
* Handle `None` value of newly created Docker container's port. ([#1645](https://github.com/lablup/backend.ai/issues/1645))
* Move database accessing code to context manager scope ([#1651](https://github.com/lablup/backend.ai/issues/1651))
* Replace the manager's shared redis config with the common's redis config, as this update is missed in #1586 ([#1653](https://github.com/lablup/backend.ai/issues/1653))
* Revert #1652 ([#1656](https://github.com/lablup/backend.ai/issues/1656))
* Fix `backend.ai-agent` package not recognizing `backend.ai-kernel` as dependency when building python package ([#1660](https://github.com/lablup/backend.ai/issues/1660))
* Fix symbolic link loop error of vfolder ([#1665](https://github.com/lablup/backend.ai/issues/1665))
* Fix `execute_with_retry()` not retrying when DB commit has failed due to incorrect exception handling ([#1667](https://github.com/lablup/backend.ai/issues/1667))
* Update the parameter of session-template update API to follow-up change of session-template create API. ([#1668](https://github.com/lablup/backend.ai/issues/1668))
* Fix infinite loop when malformed symbolic link exists in container ([#1673](https://github.com/lablup/backend.ai/issues/1673))
* Restore removed graphene fields of resource policies and set them deprecated. ([#1677](https://github.com/lablup/backend.ai/issues/1677))
* Allow running manager CLI commands without having `manager.toml` when they do not need it ([#1686](https://github.com/lablup/backend.ai/issues/1686))
* Update all functional wrappers of the Client SDK, CLI commands, and the counterpart Manager GraphQL mutations to distinguish undefined fields and deliberately-set-to-null fields ([#1688](https://github.com/lablup/backend.ai/issues/1688))
* Allow `Undefined` value of `ModifyGroupInput.user_update_mode` field to enable client-py updates group. ([#1698](https://github.com/lablup/backend.ai/issues/1698))
* Handle error in storage proxy's API error handler. ([#1701](https://github.com/lablup/backend.ai/issues/1701))
* Add missing resource-usage fields. ([#1707](https://github.com/lablup/backend.ai/issues/1707))
* Allow empty `auto_terminate_abusing_kernel` field from agent heartbeat. ([#1715](https://github.com/lablup/backend.ai/issues/1715))

### Documentation Updates
* Append new design aligns with revamped backend.ai webpage ([#1690](https://github.com/lablup/backend.ai/issues/1690))
* Append Heading hierarchy font sizes & flyout menu for selecting en and kr. ([#1702](https://github.com/lablup/backend.ai/issues/1702))
* Change fonts to webfonts and erase local font files. ([#1714](https://github.com/lablup/backend.ai/issues/1714))

### Miscellaneous
* Bump base Python version from 3.11.4 to 3.11.6 to resolve potential bugs. ([#1603](https://github.com/lablup/backend.ai/issues/1603))
* Include `HOME` env-var when running tests via pants ([#1676](https://github.com/lablup/backend.ai/issues/1676))


## 24.03.0dev5 (2023-11-13)

This is a test build for the community installer tests.

## 24.03.0dev4 (2023-11-09)

This is a test build for the community installer tests.

## 24.03.0dev3 (2023-11-08)

This is a test build for the community installer tests.

## 24.03.0dev2 (2023-11-08)

This is a test build for the community installer tests.

## 24.03.0dev1 (2023-11-08)

This is a test build for the community installer tests.

## 23.09.0 (2023-09-28)

### Features
* Add option for roundrobin agent selection strategy ([#1405](https://github.com/lablup/backend.ai/issues/1405))
* Add health check and manual trigger API for the manager scheduler ([#1444](https://github.com/lablup/backend.ai/issues/1444))
* Implement VAST storage backend. ([#1577](https://github.com/lablup/backend.ai/issues/1577))

### Fixes
* Apply the jinja `string` filter to a `yarl.URL()`-typed field in webserver.conf to make it serializable ([#1595](https://github.com/lablup/backend.ai/issues/1595))


## 23.09.0b3 (2023-09-22)

### Features
* Add a GraphQL query to get the information of a virtual folder by ID. ([#432](https://github.com/lablup/backend.ai/issues/432))
* Implement limitation of the number of containers per agent. ([#1338](https://github.com/lablup/backend.ai/issues/1338))
* Introduce the k8s agent backend mode to `install-dev.sh` with `--agent-backend` option ([#1526](https://github.com/lablup/backend.ai/issues/1526))
* Improve the resource metadata API (`/config/resource-slots/details`) to include only explicitly reported resource slots and be able to filter by the agent availability in a resource group ([#1589](https://github.com/lablup/backend.ai/issues/1589))

### Fixes
* Enable `ResourceSlotColumn` to return `None` since we need to distinguish between empty `ResourceSlot` value and `None`.
  Alter `kernels.requested_slots` column into not nullable since the value of the column should not be null. ([#1469](https://github.com/lablup/backend.ai/issues/1469))
* Update outdated nfs mount for kubernetes agent backend ([#1527](https://github.com/lablup/backend.ai/issues/1527))
* Collect orphan routings (route which its belonging session is already terminated) ([#1590](https://github.com/lablup/backend.ai/issues/1590))
* Handle external error of storage proxy to return error response with detail message rather than just leaving it. ([#1591](https://github.com/lablup/backend.ai/issues/1591))
* Add `pipeline.endpoint` default value to `configs/webserver/halfstack.conf` to be able to run immediately after install ([#1592](https://github.com/lablup/backend.ai/issues/1592))
* Make `RedisHelperConfig` optional and give default values when it is not specified. ([#1593](https://github.com/lablup/backend.ai/issues/1593))


## 23.09.0b2 (2023-09-20)

### Fixes
* Fix webserver not working ([#1588](https://github.com/lablup/backend.ai/issues/1588))


## 23.09.0b1 (2023-09-20)

### Features
* Implement optional encryption of manager-to-agent RPC channels via CURVE asymmetric keypairs using updated Callosum ([#887](https://github.com/lablup/backend.ai/issues/887))
* Feature to enable/disable passwordless sudo for a user (work account) inside a compute session ([#1530](https://github.com/lablup/backend.ai/issues/1530))
* Use `session.max_age` from webserver.conf to set the expiration for the pipeline authentication token ([#1556](https://github.com/lablup/backend.ai/issues/1556))
* Add new config directive `agent.advertised-rpc-addr` under agent.toml so that agent can be operated under NAT situation ([#1575](https://github.com/lablup/backend.ai/issues/1575))
* Add pipeline option to the `config.toml.j2` so that webui can access it. ([#1576](https://github.com/lablup/backend.ai/issues/1576))

### Fixes
* Fix sentinel connection pool usage and improve Redis sentinel support ([#1513](https://github.com/lablup/backend.ai/issues/1513))
* Fix a mismatch of the list of session status in the CLI and the manager (e.g., missing `PULLING` in the CLI) ([#1557](https://github.com/lablup/backend.ai/issues/1557))
* Let `RedisLock` retry until it acquires lock. ([#1559](https://github.com/lablup/backend.ai/issues/1559))
* Fix vFolder removal failing due to repeated type casting ([#1561](https://github.com/lablup/backend.ai/issues/1561))
* Let agents skip mount/umount task and just produce task succeeded event rather than just return. ([#1570](https://github.com/lablup/backend.ai/issues/1570))
* Resolve `last_used` field of `KeyPair` Gql object from Redis. ([#1571](https://github.com/lablup/backend.ai/issues/1571))
* Fix vFolder bulk deletion to finish any successful deletion task in a bulk. ([#1579](https://github.com/lablup/backend.ai/issues/1579))
* Fix duplicate logger initialization when using `mgr start-server` command and let the CLI commands to use local logger without relaying log records via ZMQ sockets ([#1581](https://github.com/lablup/backend.ai/issues/1581))
* Remove rows corresponding to `vfolders` not found by storage proxy. ([#1582](https://github.com/lablup/backend.ai/issues/1582))
* Handle redis `LockError` when release. ([#1583](https://github.com/lablup/backend.ai/issues/1583))
* Add new alembic migration to remove mismatches between software defined schema and actual DB schema ([#1584](https://github.com/lablup/backend.ai/issues/1584))

### External Dependency Updates
* Upgrade alembic (1.8.1 -> 1.12.0) to add `alembic check` command for ease of database branch/schema management ([#1585](https://github.com/lablup/backend.ai/issues/1585))


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

* [Unified changelog for the core components](https://github.com/lablup/backend.ai/blob/23.03/CHANGELOG.md)
