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

## 24.09.4 (2024-12-11)
### Miscellaneous
* Add alembic revision history as of 24.03.11


## 24.09.4rc1 (2024-12-11)
### Miscellaneous
* Add alembic revision history as of 24.03.11

## 24.09.3 (2024-12-09)
### Fixes
* Allow purging vfolders by enabling name-based queries of deleted VFolders ([#3176](https://github.com/lablup/backend.ai/issues/3176))
* Fix the issue where the value of occupying slots abnormally multiplies when creating a compute session ([#3186](https://github.com/lablup/backend.ai/issues/3186))
* Add missing `extra` field to `ContainerRegistryNode` GQL query, mutations. ([#3208](https://github.com/lablup/backend.ai/issues/3208))


## 24.09.3rc2 (2024-12-09)

### Fixes
* Fix purge functionality that deletes VFolder records by allowing admins to query other users' VFolders ([#3223](https://github.com/lablup/backend.ai/issues/3223))


## 24.09.3rc1 (2024-12-09)

### Fixes
* Allow purging vfolders by enabling name-based queries of deleted VFolders ([#3176](https://github.com/lablup/backend.ai/issues/3176))
* Fix the issue where the value of occupying slots abnormally multiplies when creating a compute session ([#3186](https://github.com/lablup/backend.ai/issues/3186))
* Add missing `extra` field to `ContainerRegistryNode` GQL query, mutations. ([#3208](https://github.com/lablup/backend.ai/issues/3208))


## 24.09.2 (2024-11-29)
### Fixes
* Allow the `modify_compute_session` mutation works without `priority` field in input argument and let the mutation validates `name` value ([#2985](https://github.com/lablup/backend.ai/issues/2985))
* Prevent redis password from being logged. ([#3031](https://github.com/lablup/backend.ai/issues/3031))
* Fix regression of the `AgentSummary` resolver caused by an incorrect `batch_load_func` assignment. ([#3045](https://github.com/lablup/backend.ai/issues/3045))
* Fix outdated image string join logic in `ImageRow.image_ref`. ([#3125](https://github.com/lablup/backend.ai/issues/3125))
* Allow admins to delete other users' vfolders by enabling vfolder fetching for precondition checks ([#3137](https://github.com/lablup/backend.ai/issues/3137))
* Fix Libc version not detected on unlabeled images when image has custom entrypoint set ([#3173](https://github.com/lablup/backend.ai/issues/3173))
* Fix service not started when `[logging].rotation-size` config is set ([#3174](https://github.com/lablup/backend.ai/issues/3174))


## 24.09.2rc2 (2024-11-29)
No significant changes.


## 24.09.2rc1 (2024-11-29)

### Fixes
* Allow the `modify_compute_session` mutation works without `priority` field in input argument and let the mutation validates `name` value ([#2985](https://github.com/lablup/backend.ai/issues/2985))
* Prevent redis password from being logged. ([#3031](https://github.com/lablup/backend.ai/issues/3031))
* Fix regression of the `AgentSummary` resolver caused by an incorrect `batch_load_func` assignment. ([#3045](https://github.com/lablup/backend.ai/issues/3045))
* Fix outdated image string join logic in `ImageRow.image_ref`. ([#3125](https://github.com/lablup/backend.ai/issues/3125))
* Allow admins to delete other users' vfolders by enabling vfolder fetching for precondition checks ([#3137](https://github.com/lablup/backend.ai/issues/3137))
* Fix Libc version not detected on unlabeled images when image has custom entrypoint set ([#3173](https://github.com/lablup/backend.ai/issues/3173))
* Fix service not started when `[logging].rotation-size` config is set ([#3174](https://github.com/lablup/backend.ai/issues/3174))


## 24.09.1 (2024-11-25)

### Features
* Allow regular users to assign agent manually if `hide-agent` configuration is disabled ([#2614](https://github.com/lablup/backend.ai/issues/2614))
* Hide FastTrack (`pipeline`) menu by default on installation by `install-dev.sh` script. ([#3010](https://github.com/lablup/backend.ai/issues/3010))
* Add an `show_non_installed_images` option to show all images regardless of installation on environment select section in session/service launcher page. ([#3124](https://github.com/lablup/backend.ai/issues/3124))

### Fixes
* Fix `architecture` condition not applied when query `images` rows ([#2989](https://github.com/lablup/backend.ai/issues/2989))
* Fix missing notification of cancellation or failure of background tasks when shutting down the server ([#2579](https://github.com/lablup/backend.ai/issues/2579))
* Disallow `None` id encoding in `AsyncNode.to_global_id()`. ([#2898](https://github.com/lablup/backend.ai/issues/2898))
* Update Dellemc OneFS storage backend to correctly initialize volume object and wrong http request arguments ([#2918](https://github.com/lablup/backend.ai/issues/2918))
* Fix `order` GQL query argument parser of `group_nodes` ([#2927](https://github.com/lablup/backend.ai/issues/2927))
* Set the `postgres_readonly` flag to `false` when begin generic sessions ([#2946](https://github.com/lablup/backend.ai/issues/2946))
* Fix wrong container registry migration script. ([#2949](https://github.com/lablup/backend.ai/issues/2949))
* Let GPFS client keep polling when GPFS job is running ([#2961](https://github.com/lablup/backend.ai/issues/2961))
* Handle `IndexError` when parse string to `BinarySize` ([#2962](https://github.com/lablup/backend.ai/issues/2962))
* Handle error when convert `shmem` string value into `BinarySize` ([#2972](https://github.com/lablup/backend.ai/issues/2972))
* Fix a wrong parameter when call 'recalc_agent_resource_occupancy()' ([#2982](https://github.com/lablup/backend.ai/issues/2982))
* Make image, container_registry table's `project` column nullable and improve container registry storage config migration script. ([#2978](https://github.com/lablup/backend.ai/issues/2978))
* Fix wrong password limit in container registry migration script. ([#2986](https://github.com/lablup/backend.ai/issues/2986))
* Strengthen join condition between kernels and images to prevent incorrect matches ([#2993](https://github.com/lablup/backend.ai/issues/2993))
* Enable session commit to different registry, project. ([#2997](https://github.com/lablup/backend.ai/issues/2997))
* Wrong field reference in `ImageNode` resolver ([#3002](https://github.com/lablup/backend.ai/issues/3002))
* Fix obsolete logic of `untag()` of `HarborRegistry_v2`. ([#3004](https://github.com/lablup/backend.ai/issues/3004))
* Fix `Agent.compute_containers` GraphQL field by adding missing resolver ([#3011](https://github.com/lablup/backend.ai/issues/3011))
* Fix `backend.ai apps` command's faulty argument handling logic. ([#3015](https://github.com/lablup/backend.ai/issues/3015))
* Check Vast data quota with a given name exists before creating quota and change default value of `force_login` config to true ([#3023](https://github.com/lablup/backend.ai/issues/3023))
* Fix `get_logs_from_agent()` to raise `InstanceNotFound` exception for kernels not assigned to agents ([#3032](https://github.com/lablup/backend.ai/issues/3032))
* Fix regression of `ComputeContainer` GraphQL queries due to newly introduced relationship fields ([#3042](https://github.com/lablup/backend.ai/issues/3042))
* Fix model service traffics not distributed equally to every sessions when there are 10 or more replicas ([#3043](https://github.com/lablup/backend.ai/issues/3043))
* Fix regression of `LegacyComputeSession` GraphQL queries. ([#3046](https://github.com/lablup/backend.ai/issues/3046))
* Include missing legacy logging module in the pex. ([#3054](https://github.com/lablup/backend.ai/issues/3054))
* Change the name of deleted vfolders with a timestamp suffix when sending them to DELETE_ONGOING status to allow reuse of the vfolder name, for cases when actual deletion takes a long time ([#3061](https://github.com/lablup/backend.ai/issues/3061))
* Fix model service not routing traffics based on traffic ratio ([#3075](https://github.com/lablup/backend.ai/issues/3075))
* Fix the broken `ComputeContainer.batch_load_detail` due to the misuse of `selectinload` as follow-up to #3042 ([#3078](https://github.com/lablup/backend.ai/issues/3078))
* Fix session `status_info` not being updated correctly when batch executions fail, ensuring failed batch execution states are properly reflected in the sessions table ([#3085](https://github.com/lablup/backend.ai/issues/3085))
* agent not loading `krunner-extractor` image when Docker instance does not support loading XZ compressed images ([#3101](https://github.com/lablup/backend.ai/issues/3101))


## 24.09.1rc2 (2024-10-28)

### Fixes
* Fix `architecture` condition not applied when query `images` rows ([#2989](https://github.com/lablup/backend.ai/issues/2989))


## 24.09.1rc1 (2024-10-25)

### Fixes
* Fix missing notification of cancellation or failure of background tasks when shutting down the server ([#2579](https://github.com/lablup/backend.ai/issues/2579))
* Disallow `None` id encoding in `AsyncNode.to_global_id()`. ([#2898](https://github.com/lablup/backend.ai/issues/2898))
* Update Dellemc OneFS storage backend to correctly initialize volume object and wrong http request arguments ([#2918](https://github.com/lablup/backend.ai/issues/2918))
* Fix `order` GQL query argument parser of `group_nodes` ([#2927](https://github.com/lablup/backend.ai/issues/2927))
* Set the `postgres_readonly` flag to `false` when begin generic sessions ([#2946](https://github.com/lablup/backend.ai/issues/2946))
* Fix wrong container registry migration script. ([#2949](https://github.com/lablup/backend.ai/issues/2949))
* Let GPFS client keep polling when GPFS job is running ([#2961](https://github.com/lablup/backend.ai/issues/2961))
* Handle `IndexError` when parse string to `BinarySize` ([#2962](https://github.com/lablup/backend.ai/issues/2962))
* Handle error when convert `shmem` string value into `BinarySize` ([#2972](https://github.com/lablup/backend.ai/issues/2972))
* Fix a wrong parameter when call 'recalc_agent_resource_occupancy()' ([#2982](https://github.com/lablup/backend.ai/issues/2982))


## 24.09.0 (2024-10-21)

### Features
* Add support for optional payload encryption in the client SDK and CLI as a follow-up to #484 ([#493](https://github.com/lablup/backend.ai/issues/493))
* Allow unicode characters in project(user group) name and domain name. ([#1663](https://github.com/lablup/backend.ai/issues/1663))
* Improve exception logging stability by pre-formatting exception objects instead of pickling/unpickling them ([#1759](https://github.com/lablup/backend.ai/issues/1759))
* Add new API to create new image from live session ([#1973](https://github.com/lablup/backend.ai/issues/1973))
* Clear `error_logs` records in the `clear-history` command ([#1989](https://github.com/lablup/backend.ai/issues/1989))
* Introduce `mgr schema dump-history` and `mgr schema apply-missing-revisions` command to ease the major upgrade involving deviation of database migration histories ([#2002](https://github.com/lablup/backend.ai/issues/2002))
* Update `image forget` CLI command to untag image from registry before forgetting it from the database ([#2010](https://github.com/lablup/backend.ai/issues/2010))
* Update `etcd-client-py` to 0.3.0 ([#2014](https://github.com/lablup/backend.ai/issues/2014))
* Allow self-ssh in single-node single-container compute sessions. ([#2032](https://github.com/lablup/backend.ai/issues/2032))
* Prevent deleting mounted folders. ([#2036](https://github.com/lablup/backend.ai/issues/2036))
* Allow agent to report its internal registry snapshot via UNIX domain socket server ([#2038](https://github.com/lablup/backend.ai/issues/2038))
* New redis client (experimental) ([#2041](https://github.com/lablup/backend.ai/issues/2041))
* Expose user info to environment variables ([#2043](https://github.com/lablup/backend.ai/issues/2043))
* Introduce the `rolling_count` GraphQL field to provide the current rate limit counter for a keypair within the designated time window slice ([#2050](https://github.com/lablup/backend.ai/issues/2050))
* Deprecate the reliance on HTTP cookies for authenticating the pipeline service, switching to the use of HTTP headers instead ([#2051](https://github.com/lablup/backend.ai/issues/2051))
* Allow user to explicitly set filename of model definition YAML ([#2063](https://github.com/lablup/backend.ai/issues/2063))
* Add the `backend.ai plugin scan` command to inspect the plugin scan results from various entrypoint sources ([#2070](https://github.com/lablup/backend.ai/issues/2070))
* Bring back etcetra-backed Etcd as an option for ditributed lock backend ([#2079](https://github.com/lablup/backend.ai/issues/2079))
* Enable distribute-lock configuration ([#2080](https://github.com/lablup/backend.ai/issues/2080))
* Cache volume objects in `RootContext.get_volume` ([#2081](https://github.com/lablup/backend.ai/issues/2081))
* Revamp images GQL query by changing image filtering from flag-based to feature set-based and add `aliases` field to customized image GQL schema ([#2136](https://github.com/lablup/backend.ai/issues/2136))
* Added missing fields for `keypair_resource_policy` in client-py, models, etc. ([#2146](https://github.com/lablup/backend.ai/issues/2146))
* Add parameters to `check-presets` SDK function ([#2153](https://github.com/lablup/backend.ai/issues/2153))
* Add relay-aware `VirtualFolderNode` GQL Query ([#2165](https://github.com/lablup/backend.ai/issues/2165))
* Also perform basic model service validation process when updating model service via `ModifyEndpoint` ([#2167](https://github.com/lablup/backend.ai/issues/2167))
* Add support for mounting arbitrary VFolders on model service session ([#2168](https://github.com/lablup/backend.ai/issues/2168))
* Add support for CentOS 8 based kernels ([#2220](https://github.com/lablup/backend.ai/issues/2220))
* Clear zombie routes automatically ([#2229](https://github.com/lablup/backend.ai/issues/2229))
* Add `scaling_group.agent_count_by_status` and `scaling_group.agent_total_resource_slots_by_status` GQL fields to query the count and the resource allocation of agents that belong to a scaling group. ([#2254](https://github.com/lablup/backend.ai/issues/2254))
* Allow modifying model service session's environment variable setup ([#2255](https://github.com/lablup/backend.ai/issues/2255))
* Add `endpoint.runtime_variant` column ([#2256](https://github.com/lablup/backend.ai/issues/2256))
* Add new API to show list of supported inference runtimes ([#2258](https://github.com/lablup/backend.ai/issues/2258))
* Add support for model service provisioning without `model-definition.yaml` ([#2260](https://github.com/lablup/backend.ai/issues/2260))
* Allow superadmins to force-update session status through destroy API. ([#2275](https://github.com/lablup/backend.ai/issues/2275))
* Add session status check & update API. ([#2312](https://github.com/lablup/backend.ai/issues/2312))
* Add support for fetching container logs of a specific kernel. ([#2364](https://github.com/lablup/backend.ai/issues/2364))
* Introduce Python native WSProxy ([#2372](https://github.com/lablup/backend.ai/issues/2372))
* Implement scanning plugin entrypoints of external packages ([#2377](https://github.com/lablup/backend.ai/issues/2377))
* Add `row_id`, `type` and `container_registry` fields to the `GroupNode` GQL schema. ([#2409](https://github.com/lablup/backend.ai/issues/2409))
* Add support for PureStorage RapidFiles Toolkit v2 ([#2419](https://github.com/lablup/backend.ai/issues/2419))
* Add API that extends lifespan of webserver's login session. ([#2456](https://github.com/lablup/backend.ai/issues/2456))
* Allow bulk association and disassociation of scaling groups with domains, user groups, and key pairs. ([#2473](https://github.com/lablup/backend.ai/issues/2473))
* Match container's timezone to container host OS when available ([#2503](https://github.com/lablup/backend.ai/issues/2503))
* Add a pre-setup configuration menu to the TUI installer to allow setting the public-facing address of Backend.AI components ([#2541](https://github.com/lablup/backend.ai/issues/2541))
* Now Backend.AI can run arbitrary container images without Backend.AI-specific metadata labels by introducing good default values and replacing intrinsic kernel-runner binaries with statically built ones ([#2582](https://github.com/lablup/backend.ai/issues/2582))
* Allow `Bearer` as valid token type on model service authentication ([#2583](https://github.com/lablup/backend.ai/issues/2583))
* Introduce automatic creation of a 'model-store' group upon inserting a new domain. ([#2611](https://github.com/lablup/backend.ai/issues/2611))
* Add support for declaring custom description field for GraphQL `relay` edge types. ([#2643](https://github.com/lablup/backend.ai/issues/2643))
* Add an `enable_LLM_playground` option to show/hide the LLM playground tab on the serving page. ([#2677](https://github.com/lablup/backend.ai/issues/2677))
* Add `max_gaudi2_devices_per_container` config on webserver ([#2685](https://github.com/lablup/backend.ai/issues/2685))
* Add `max_atom_plus_device_per_container` config on webserver ([#2686](https://github.com/lablup/backend.ai/issues/2686))
* Introduce Account-manager component. ([#2688](https://github.com/lablup/backend.ai/issues/2688))
* * Add query depth limit config of GQL.
  * Add page size limit config of GQL Connection.
  * Set default page size of GQL Connection to 10. ([#2709](https://github.com/lablup/backend.ai/issues/2709))
* Add compute session GQL Relay query schema. ([#2711](https://github.com/lablup/backend.ai/issues/2711))
* Allow `DataLoaderManager` to get a loader function by function itself rather than function name. ([#2717](https://github.com/lablup/backend.ai/issues/2717))
* Allow filter and order in endpointlist gql request. ([#2723](https://github.com/lablup/backend.ai/issues/2723))
* Add new vfolder API to update sharing status. ([#2740](https://github.com/lablup/backend.ai/issues/2740))
* Avoid raising a type error even if a particular table in the toml file is empty, as long as the default value for all settings exists. ([#2782](https://github.com/lablup/backend.ai/issues/2782))
* Add an explicit configuration `scaling-group-type` to `agent.toml` so that the agent could distinguish whether itself belongs to an SFTP resource group or not ([#2796](https://github.com/lablup/backend.ai/issues/2796))
* Add per-session priority attributes and `ModifyComputeSession` GraphQL mutation to update session names and priorities ([#2840](https://github.com/lablup/backend.ai/issues/2840))
* Add dependee/dependent/graph ComputeSessionNode connection queries ([#2844](https://github.com/lablup/backend.ai/issues/2844))
* Implement the priority-aware scheduler that applies to any arbitrary scheduler plugin ([#2848](https://github.com/lablup/backend.ai/issues/2848))
* Add support for setting a timeout when pulling Docker images and upgrade aiodocker to version 0.23.0. ([#2852](https://github.com/lablup/backend.ai/issues/2852))

### Improvements
* Enable robust DB connection handling by allowing `pool-pre-ping` setting. ([#1991](https://github.com/lablup/backend.ai/issues/1991))
* Enhance update mechanism of session & kernel status. ([#2311](https://github.com/lablup/backend.ai/issues/2311))
* Remove database-level foreign key constraints in `vfolders.{user,group}` columns to decouple the timing of vfolder deletion and user/group deletion. ([#2404](https://github.com/lablup/backend.ai/issues/2404))
* Implement storage-host RBAC interface. ([#2505](https://github.com/lablup/backend.ai/issues/2505))
* Optimize the query latency when fetching a large number of agents with stat metrics from Redis ([#2558](https://github.com/lablup/backend.ai/issues/2558))
* Split out `ai.backend.logging` package from the `ai.backend.common` to improve reusability and reduce the startup time (i.e., import latencies) ([#2760](https://github.com/lablup/backend.ai/issues/2760))
* Avoid using `collections.OrderedDict` when not necessary in the manager API and client SDK ([#2842](https://github.com/lablup/backend.ai/issues/2842))

### Deprecations
* Remove no longer used `env-tester-{admin,user,user2}.sh` scripts and all references ([#1956](https://github.com/lablup/backend.ai/issues/1956))

### Fixes
* Merge `kernels.role` into `sessions.session_type` and check the image compatibility based on comparison with the `ai.backend.role` label ([#1587](https://github.com/lablup/backend.ai/issues/1587))
* Refactor `PendingSession` Scheduler into `PendingSession` scheduler and `AgentSelector`, and replace `roundrobin` flag with `AgentSelectionStrategy.RoundRobin` policy. ([#1655](https://github.com/lablup/backend.ai/issues/1655))
* Do not omit to update session's occupying resources to DB when a kernel starts. ([#1832](https://github.com/lablup/backend.ai/issues/1832))
* Fix DDN command output handling when exceeding quotas. ([#1901](https://github.com/lablup/backend.ai/issues/1901))
* Explicitly specify the storage-side UID/GID when creating qtrees in the NetApp storage backend ([#1983](https://github.com/lablup/backend.ai/issues/1983))
* Sync mismatch between `kernels.session_name` and `sessions.name` and fix session-rename API to update `session_name` of sibling kernels atomically. ([#1985](https://github.com/lablup/backend.ai/issues/1985))
* Change function default arguments from mutable object to `None`. ([#1986](https://github.com/lablup/backend.ai/issues/1986))
* Revert some VFolder APIs response type to remove mismatch between `Content-Type` header and body. ([#1988](https://github.com/lablup/backend.ai/issues/1988))
* Upgrade pants to 2.21.0.dev4 for Python 3.12 support in their embedded pex/pip versions ([#1998](https://github.com/lablup/backend.ai/issues/1998))
* Fix Graylog log adapter not working after upgrading to Python 3.12 ([#1999](https://github.com/lablup/backend.ai/issues/1999))
* Fix `compute_container` GraphQL query resolver functions. ([#2012](https://github.com/lablup/backend.ai/issues/2012))
* Fix harbor v2 image scanner skipping importing rest of the artifacts when any of the item does not include tag ([#2015](https://github.com/lablup/backend.ai/issues/2015))
* Let external log viewers display more accurate, meaningful stack frames of logger invocations. ([#2019](https://github.com/lablup/backend.ai/issues/2019))
* Fix handling of undefined values in the ModifyImage GraphQL mutation. ([#2028](https://github.com/lablup/backend.ai/issues/2028))
* Fix container commit not working on certain docker engine versions ([#2040](https://github.com/lablup/backend.ai/issues/2040))
* add omitted request fetching from client to manager about deleting vfolder in trash bin. ([#2042](https://github.com/lablup/backend.ai/issues/2042))
* Fix a buggy restriction on VFolder deletion due to wrong query condition ([#2055](https://github.com/lablup/backend.ai/issues/2055))
* Fix wrong usage of dataloader in GQL group resolver. ([#2056](https://github.com/lablup/backend.ai/issues/2056))
* Ensure that vfolders, including automount vfolders, are mounted during session creation only if their status is not set to "DEAD" (i.e., deleted). ([#2059](https://github.com/lablup/backend.ai/issues/2059))
* Fix wrong calculation of resource usage ([#2062](https://github.com/lablup/backend.ai/issues/2062))
* Fix VFolder file operation not working when user has been granted access to shared but deleted VFolder which has same name with the normal one ([#2072](https://github.com/lablup/backend.ai/issues/2072))
* Add missing type argument in group query ([#2073](https://github.com/lablup/backend.ai/issues/2073))
* Let the `backend.ai mgr clear-history` command clears session records as well as kernel records ([#2077](https://github.com/lablup/backend.ai/issues/2077))
* Fix `compute_session_list` GQL query not responding on an abundant amount of sessions ([#2084](https://github.com/lablup/backend.ai/issues/2084))
* Fix VFolder invitation not accepted when inviting VFolder shares name with already deleted one ([#2093](https://github.com/lablup/backend.ai/issues/2093))
* Fix orphan model service routes being created ([#2096](https://github.com/lablup/backend.ai/issues/2096))
* Fix initialization of the resource usage API's kernel-level usage aggregation ([#2102](https://github.com/lablup/backend.ai/issues/2102))
* Fix model server starting on every kernels (including sub role kernels) on multi container infernce session ([#2124](https://github.com/lablup/backend.ai/issues/2124))
* Add missing `commit_session_to_file` to `OP_EXC` ([#2127](https://github.com/lablup/backend.ai/issues/2127))
* Fix wrong SQL query build for GQL Relay node ([#2128](https://github.com/lablup/backend.ai/issues/2128))
* Pass ImageRef.canonical in `commit_session_to_file` ([#2134](https://github.com/lablup/backend.ai/issues/2134))
* Handle fileset-already-exists response of `create-filset` API request and make sure to wait between all GPFS job polling iterations ([#2144](https://github.com/lablup/backend.ai/issues/2144))
* Skip any possible redundant quota update requests when creating new quota ([#2145](https://github.com/lablup/backend.ai/issues/2145))
* * Fix error when calling `check_presets` Client SDK API with an invalid `group` parameter 
  * Rewrite Client SDK to access all APIConfig fields ([#2152](https://github.com/lablup/backend.ai/issues/2152))
* Ensure that all pending sessions are picked by schedulers ([#2155](https://github.com/lablup/backend.ai/issues/2155))
* Fix user creation error when any model-store does not exists. ([#2160](https://github.com/lablup/backend.ai/issues/2160))
* Fix buggy resolver of `model_card` GQL Query. ([#2161](https://github.com/lablup/backend.ai/issues/2161))
* Fix security vulnerability for `sudo_session_enabled` ([#2162](https://github.com/lablup/backend.ai/issues/2162))
* Rename `endpoints.model_mount_destiation` to `model_mount_destination` ([#2163](https://github.com/lablup/backend.ai/issues/2163))
* Wait for real quota scope directory creation after Netapp `create_qtree()` call ([#2170](https://github.com/lablup/backend.ai/issues/2170))
* Fix wrong per-user concurrency calculation logic ([#2175](https://github.com/lablup/backend.ai/issues/2175))
* Keep `sync_container_lifecycles()` bgtask alive in a loop. ([#2178](https://github.com/lablup/backend.ai/issues/2178))
* Fix missing check for group (project) vfolder count limit and error handling with an invalid `group` parameter ([#2190](https://github.com/lablup/backend.ai/issues/2190))
* Fix model service persisting on `degraded` status forever in rare chance when trying to delete the service ([#2191](https://github.com/lablup/backend.ai/issues/2191))
* Fix error when query or mutate GraphQL using `BigInt` field type ([#2203](https://github.com/lablup/backend.ai/issues/2203))
* Ensure that utilization idleness is checked after a set period. ([#2205](https://github.com/lablup/backend.ai/issues/2205))
* Fix `backend.ai ssh` command execution when packaged as SCIE/PEX ([#2226](https://github.com/lablup/backend.ai/issues/2226))
* * fix `endpoints` query not working when trying to load `image_row.aliases`
  * fix `endpoints.status` reporting `PROVISIONING` when its status is in `DESTROYING` state ([#2233](https://github.com/lablup/backend.ai/issues/2233))
* Fix GQL raising error when trying to resolve `endpoints.errors` field occasionally ([#2236](https://github.com/lablup/backend.ai/issues/2236))
* Fix `ZeroDivisionError` in volume usage calculation by returning 0% when volume capacity is zero ([#2245](https://github.com/lablup/backend.ai/issues/2245))
* Fix GraphQL to support query to non-installed images ([#2250](https://github.com/lablup/backend.ai/issues/2250))
* Add missing `push_image` method implementation to Dummy Agent ([#2253](https://github.com/lablup/backend.ai/issues/2253))
* Rename no-op `access_key` parameter of `endpoint_list` GQL Query to `user_uuid` ([#2287](https://github.com/lablup/backend.ai/issues/2287))
* Fix `ai.backend.service-ports` label syntax broken when image does not expose built-in service port ([#2288](https://github.com/lablup/backend.ai/issues/2288))
* Improve stability of `untag_image_from_registry` mutation ([#2289](https://github.com/lablup/backend.ai/issues/2289))
* SSH not working between kernels started with customized image ([#2290](https://github.com/lablup/backend.ai/issues/2290))
* Invalid container memory capacity reported ([#2291](https://github.com/lablup/backend.ai/issues/2291))
* Corrected an issue where the `resource_policy` field in the user model was incorrectly mapped to `domain_name`. ([#2314](https://github.com/lablup/backend.ai/issues/2314))
* Omit to clean containerless kernels which are still creating its container. ([#2317](https://github.com/lablup/backend.ai/issues/2317))
* Fix model service sessions created before 24.03.5 failing to spawn ([#2318](https://github.com/lablup/backend.ai/issues/2318))
* Image commit not working ([#2319](https://github.com/lablup/backend.ai/issues/2319))
* model service session scheduler (`scale_services()`) failing when sessions bound to active route already marked as terminated ([#2320](https://github.com/lablup/backend.ai/issues/2320))
* Fix container metric collection halted on systems with Cgroups v1 ([#2321](https://github.com/lablup/backend.ai/issues/2321))
* Run batch execution after the batch session starts. ([#2327](https://github.com/lablup/backend.ai/issues/2327))
* Add support for configuring `sync_container_lifecycles()` task. ([#2338](https://github.com/lablup/backend.ai/issues/2338))
* Fix mismatches between responses of `/services/_runtimes` and new model service creation input ([#2371](https://github.com/lablup/backend.ai/issues/2371))
* Fix incorrect check of values returned from docker stat API. ([#2389](https://github.com/lablup/backend.ai/issues/2389))
* Shutdown agent properly by removing a code that waits a cancelled task. ([#2392](https://github.com/lablup/backend.ai/issues/2392))
* Restrict GraphQL query to `user_nodes` field to require `superadmin` privilege ([#2401](https://github.com/lablup/backend.ai/issues/2401))
* Handle all possible exceptions when scheduling single node session so that the status information of pending session is not empty. ([#2411](https://github.com/lablup/backend.ai/issues/2411))
* Utilize `ExtendedJSONEncoder` for error logging to handle `UUID` objects in `extra_data` ([#2415](https://github.com/lablup/backend.ai/issues/2415))
* Change outdated references in event module from `kernels` to `sessions`. ([#2421](https://github.com/lablup/backend.ai/issues/2421))
* Upgrade `inquirer` to remove dependency on deprecated `distutils`, which breaks up execution of the scie builds ([#2424](https://github.com/lablup/backend.ai/issues/2424))
* Allow specific status of vfolders to query to purge. ([#2429](https://github.com/lablup/backend.ai/issues/2429))
* Update the install-dev scripts to use `pnpm` instead of `npm` to speed up installation and resolve some peculiar version resolution issues related to esbuild. ([#2436](https://github.com/lablup/backend.ai/issues/2436))
* Fix a packaging issue in the `backendai-webserver` scie executable due to missing explicit requirement of setuptools ([#2454](https://github.com/lablup/backend.ai/issues/2454))
* Improve pruning of non-physical filesystems when measuring disk usage in agents ([#2460](https://github.com/lablup/backend.ai/issues/2460))
* Update the install-dev scripts to install `pnpm` if pnpm isn't installed. ([#2472](https://github.com/lablup/backend.ai/issues/2472))
* Improve error handling of initialization failures in the kernel runner ([#2478](https://github.com/lablup/backend.ai/issues/2478))
* Fix `BACKEND_MODEL_NAME` environment always overwritten to model name specified at model definition ([#2481](https://github.com/lablup/backend.ai/issues/2481))
* Do not allow assigning preopen port which collides with image's own service port definition ([#2482](https://github.com/lablup/backend.ai/issues/2482))
* Fix GET requests with queryparams defined in API spec occasionally throwing 400 Bad Request error ([#2483](https://github.com/lablup/backend.ai/issues/2483))
* Check null value of user mutation by `Undefined` sentinel value rather than `None`. ([#2506](https://github.com/lablup/backend.ai/issues/2506))
* Do null check on `groups.total_resource_slots` and `domains.total_resource_slots` value. ([#2509](https://github.com/lablup/backend.ai/issues/2509))
* Fix hearbeat processing failing when agent reports image with its name not compilant to Backend.AI's naming rule ([#2516](https://github.com/lablup/backend.ai/issues/2516))
* Corrected a typo (`maanger` corrected to `manager`) in the `check_status()` API response of the storage component ([#2523](https://github.com/lablup/backend.ai/issues/2523))
* Rename `images.image_filters` GQL Query argument to `images.image_types` ([#2555](https://github.com/lablup/backend.ai/issues/2555))
* Prevent session status from being transit to `PULLING` status event if image pull is not required ([#2556](https://github.com/lablup/backend.ai/issues/2556))
* Prevent other user's customized image from being listed as a response of `images` GQL query ([#2557](https://github.com/lablup/backend.ai/issues/2557))
* skip resolving malformed `ModelCard` GQL item ([#2570](https://github.com/lablup/backend.ai/issues/2570))
* Delete sessions DB records when purging project. ([#2573](https://github.com/lablup/backend.ai/issues/2573))
* Initialize Redis connection pool objects with specified connection opts rather than ignoring them. ([#2574](https://github.com/lablup/backend.ai/issues/2574))
* Fix `GET /func/folders/{folderName}` API returning string literal `"null"` instead of null value on `user` and `group` fields ([#2584](https://github.com/lablup/backend.ai/issues/2584))
* Update `GQLPrivilegeCheckMiddleware` to align with upstream changes on `graphql-core` package ([#2598](https://github.com/lablup/backend.ai/issues/2598))
* Robust type check when idle checker fetches utilization data. ([#2601](https://github.com/lablup/backend.ai/issues/2601))
* Skip mounting zero-byte lxcfs files when lxcfs is activated to prevent crashes in session containers ([#2604](https://github.com/lablup/backend.ai/issues/2604))
* Fix typo in minilang query field spec and column map. ([#2605](https://github.com/lablup/backend.ai/issues/2605))
* Remove duplicate CPU quota arguments when creating containers ([#2608](https://github.com/lablup/backend.ai/issues/2608))
* Increase `MAX_CMD_LEN` of dropbear to improve compatibility with PyCharm debugger ([#2613](https://github.com/lablup/backend.ai/issues/2613))
* Silence falsy Redis timeout warnings when retrying blocking commands if the timeout does not exceed the expected command timeout ([#2632](https://github.com/lablup/backend.ai/issues/2632))
* Fix a regression of #2483 in the session-download API used by the `backend.ai ssh` command ([#2635](https://github.com/lablup/backend.ai/issues/2635))
* Implement missing `StrEnumType` handling in `populate_fixture()`. ([#2648](https://github.com/lablup/backend.ai/issues/2648))
* Let `GET /resource/usage/period` request contain data in query parameter rather than JSON body. ([#2661](https://github.com/lablup/backend.ai/issues/2661))
* Allow sudo-enabled container users to ovewrite `/usr/bin/scp` and `/usr/libexec/sftp-server` by unifying the intrinsic ssh binaries to use the merged `dropbearmulti` executable. ([#2667](https://github.com/lablup/backend.ai/issues/2667))
* Update `webserver` logout API to respond with HTTP 200 OK ([#2681](https://github.com/lablup/backend.ai/issues/2681))
* Fix WSProxy not properly handling WebSocket request sent from Firefox ([#2684](https://github.com/lablup/backend.ai/issues/2684))
* Scan parent directory of created qtree to avoid creating quota on non-existing directory. ([#2696](https://github.com/lablup/backend.ai/issues/2696))
* Fix `list_files`, `get_fstab_contents`, `get_performance_metric` and `shared_vfolder_info` Python SDK function not working with `ValidationError` exception printed ([#2706](https://github.com/lablup/backend.ai/issues/2706))
* Resolve the issue where the vfolder id does not match in `list_shared_vfolders`. ([#2731](https://github.com/lablup/backend.ai/issues/2731))
* Handle OS Error when deleting vfolders. ([#2741](https://github.com/lablup/backend.ai/issues/2741))
* Fix typo in Virtual-folder status update code. ([#2742](https://github.com/lablup/backend.ai/issues/2742))
* Correct `msgpack` deserialization of `ResourceSlot`. ([#2754](https://github.com/lablup/backend.ai/issues/2754))
* Fix regression error of `session create_from_template` command. ([#2761](https://github.com/lablup/backend.ai/issues/2761))
* Silence `model_` namespace warnings with pydantic-based model classes ([#2765](https://github.com/lablup/backend.ai/issues/2765))
* Change the initialization order of PackageContext to apply `target_path` correctly in the TUI installer ([#2768](https://github.com/lablup/backend.ai/issues/2768))
* Make the regex patterns to update configuration files working with multiline texts correctly in the TUI installer ([#2771](https://github.com/lablup/backend.ai/issues/2771))
* Omit null parameter when call `usage-per-period` API. ([#2777](https://github.com/lablup/backend.ai/issues/2777))
* Delete vfolder invitation and permission rows when deleting vfolders. ([#2780](https://github.com/lablup/backend.ai/issues/2780))
* Handle container port mismatch when creating kernel. ([#2786](https://github.com/lablup/backend.ai/issues/2786))
* Explicitly set the protected service ports depending on the resource group type and the service types ([#2797](https://github.com/lablup/backend.ai/issues/2797))
* Correct session status determiner function. ([#2803](https://github.com/lablup/backend.ai/issues/2803))
* Fix `endpoint_list.total_count` GQL field returning incorrect value ([#2805](https://github.com/lablup/backend.ai/issues/2805))
* Fix `Service.create()` SDK method and `service create` CLI command not working with `UnboundLocalError` exception ([#2806](https://github.com/lablup/backend.ai/issues/2806))
* Refresh expiration time of login session when login. ([#2816](https://github.com/lablup/backend.ai/issues/2816))
* Fix `kernel_id` assignment for main kernel log retrieval ([#2820](https://github.com/lablup/backend.ai/issues/2820))
* Use a safer TLS version (v1.2) when creating SSL sockets in the logstash handler ([#2827](https://github.com/lablup/backend.ai/issues/2827))
* Wrong count of concurrent compute sessions. ([#2829](https://github.com/lablup/backend.ai/issues/2829))
* Create kernels with correct `scaling_group` value. ([#2837](https://github.com/lablup/backend.ai/issues/2837))
* Fix a regression in progress bar rendering of the TUI installer after upgrading the Textual library ([#2867](https://github.com/lablup/backend.ai/issues/2867))

### Documentation Updates
* Add note about installing client library with same version as server ([#1976](https://github.com/lablup/backend.ai/issues/1976))
* Remove deprecated `version` from the docker compose YAML templates in package installation docs. ([#2035](https://github.com/lablup/backend.ai/issues/2035))
* Fix a typo in the `agent.toml` example of the package-based installation guide to have a duplicate double quote ([#2069](https://github.com/lablup/backend.ai/issues/2069))

### External Dependency Updates
* Upgrade the base runtime (CPython) version from 3.11.6 to 3.12.2 ([#1994](https://github.com/lablup/backend.ai/issues/1994))
* Upgrade aiodocker to v0.22.0 with minor bug fixes found by improved type annotations ([#2339](https://github.com/lablup/backend.ai/issues/2339))
* Update the halfstack containers to point the latest stable versions ([#2367](https://github.com/lablup/backend.ai/issues/2367))
* Upgrade aiodocker to 0.22.1 to fix error handling when trying to extract the log of non-existing containers ([#2402](https://github.com/lablup/backend.ai/issues/2402))
* Upgrade the base CPython from 3.12.2 to 3.12.4 ([#2449](https://github.com/lablup/backend.ai/issues/2449))
* Upgrade Python (3.12.4 -> 3.12.6) and common/tool dependencies to prepare for Python 3.13 and apply latest fixes ([#2851](https://github.com/lablup/backend.ai/issues/2851))

### Miscellaneous
* Wrap RPC authentication error to custom error for better logging. ([#1970](https://github.com/lablup/backend.ai/issues/1970))
* Add `requested_slots` field to compute session GQL type. ([#1984](https://github.com/lablup/backend.ai/issues/1984))
* Allow `pydantic.BaseModel` as the API handler return schema. ([#1987](https://github.com/lablup/backend.ai/issues/1987))
* Fix incorrect version notation of GQL Field. ([#1993](https://github.com/lablup/backend.ai/issues/1993))
* Add max_pending_session_count field to Keypair resource policy GQL schema ([#2013](https://github.com/lablup/backend.ai/issues/2013))
* Handle container creation exception and start exception in separate try-except contexts. ([#2316](https://github.com/lablup/backend.ai/issues/2316))
* Fix broken the workflow call for the action that auto-assigns PR numbers to news fragments ([#2358](https://github.com/lablup/backend.ai/issues/2358))
* Finally stabilize the hanging tests in our CI due to docker-internal races on TCP port mappings to concurrently spawned fixture containers by introducing monotonically increasing TCP port numbers ([#2379](https://github.com/lablup/backend.ai/issues/2379))
* Further improve the monotonic port allocation logic for the test containers to remove maximum concurrency restrictions ([#2396](https://github.com/lablup/backend.ai/issues/2396))
* Add PEX, SCIE binary build configs for the plugin subsystem. ([#2422](https://github.com/lablup/backend.ai/issues/2422))
* * Add POST `/folders` API endpoints to replace DELETE APIs that require request body.
  * Allow `DELETE` requests to have body data. ([#2571](https://github.com/lablup/backend.ai/issues/2571))
* Enhacne type hints for potential `None` arguments ([#2580](https://github.com/lablup/backend.ai/issues/2580))
* Add `ai.backend.manager.models.graphql` module for better code base management. ([#2669](https://github.com/lablup/backend.ai/issues/2669))
* Remove Scheduler related types that are no longer used. ([#2705](https://github.com/lablup/backend.ai/issues/2705))
* Allow adding required GQL field argument to schema. ([#2712](https://github.com/lablup/backend.ai/issues/2712))
* Upgrade `readthedocs` build environment to Python 3.12 ([#2814](https://github.com/lablup/backend.ai/issues/2814))## 24.03.0rc1 (2024-03-31)

### Features
* Allw filter `compute_session` query by `user_id`. ([#1805](https://github.com/lablup/backend.ai/issues/1805))
* Allow overriding vfolder mount permissions in API calls and CLI commands to create new sessions, with addition of a generic parser of comma-separated "key=value" list for CLI args and API params ([#1838](https://github.com/lablup/backend.ai/issues/1838))
* Always enable `ai.backend.accelerator.cuda_open` in the scie-based installer ([#1966](https://github.com/lablup/backend.ai/issues/1966))
* Use `config["pipeline"]["endpoint"]` as default value of `config["pipeline"]["frontend-endpoint"]` when not provided ([#1972](https://github.com/lablup/backend.ai/issues/1972))
* Migrate container registry config storage from `Etcd` to `PostgreSQL` ([#1917](https://github.com/lablup/backend.ai/issues/1917))
* Implement ID-based client workflow to ContainerRegistry API. ([#2615](https://github.com/lablup/backend.ai/issues/2615))
* Rafactor Base ContainerRegistry's `scan_tag` and implement `MEDIA_TYPE_DOCKER_MANIFEST` type handling. ([#2620](https://github.com/lablup/backend.ai/issues/2620))
* Support GitHub Container Registry. ([#2621](https://github.com/lablup/backend.ai/issues/2621))
* Support GitLab Container Registry. ([#2622](https://github.com/lablup/backend.ai/issues/2622))
* Support AWS ECR Public Container Registry. ([#2623](https://github.com/lablup/backend.ai/issues/2623))
* Support AWS ECR Private Container Registry. ([#2624](https://github.com/lablup/backend.ai/issues/2624))
* Replace rescan command's `--local` flag with local container registry record. ([#2665](https://github.com/lablup/backend.ai/issues/2665))
* Add `project` column to the images table and refactoring `ImageRef` logic. ([#2707](https://github.com/lablup/backend.ai/issues/2707))
* Support docker image manifest v2 schema1. ([#2815](https://github.com/lablup/backend.ai/issues/2815))
* Add `filter` and `order` parameters to Group GQL Relay API. ([#2863](https://github.com/lablup/backend.ai/issues/2863))
* Add `vast_use_auth_token` config to utilize VASTData API token optionally. ([#2901](https://github.com/lablup/backend.ai/issues/2901))
* Use a valid value for the `id` field in the GQL schema query resolver for `ContainerRegistry`. ([#2908](https://github.com/lablup/backend.ai/issues/2908))


### Fixes
* Set single agent per kernel resource usage. ([#1725](https://github.com/lablup/backend.ai/issues/1725))
* Abort container creation when duplicate container port definition exists ([#1750](https://github.com/lablup/backend.ai/issues/1750))
* To update image metadata, check if the min/max values in `resource_limits` are undefined. ([#1941](https://github.com/lablup/backend.ai/issues/1941))
* Explicitly disable the user-site package detection in the krunner python commands to avoid potential conflicts with user-installed packages in `.local` directories ([#1962](https://github.com/lablup/backend.ai/issues/1962))
* Fix `caf54fcc17ab` migration to drop a primary key only if it exists and in `589c764a18f1` migration, add missing table arguments. ([#1963](https://github.com/lablup/backend.ai/issues/1963))
* Explicitly wait for readiness of the Docker daemon and the compose stack before pouring database fixtures in `install-dev.sh` for when installing at the provisioning stage of Codespaces and integration tests in CI. ([#2378](https://github.com/lablup/backend.ai/issues/2378))
* Add missing implementation of wsproxy and manager CLI's log-level customization options ([#2698](https://github.com/lablup/backend.ai/issues/2698))
* Add missing batch execution call after session starts ([#2884](https://github.com/lablup/backend.ai/issues/2884))
* Fix a regression of the unicode-aware slug update that prevented creation of dot-prefixed (automount) vfolders ([#2892](https://github.com/lablup/backend.ai/issues/2892))
* Fix invalid image format log spam in Agent ([#2894](https://github.com/lablup/backend.ai/issues/2894))
* Fix wrong creation of `raw_configs` in `_create_kernels_in_one_agent` ([#2896](https://github.com/lablup/backend.ai/issues/2896))
* Assign valid value to `id` field in `ContainerRegistryNode` GQL schema query resolver. ([#2899](https://github.com/lablup/backend.ai/issues/2899))
* Update vast quota rather than raise error when quota exists. ([#2900](https://github.com/lablup/backend.ai/issues/2900))
* Calculate correct expiration time of VAST auth token and add `vast_force_login` config to enable login before every REST API call ([#2911](https://github.com/lablup/backend.ai/issues/2911))

### Documentation Updates
* Update docstrings in `ai.backend.client.request.Request:fetch()` and `ai.backend.client.request.FetchContextManager` as the support for synchronous context manager has been deprecated. ([#1801](https://github.com/lablup/backend.ai/issues/1801))
* Resize font-size of footer text in ethical ads in documentation hosted by read-the-docs ([#1965](https://github.com/lablup/backend.ai/issues/1965))
* Only resize font-size of footer text in ethical ads not in title of content in documentation ([#1967](https://github.com/lablup/backend.ai/issues/1967))

### Miscellaneous
* Revert response type of service create API. ([#1979](https://github.com/lablup/backend.ai/issues/1979))


## 24.09.0rc1 (2024-10-21)

### Features
* Migrate container registry config storage from `Etcd` to `PostgreSQL` ([#1917](https://github.com/lablup/backend.ai/issues/1917))
* Implement ID-based client workflow to ContainerRegistry API. ([#2615](https://github.com/lablup/backend.ai/issues/2615))
* Rafactor Base ContainerRegistry's `scan_tag` and implement `MEDIA_TYPE_DOCKER_MANIFEST` type handling. ([#2620](https://github.com/lablup/backend.ai/issues/2620))
* Support GitHub Container Registry. ([#2621](https://github.com/lablup/backend.ai/issues/2621))
* Support GitLab Container Registry. ([#2622](https://github.com/lablup/backend.ai/issues/2622))
* Support AWS ECR Public Container Registry. ([#2623](https://github.com/lablup/backend.ai/issues/2623))
* Support AWS ECR Private Container Registry. ([#2624](https://github.com/lablup/backend.ai/issues/2624))
* Replace rescan command's `--local` flag with local container registry record. ([#2665](https://github.com/lablup/backend.ai/issues/2665))
* Add `project` column to the images table and refactoring `ImageRef` logic. ([#2707](https://github.com/lablup/backend.ai/issues/2707))
* Support docker image manifest v2 schema1. ([#2815](https://github.com/lablup/backend.ai/issues/2815))
* Add `filter` and `order` parameters to Group GQL Relay API. ([#2863](https://github.com/lablup/backend.ai/issues/2863))
* Add `vast_use_auth_token` config to utilize VASTData API token optionally. ([#2901](https://github.com/lablup/backend.ai/issues/2901))
* Use a valid value for the `id` field in the GQL schema query resolver for `ContainerRegistry`. ([#2908](https://github.com/lablup/backend.ai/issues/2908))

### Fixes
* Explicitly wait for readiness of the Docker daemon and the compose stack before pouring database fixtures in `install-dev.sh` for when installing at the provisioning stage of Codespaces and integration tests in CI. ([#2378](https://github.com/lablup/backend.ai/issues/2378))
* Add missing implementation of wsproxy and manager CLI's log-level customization options ([#2698](https://github.com/lablup/backend.ai/issues/2698))
* Add missing batch execution call after session starts ([#2884](https://github.com/lablup/backend.ai/issues/2884))
* Fix a regression of the unicode-aware slug update that prevented creation of dot-prefixed (automount) vfolders ([#2892](https://github.com/lablup/backend.ai/issues/2892))
* Fix invalid image format log spam in Agent ([#2894](https://github.com/lablup/backend.ai/issues/2894))
* Fix wrong creation of `raw_configs` in `_create_kernels_in_one_agent` ([#2896](https://github.com/lablup/backend.ai/issues/2896))
* Assign valid value to `id` field in `ContainerRegistryNode` GQL schema query resolver. ([#2899](https://github.com/lablup/backend.ai/issues/2899))
* Update vast quota rather than raise error when quota exists. ([#2900](https://github.com/lablup/backend.ai/issues/2900))
* Calculate correct expiration time of VAST auth token and add `vast_force_login` config to enable login before every REST API call ([#2911](https://github.com/lablup/backend.ai/issues/2911))


## 24.09.0b1 (2024-09-30)

### Features
* Add support for optional payload encryption in the client SDK and CLI as a follow-up to #484 ([#493](https://github.com/lablup/backend.ai/issues/493))
* Allow unicode characters in project(user group) name and domain name. ([#1663](https://github.com/lablup/backend.ai/issues/1663))
* Improve exception logging stability by pre-formatting exception objects instead of pickling/unpickling them ([#1759](https://github.com/lablup/backend.ai/issues/1759))
* Add new API to create new image from live session ([#1973](https://github.com/lablup/backend.ai/issues/1973))
* Clear `error_logs` records in the `clear-history` command ([#1989](https://github.com/lablup/backend.ai/issues/1989))
* Introduce `mgr schema dump-history` and `mgr schema apply-missing-revisions` command to ease the major upgrade involving deviation of database migration histories ([#2002](https://github.com/lablup/backend.ai/issues/2002))
* Update `image forget` CLI command to untag image from registry before forgetting it from the database ([#2010](https://github.com/lablup/backend.ai/issues/2010))
* Update `etcd-client-py` to 0.3.0 ([#2014](https://github.com/lablup/backend.ai/issues/2014))
* Allow self-ssh in single-node single-container compute sessions. ([#2032](https://github.com/lablup/backend.ai/issues/2032))
* Prevent deleting mounted folders. ([#2036](https://github.com/lablup/backend.ai/issues/2036))
* Allow agent to report its internal registry snapshot via UNIX domain socket server ([#2038](https://github.com/lablup/backend.ai/issues/2038))
* New redis client (experimental) ([#2041](https://github.com/lablup/backend.ai/issues/2041))
* Expose user info to environment variables ([#2043](https://github.com/lablup/backend.ai/issues/2043))
* Introduce the `rolling_count` GraphQL field to provide the current rate limit counter for a keypair within the designated time window slice ([#2050](https://github.com/lablup/backend.ai/issues/2050))
* Deprecate the reliance on HTTP cookies for authenticating the pipeline service, switching to the use of HTTP headers instead ([#2051](https://github.com/lablup/backend.ai/issues/2051))
* Allow user to explicitly set filename of model definition YAML ([#2063](https://github.com/lablup/backend.ai/issues/2063))
* Add the `backend.ai plugin scan` command to inspect the plugin scan results from various entrypoint sources ([#2070](https://github.com/lablup/backend.ai/issues/2070))
* Bring back etcetra-backed Etcd as an option for ditributed lock backend ([#2079](https://github.com/lablup/backend.ai/issues/2079))
* Enable distribute-lock configuration ([#2080](https://github.com/lablup/backend.ai/issues/2080))
* Cache volume objects in `RootContext.get_volume` ([#2081](https://github.com/lablup/backend.ai/issues/2081))
* Revamp images GQL query by changing image filtering from flag-based to feature set-based and add `aliases` field to customized image GQL schema ([#2136](https://github.com/lablup/backend.ai/issues/2136))
* Added missing fields for `keypair_resource_policy` in client-py, models, etc. ([#2146](https://github.com/lablup/backend.ai/issues/2146))
* Add parameters to `check-presets` SDK function ([#2153](https://github.com/lablup/backend.ai/issues/2153))
* Add relay-aware `VirtualFolderNode` GQL Query ([#2165](https://github.com/lablup/backend.ai/issues/2165))
* Also perform basic model service validation process when updating model service via `ModifyEndpoint` ([#2167](https://github.com/lablup/backend.ai/issues/2167))
* Add support for mounting arbitrary VFolders on model service session ([#2168](https://github.com/lablup/backend.ai/issues/2168))
* Add support for CentOS 8 based kernels ([#2220](https://github.com/lablup/backend.ai/issues/2220))
* Clear zombie routes automatically ([#2229](https://github.com/lablup/backend.ai/issues/2229))
* Add `scaling_group.agent_count_by_status` and `scaling_group.agent_total_resource_slots_by_status` GQL fields to query the count and the resource allocation of agents that belong to a scaling group. ([#2254](https://github.com/lablup/backend.ai/issues/2254))
* Allow modifying model service session's environment variable setup ([#2255](https://github.com/lablup/backend.ai/issues/2255))
* Add `endpoint.runtime_variant` column ([#2256](https://github.com/lablup/backend.ai/issues/2256))
* Add new API to show list of supported inference runtimes ([#2258](https://github.com/lablup/backend.ai/issues/2258))
* Add support for model service provisioning without `model-definition.yaml` ([#2260](https://github.com/lablup/backend.ai/issues/2260))
* Allow superadmins to force-update session status through destroy API. ([#2275](https://github.com/lablup/backend.ai/issues/2275))
* Add session status check & update API. ([#2312](https://github.com/lablup/backend.ai/issues/2312))
* Add support for fetching container logs of a specific kernel. ([#2364](https://github.com/lablup/backend.ai/issues/2364))
* Introduce Python native WSProxy ([#2372](https://github.com/lablup/backend.ai/issues/2372))
* Implement scanning plugin entrypoints of external packages ([#2377](https://github.com/lablup/backend.ai/issues/2377))
* Add `row_id`, `type` and `container_registry` fields to the `GroupNode` GQL schema. ([#2409](https://github.com/lablup/backend.ai/issues/2409))
* Add support for PureStorage RapidFiles Toolkit v2 ([#2419](https://github.com/lablup/backend.ai/issues/2419))
* Add API that extends lifespan of webserver's login session. ([#2456](https://github.com/lablup/backend.ai/issues/2456))
* Allow bulk association and disassociation of scaling groups with domains, user groups, and key pairs. ([#2473](https://github.com/lablup/backend.ai/issues/2473))
* Match container's timezone to container host OS when available ([#2503](https://github.com/lablup/backend.ai/issues/2503))
* Add a pre-setup configuration menu to the TUI installer to allow setting the public-facing address of Backend.AI components ([#2541](https://github.com/lablup/backend.ai/issues/2541))
* Now Backend.AI can run arbitrary container images without Backend.AI-specific metadata labels by introducing good default values and replacing intrinsic kernel-runner binaries with statically built ones ([#2582](https://github.com/lablup/backend.ai/issues/2582))
* Allow `Bearer` as valid token type on model service authentication ([#2583](https://github.com/lablup/backend.ai/issues/2583))
* Introduce automatic creation of a 'model-store' group upon inserting a new domain. ([#2611](https://github.com/lablup/backend.ai/issues/2611))
* Add support for declaring custom description field for GraphQL `relay` edge types. ([#2643](https://github.com/lablup/backend.ai/issues/2643))
* Add an `enable_LLM_playground` option to show/hide the LLM playground tab on the serving page. ([#2677](https://github.com/lablup/backend.ai/issues/2677))
* Add `max_gaudi2_devices_per_container` config on webserver ([#2685](https://github.com/lablup/backend.ai/issues/2685))
* Add `max_atom_plus_device_per_container` config on webserver ([#2686](https://github.com/lablup/backend.ai/issues/2686))
* Introduce Account-manager component. ([#2688](https://github.com/lablup/backend.ai/issues/2688))
* * Add query depth limit config of GQL.
  * Add page size limit config of GQL Connection.
  * Set default page size of GQL Connection to 10. ([#2709](https://github.com/lablup/backend.ai/issues/2709))
* Add compute session GQL Relay query schema. ([#2711](https://github.com/lablup/backend.ai/issues/2711))
* Allow `DataLoaderManager` to get a loader function by function itself rather than function name. ([#2717](https://github.com/lablup/backend.ai/issues/2717))
* Allow filter and order in endpointlist gql request. ([#2723](https://github.com/lablup/backend.ai/issues/2723))
* Add new vfolder API to update sharing status. ([#2740](https://github.com/lablup/backend.ai/issues/2740))
* Avoid raising a type error even if a particular table in the toml file is empty, as long as the default value for all settings exists. ([#2782](https://github.com/lablup/backend.ai/issues/2782))
* Add an explicit configuration `scaling-group-type` to `agent.toml` so that the agent could distinguish whether itself belongs to an SFTP resource group or not ([#2796](https://github.com/lablup/backend.ai/issues/2796))
* Add per-session priority attributes and `ModifyComputeSession` GraphQL mutation to update session names and priorities ([#2840](https://github.com/lablup/backend.ai/issues/2840))
* Add dependee/dependent/graph ComputeSessionNode connection queries ([#2844](https://github.com/lablup/backend.ai/issues/2844))
* Implement the priority-aware scheduler that applies to any arbitrary scheduler plugin ([#2848](https://github.com/lablup/backend.ai/issues/2848))
* Add support for setting a timeout when pulling Docker images and upgrade aiodocker to version 0.23.0. ([#2852](https://github.com/lablup/backend.ai/issues/2852))

### Improvements
* Enable robust DB connection handling by allowing `pool-pre-ping` setting. ([#1991](https://github.com/lablup/backend.ai/issues/1991))
* Enhance update mechanism of session & kernel status. ([#2311](https://github.com/lablup/backend.ai/issues/2311))
* Remove database-level foreign key constraints in `vfolders.{user,group}` columns to decouple the timing of vfolder deletion and user/group deletion. ([#2404](https://github.com/lablup/backend.ai/issues/2404))
* Implement storage-host RBAC interface. ([#2505](https://github.com/lablup/backend.ai/issues/2505))
* Optimize the query latency when fetching a large number of agents with stat metrics from Redis ([#2558](https://github.com/lablup/backend.ai/issues/2558))
* Split out `ai.backend.logging` package from the `ai.backend.common` to improve reusability and reduce the startup time (i.e., import latencies) ([#2760](https://github.com/lablup/backend.ai/issues/2760))
* Avoid using `collections.OrderedDict` when not necessary in the manager API and client SDK ([#2842](https://github.com/lablup/backend.ai/issues/2842))

### Deprecations
* Remove no longer used `env-tester-{admin,user,user2}.sh` scripts and all references ([#1956](https://github.com/lablup/backend.ai/issues/1956))

### Fixes
* Merge `kernels.role` into `sessions.session_type` and check the image compatibility based on comparison with the `ai.backend.role` label ([#1587](https://github.com/lablup/backend.ai/issues/1587))
* Refactor `PendingSession` Scheduler into `PendingSession` scheduler and `AgentSelector`, and replace `roundrobin` flag with `AgentSelectionStrategy.RoundRobin` policy. ([#1655](https://github.com/lablup/backend.ai/issues/1655))
* Do not omit to update session's occupying resources to DB when a kernel starts. ([#1832](https://github.com/lablup/backend.ai/issues/1832))
* Fix DDN command output handling when exceeding quotas. ([#1901](https://github.com/lablup/backend.ai/issues/1901))
* Explicitly specify the storage-side UID/GID when creating qtrees in the NetApp storage backend ([#1983](https://github.com/lablup/backend.ai/issues/1983))
* Sync mismatch between `kernels.session_name` and `sessions.name` and fix session-rename API to update `session_name` of sibling kernels atomically. ([#1985](https://github.com/lablup/backend.ai/issues/1985))
* Change function default arguments from mutable object to `None`. ([#1986](https://github.com/lablup/backend.ai/issues/1986))
* Revert some VFolder APIs response type to remove mismatch between `Content-Type` header and body. ([#1988](https://github.com/lablup/backend.ai/issues/1988))
* Upgrade pants to 2.21.0.dev4 for Python 3.12 support in their embedded pex/pip versions ([#1998](https://github.com/lablup/backend.ai/issues/1998))
* Fix Graylog log adapter not working after upgrading to Python 3.12 ([#1999](https://github.com/lablup/backend.ai/issues/1999))
* Fix `compute_container` GraphQL query resolver functions. ([#2012](https://github.com/lablup/backend.ai/issues/2012))
* Fix harbor v2 image scanner skipping importing rest of the artifacts when any of the item does not include tag ([#2015](https://github.com/lablup/backend.ai/issues/2015))
* Let external log viewers display more accurate, meaningful stack frames of logger invocations. ([#2019](https://github.com/lablup/backend.ai/issues/2019))
* Fix handling of undefined values in the ModifyImage GraphQL mutation. ([#2028](https://github.com/lablup/backend.ai/issues/2028))
* Fix container commit not working on certain docker engine versions ([#2040](https://github.com/lablup/backend.ai/issues/2040))
* add omitted request fetching from client to manager about deleting vfolder in trash bin. ([#2042](https://github.com/lablup/backend.ai/issues/2042))
* Fix a buggy restriction on VFolder deletion due to wrong query condition ([#2055](https://github.com/lablup/backend.ai/issues/2055))
* Fix wrong usage of dataloader in GQL group resolver. ([#2056](https://github.com/lablup/backend.ai/issues/2056))
* Ensure that vfolders, including automount vfolders, are mounted during session creation only if their status is not set to "DEAD" (i.e., deleted). ([#2059](https://github.com/lablup/backend.ai/issues/2059))
* Fix wrong calculation of resource usage ([#2062](https://github.com/lablup/backend.ai/issues/2062))
* Fix VFolder file operation not working when user has been granted access to shared but deleted VFolder which has same name with the normal one ([#2072](https://github.com/lablup/backend.ai/issues/2072))
* Add missing type argument in group query ([#2073](https://github.com/lablup/backend.ai/issues/2073))
* Let the `backend.ai mgr clear-history` command clears session records as well as kernel records ([#2077](https://github.com/lablup/backend.ai/issues/2077))
* Fix `compute_session_list` GQL query not responding on an abundant amount of sessions ([#2084](https://github.com/lablup/backend.ai/issues/2084))
* Fix VFolder invitation not accepted when inviting VFolder shares name with already deleted one ([#2093](https://github.com/lablup/backend.ai/issues/2093))
* Fix orphan model service routes being created ([#2096](https://github.com/lablup/backend.ai/issues/2096))
* Fix initialization of the resource usage API's kernel-level usage aggregation ([#2102](https://github.com/lablup/backend.ai/issues/2102))
* Fix model server starting on every kernels (including sub role kernels) on multi container infernce session ([#2124](https://github.com/lablup/backend.ai/issues/2124))
* Add missing `commit_session_to_file` to `OP_EXC` ([#2127](https://github.com/lablup/backend.ai/issues/2127))
* Fix wrong SQL query build for GQL Relay node ([#2128](https://github.com/lablup/backend.ai/issues/2128))
* Pass ImageRef.canonical in `commit_session_to_file` ([#2134](https://github.com/lablup/backend.ai/issues/2134))
* Handle fileset-already-exists response of `create-filset` API request and make sure to wait between all GPFS job polling iterations ([#2144](https://github.com/lablup/backend.ai/issues/2144))
* Skip any possible redundant quota update requests when creating new quota ([#2145](https://github.com/lablup/backend.ai/issues/2145))
* * Fix error when calling `check_presets` Client SDK API with an invalid `group` parameter 
  * Rewrite Client SDK to access all APIConfig fields ([#2152](https://github.com/lablup/backend.ai/issues/2152))
* Ensure that all pending sessions are picked by schedulers ([#2155](https://github.com/lablup/backend.ai/issues/2155))
* Fix user creation error when any model-store does not exists. ([#2160](https://github.com/lablup/backend.ai/issues/2160))
* Fix buggy resolver of `model_card` GQL Query. ([#2161](https://github.com/lablup/backend.ai/issues/2161))
* Fix security vulnerability for `sudo_session_enabled` ([#2162](https://github.com/lablup/backend.ai/issues/2162))
* Rename `endpoints.model_mount_destiation` to `model_mount_destination` ([#2163](https://github.com/lablup/backend.ai/issues/2163))
* Wait for real quota scope directory creation after Netapp `create_qtree()` call ([#2170](https://github.com/lablup/backend.ai/issues/2170))
* Fix wrong per-user concurrency calculation logic ([#2175](https://github.com/lablup/backend.ai/issues/2175))
* Keep `sync_container_lifecycles()` bgtask alive in a loop. ([#2178](https://github.com/lablup/backend.ai/issues/2178))
* Fix missing check for group (project) vfolder count limit and error handling with an invalid `group` parameter ([#2190](https://github.com/lablup/backend.ai/issues/2190))
* Fix model service persisting on `degraded` status forever in rare chance when trying to delete the service ([#2191](https://github.com/lablup/backend.ai/issues/2191))
* Fix error when query or mutate GraphQL using `BigInt` field type ([#2203](https://github.com/lablup/backend.ai/issues/2203))
* Ensure that utilization idleness is checked after a set period. ([#2205](https://github.com/lablup/backend.ai/issues/2205))
* Fix `backend.ai ssh` command execution when packaged as SCIE/PEX ([#2226](https://github.com/lablup/backend.ai/issues/2226))
* * fix `endpoints` query not working when trying to load `image_row.aliases`
  * fix `endpoints.status` reporting `PROVISIONING` when its status is in `DESTROYING` state ([#2233](https://github.com/lablup/backend.ai/issues/2233))
* Fix GQL raising error when trying to resolve `endpoints.errors` field occasionally ([#2236](https://github.com/lablup/backend.ai/issues/2236))
* Fix `ZeroDivisionError` in volume usage calculation by returning 0% when volume capacity is zero ([#2245](https://github.com/lablup/backend.ai/issues/2245))
* Fix GraphQL to support query to non-installed images ([#2250](https://github.com/lablup/backend.ai/issues/2250))
* Add missing `push_image` method implementation to Dummy Agent ([#2253](https://github.com/lablup/backend.ai/issues/2253))
* Rename no-op `access_key` parameter of `endpoint_list` GQL Query to `user_uuid` ([#2287](https://github.com/lablup/backend.ai/issues/2287))
* Fix `ai.backend.service-ports` label syntax broken when image does not expose built-in service port ([#2288](https://github.com/lablup/backend.ai/issues/2288))
* Improve stability of `untag_image_from_registry` mutation ([#2289](https://github.com/lablup/backend.ai/issues/2289))
* SSH not working between kernels started with customized image ([#2290](https://github.com/lablup/backend.ai/issues/2290))
* Invalid container memory capacity reported ([#2291](https://github.com/lablup/backend.ai/issues/2291))
* Corrected an issue where the `resource_policy` field in the user model was incorrectly mapped to `domain_name`. ([#2314](https://github.com/lablup/backend.ai/issues/2314))
* Omit to clean containerless kernels which are still creating its container. ([#2317](https://github.com/lablup/backend.ai/issues/2317))
* Fix model service sessions created before 24.03.5 failing to spawn ([#2318](https://github.com/lablup/backend.ai/issues/2318))
* Image commit not working ([#2319](https://github.com/lablup/backend.ai/issues/2319))
* model service session scheduler (`scale_services()`) failing when sessions bound to active route already marked as terminated ([#2320](https://github.com/lablup/backend.ai/issues/2320))
* Fix container metric collection halted on systems with Cgroups v1 ([#2321](https://github.com/lablup/backend.ai/issues/2321))
* Run batch execution after the batch session starts. ([#2327](https://github.com/lablup/backend.ai/issues/2327))
* Add support for configuring `sync_container_lifecycles()` task. ([#2338](https://github.com/lablup/backend.ai/issues/2338))
* Fix mismatches between responses of `/services/_runtimes` and new model service creation input ([#2371](https://github.com/lablup/backend.ai/issues/2371))
* Fix incorrect check of values returned from docker stat API. ([#2389](https://github.com/lablup/backend.ai/issues/2389))
* Shutdown agent properly by removing a code that waits a cancelled task. ([#2392](https://github.com/lablup/backend.ai/issues/2392))
* Restrict GraphQL query to `user_nodes` field to require `superadmin` privilege ([#2401](https://github.com/lablup/backend.ai/issues/2401))
* Handle all possible exceptions when scheduling single node session so that the status information of pending session is not empty. ([#2411](https://github.com/lablup/backend.ai/issues/2411))
* Utilize `ExtendedJSONEncoder` for error logging to handle `UUID` objects in `extra_data` ([#2415](https://github.com/lablup/backend.ai/issues/2415))
* Change outdated references in event module from `kernels` to `sessions`. ([#2421](https://github.com/lablup/backend.ai/issues/2421))
* Upgrade `inquirer` to remove dependency on deprecated `distutils`, which breaks up execution of the scie builds ([#2424](https://github.com/lablup/backend.ai/issues/2424))
* Allow specific status of vfolders to query to purge. ([#2429](https://github.com/lablup/backend.ai/issues/2429))
* Update the install-dev scripts to use `pnpm` instead of `npm` to speed up installation and resolve some peculiar version resolution issues related to esbuild. ([#2436](https://github.com/lablup/backend.ai/issues/2436))
* Fix a packaging issue in the `backendai-webserver` scie executable due to missing explicit requirement of setuptools ([#2454](https://github.com/lablup/backend.ai/issues/2454))
* Improve pruning of non-physical filesystems when measuring disk usage in agents ([#2460](https://github.com/lablup/backend.ai/issues/2460))
* Update the install-dev scripts to install `pnpm` if pnpm isn't installed. ([#2472](https://github.com/lablup/backend.ai/issues/2472))
* Improve error handling of initialization failures in the kernel runner ([#2478](https://github.com/lablup/backend.ai/issues/2478))
* Fix `BACKEND_MODEL_NAME` environment always overwritten to model name specified at model definition ([#2481](https://github.com/lablup/backend.ai/issues/2481))
* Do not allow assigning preopen port which collides with image's own service port definition ([#2482](https://github.com/lablup/backend.ai/issues/2482))
* Fix GET requests with queryparams defined in API spec occasionally throwing 400 Bad Request error ([#2483](https://github.com/lablup/backend.ai/issues/2483))
* Check null value of user mutation by `Undefined` sentinel value rather than `None`. ([#2506](https://github.com/lablup/backend.ai/issues/2506))
* Do null check on `groups.total_resource_slots` and `domains.total_resource_slots` value. ([#2509](https://github.com/lablup/backend.ai/issues/2509))
* Fix hearbeat processing failing when agent reports image with its name not compilant to Backend.AI's naming rule ([#2516](https://github.com/lablup/backend.ai/issues/2516))
* Corrected a typo (`maanger` corrected to `manager`) in the `check_status()` API response of the storage component ([#2523](https://github.com/lablup/backend.ai/issues/2523))
* Rename `images.image_filters` GQL Query argument to `images.image_types` ([#2555](https://github.com/lablup/backend.ai/issues/2555))
* Prevent session status from being transit to `PULLING` status event if image pull is not required ([#2556](https://github.com/lablup/backend.ai/issues/2556))
* Prevent other user's customized image from being listed as a response of `images` GQL query ([#2557](https://github.com/lablup/backend.ai/issues/2557))
* skip resolving malformed `ModelCard` GQL item ([#2570](https://github.com/lablup/backend.ai/issues/2570))
* Delete sessions DB records when purging project. ([#2573](https://github.com/lablup/backend.ai/issues/2573))
* Initialize Redis connection pool objects with specified connection opts rather than ignoring them. ([#2574](https://github.com/lablup/backend.ai/issues/2574))
* Fix `GET /func/folders/{folderName}` API returning string literal `"null"` instead of null value on `user` and `group` fields ([#2584](https://github.com/lablup/backend.ai/issues/2584))
* Update `GQLPrivilegeCheckMiddleware` to align with upstream changes on `graphql-core` package ([#2598](https://github.com/lablup/backend.ai/issues/2598))
* Robust type check when idle checker fetches utilization data. ([#2601](https://github.com/lablup/backend.ai/issues/2601))
* Skip mounting zero-byte lxcfs files when lxcfs is activated to prevent crashes in session containers ([#2604](https://github.com/lablup/backend.ai/issues/2604))
* Fix typo in minilang query field spec and column map. ([#2605](https://github.com/lablup/backend.ai/issues/2605))
* Remove duplicate CPU quota arguments when creating containers ([#2608](https://github.com/lablup/backend.ai/issues/2608))
* Increase `MAX_CMD_LEN` of dropbear to improve compatibility with PyCharm debugger ([#2613](https://github.com/lablup/backend.ai/issues/2613))
* Silence falsy Redis timeout warnings when retrying blocking commands if the timeout does not exceed the expected command timeout ([#2632](https://github.com/lablup/backend.ai/issues/2632))
* Fix a regression of #2483 in the session-download API used by the `backend.ai ssh` command ([#2635](https://github.com/lablup/backend.ai/issues/2635))
* Implement missing `StrEnumType` handling in `populate_fixture()`. ([#2648](https://github.com/lablup/backend.ai/issues/2648))
* Let `GET /resource/usage/period` request contain data in query parameter rather than JSON body. ([#2661](https://github.com/lablup/backend.ai/issues/2661))
* Allow sudo-enabled container users to ovewrite `/usr/bin/scp` and `/usr/libexec/sftp-server` by unifying the intrinsic ssh binaries to use the merged `dropbearmulti` executable. ([#2667](https://github.com/lablup/backend.ai/issues/2667))
* Update `webserver` logout API to respond with HTTP 200 OK ([#2681](https://github.com/lablup/backend.ai/issues/2681))
* Fix WSProxy not properly handling WebSocket request sent from Firefox ([#2684](https://github.com/lablup/backend.ai/issues/2684))
* Scan parent directory of created qtree to avoid creating quota on non-existing directory. ([#2696](https://github.com/lablup/backend.ai/issues/2696))
* Fix `list_files`, `get_fstab_contents`, `get_performance_metric` and `shared_vfolder_info` Python SDK function not working with `ValidationError` exception printed ([#2706](https://github.com/lablup/backend.ai/issues/2706))
* Resolve the issue where the vfolder id does not match in `list_shared_vfolders`. ([#2731](https://github.com/lablup/backend.ai/issues/2731))
* Handle OS Error when deleting vfolders. ([#2741](https://github.com/lablup/backend.ai/issues/2741))
* Fix typo in Virtual-folder status update code. ([#2742](https://github.com/lablup/backend.ai/issues/2742))
* Correct `msgpack` deserialization of `ResourceSlot`. ([#2754](https://github.com/lablup/backend.ai/issues/2754))
* Fix regression error of `session create_from_template` command. ([#2761](https://github.com/lablup/backend.ai/issues/2761))
* Silence `model_` namespace warnings with pydantic-based model classes ([#2765](https://github.com/lablup/backend.ai/issues/2765))
* Change the initialization order of PackageContext to apply `target_path` correctly in the TUI installer ([#2768](https://github.com/lablup/backend.ai/issues/2768))
* Make the regex patterns to update configuration files working with multiline texts correctly in the TUI installer ([#2771](https://github.com/lablup/backend.ai/issues/2771))
* Omit null parameter when call `usage-per-period` API. ([#2777](https://github.com/lablup/backend.ai/issues/2777))
* Delete vfolder invitation and permission rows when deleting vfolders. ([#2780](https://github.com/lablup/backend.ai/issues/2780))
* Handle container port mismatch when creating kernel. ([#2786](https://github.com/lablup/backend.ai/issues/2786))
* Explicitly set the protected service ports depending on the resource group type and the service types ([#2797](https://github.com/lablup/backend.ai/issues/2797))
* Correct session status determiner function. ([#2803](https://github.com/lablup/backend.ai/issues/2803))
* Fix `endpoint_list.total_count` GQL field returning incorrect value ([#2805](https://github.com/lablup/backend.ai/issues/2805))
* Fix `Service.create()` SDK method and `service create` CLI command not working with `UnboundLocalError` exception ([#2806](https://github.com/lablup/backend.ai/issues/2806))
* Refresh expiration time of login session when login. ([#2816](https://github.com/lablup/backend.ai/issues/2816))
* Fix `kernel_id` assignment for main kernel log retrieval ([#2820](https://github.com/lablup/backend.ai/issues/2820))
* Use a safer TLS version (v1.2) when creating SSL sockets in the logstash handler ([#2827](https://github.com/lablup/backend.ai/issues/2827))
* Wrong count of concurrent compute sessions. ([#2829](https://github.com/lablup/backend.ai/issues/2829))
* Create kernels with correct `scaling_group` value. ([#2837](https://github.com/lablup/backend.ai/issues/2837))
* Fix a regression in progress bar rendering of the TUI installer after upgrading the Textual library ([#2867](https://github.com/lablup/backend.ai/issues/2867))

### Documentation Updates
* Add note about installing client library with same version as server ([#1976](https://github.com/lablup/backend.ai/issues/1976))
* Remove deprecated `version` from the docker compose YAML templates in package installation docs. ([#2035](https://github.com/lablup/backend.ai/issues/2035))
* Fix a typo in the `agent.toml` example of the package-based installation guide to have a duplicate double quote ([#2069](https://github.com/lablup/backend.ai/issues/2069))

### External Dependency Updates
* Upgrade the base runtime (CPython) version from 3.11.6 to 3.12.2 ([#1994](https://github.com/lablup/backend.ai/issues/1994))
* Upgrade aiodocker to v0.22.0 with minor bug fixes found by improved type annotations ([#2339](https://github.com/lablup/backend.ai/issues/2339))
* Update the halfstack containers to point the latest stable versions ([#2367](https://github.com/lablup/backend.ai/issues/2367))
* Upgrade aiodocker to 0.22.1 to fix error handling when trying to extract the log of non-existing containers ([#2402](https://github.com/lablup/backend.ai/issues/2402))
* Upgrade the base CPython from 3.12.2 to 3.12.4 ([#2449](https://github.com/lablup/backend.ai/issues/2449))
* Upgrade Python (3.12.4 -> 3.12.6) and common/tool dependencies to prepare for Python 3.13 and apply latest fixes ([#2851](https://github.com/lablup/backend.ai/issues/2851))

### Miscellaneous
* Wrap RPC authentication error to custom error for better logging. ([#1970](https://github.com/lablup/backend.ai/issues/1970))
* Add `requested_slots` field to compute session GQL type. ([#1984](https://github.com/lablup/backend.ai/issues/1984))
* Allow `pydantic.BaseModel` as the API handler return schema. ([#1987](https://github.com/lablup/backend.ai/issues/1987))
* Fix incorrect version notation of GQL Field. ([#1993](https://github.com/lablup/backend.ai/issues/1993))
* Add max_pending_session_count field to Keypair resource policy GQL schema ([#2013](https://github.com/lablup/backend.ai/issues/2013))
* Handle container creation exception and start exception in separate try-except contexts. ([#2316](https://github.com/lablup/backend.ai/issues/2316))
* Fix broken the workflow call for the action that auto-assigns PR numbers to news fragments ([#2358](https://github.com/lablup/backend.ai/issues/2358))
* Finally stabilize the hanging tests in our CI due to docker-internal races on TCP port mappings to concurrently spawned fixture containers by introducing monotonically increasing TCP port numbers ([#2379](https://github.com/lablup/backend.ai/issues/2379))
* Further improve the monotonic port allocation logic for the test containers to remove maximum concurrency restrictions ([#2396](https://github.com/lablup/backend.ai/issues/2396))
* Add PEX, SCIE binary build configs for the plugin subsystem. ([#2422](https://github.com/lablup/backend.ai/issues/2422))
* * Add POST `/folders` API endpoints to replace DELETE APIs that require request body.
  * Allow `DELETE` requests to have body data. ([#2571](https://github.com/lablup/backend.ai/issues/2571))
* Enhacne type hints for potential `None` arguments ([#2580](https://github.com/lablup/backend.ai/issues/2580))
* Add `ai.backend.manager.models.graphql` module for better code base management. ([#2669](https://github.com/lablup/backend.ai/issues/2669))
* Remove Scheduler related types that are no longer used. ([#2705](https://github.com/lablup/backend.ai/issues/2705))
* Allow adding required GQL field argument to schema. ([#2712](https://github.com/lablup/backend.ai/issues/2712))
* Upgrade `readthedocs` build environment to Python 3.12 ([#2814](https://github.com/lablup/backend.ai/issues/2814))## 24.03.0rc1 (2024-03-31)

### Features
* Allw filter `compute_session` query by `user_id`. ([#1805](https://github.com/lablup/backend.ai/issues/1805))
* Allow overriding vfolder mount permissions in API calls and CLI commands to create new sessions, with addition of a generic parser of comma-separated "key=value" list for CLI args and API params ([#1838](https://github.com/lablup/backend.ai/issues/1838))
* Always enable `ai.backend.accelerator.cuda_open` in the scie-based installer ([#1966](https://github.com/lablup/backend.ai/issues/1966))
* Use `config["pipeline"]["endpoint"]` as default value of `config["pipeline"]["frontend-endpoint"]` when not provided ([#1972](https://github.com/lablup/backend.ai/issues/1972))

### Fixes
* Set single agent per kernel resource usage. ([#1725](https://github.com/lablup/backend.ai/issues/1725))
* Abort container creation when duplicate container port definition exists ([#1750](https://github.com/lablup/backend.ai/issues/1750))
* To update image metadata, check if the min/max values in `resource_limits` are undefined. ([#1941](https://github.com/lablup/backend.ai/issues/1941))
* Explicitly disable the user-site package detection in the krunner python commands to avoid potential conflicts with user-installed packages in `.local` directories ([#1962](https://github.com/lablup/backend.ai/issues/1962))
* Fix `caf54fcc17ab` migration to drop a primary key only if it exists and in `589c764a18f1` migration, add missing table arguments. ([#1963](https://github.com/lablup/backend.ai/issues/1963))

### Documentation Updates
* Update docstrings in `ai.backend.client.request.Request:fetch()` and `ai.backend.client.request.FetchContextManager` as the support for synchronous context manager has been deprecated. ([#1801](https://github.com/lablup/backend.ai/issues/1801))
* Resize font-size of footer text in ethical ads in documentation hosted by read-the-docs ([#1965](https://github.com/lablup/backend.ai/issues/1965))
* Only resize font-size of footer text in ethical ads not in title of content in documentation ([#1967](https://github.com/lablup/backend.ai/issues/1967))

### Miscellaneous
* Revert response type of service create API. ([#1979](https://github.com/lablup/backend.ai/issues/1979))


## 24.03.0b1 (2024-03-14)

### Features
* Add a policy to predicate to limit the number and resources of concurrent pending sessions. ([#1226](https://github.com/lablup/backend.ai/issues/1226))
* Implement `/services/_/try` API ([#1754](https://github.com/lablup/backend.ai/issues/1754))
* Add support for multi directory mkdir by fixing cli to accept multiple arguments and by adding list type annotation to accept multiple directories ([#1803](https://github.com/lablup/backend.ai/issues/1803))
* Add GraphQL mutations to allow altering model service (endpoint) specs, especially for resource allocation and image enviroment setups ([#1859](https://github.com/lablup/backend.ai/issues/1859))
* Add a new client-side admin command group to manager the quota scopes (`admin quota-scope`), replacing the legacy `--quota` options in the vfolder management commands ([#1862](https://github.com/lablup/backend.ai/issues/1862))
* Implement customization of name displayed in the Graylog source field through the config file. ([#1866](https://github.com/lablup/backend.ai/issues/1866))
* Add `allow_non_auth_tcp` as allowed webui config key ([#1868](https://github.com/lablup/backend.ai/issues/1868))
* Introduce `etcd-client-py` ([#1870](https://github.com/lablup/backend.ai/issues/1870))
* Enhance logging by adding more detailed exceptions when scheduling sessions, such as conditions like missing kernels or no agents available at all for the selected pending session ([#1887](https://github.com/lablup/backend.ai/issues/1887))
* Add validate-image-canonical and validate-image-alias cli command ([#1891](https://github.com/lablup/backend.ai/issues/1891))
* Re-define vfolder delete status by adding `delete-pending`, `delete-error` vfolder status and set `delete-pending` as trash-bin status and `delete-complete` as hard-delete status. ([#1892](https://github.com/lablup/backend.ai/issues/1892))
* Add new test cases for vfolder CLI commands. ([#1918](https://github.com/lablup/backend.ai/issues/1918))
* Add the `--non-interactive` flag to the TUI installer ([#1922](https://github.com/lablup/backend.ai/issues/1922))
* Bump the manager API version to v8.20240315 with some big changes memo'ed in manager/server.py ([#1938](https://github.com/lablup/backend.ai/issues/1938))
* Add new `user_resource_policies.max_session_count_per_model_session` column to limit number of maximum available sessions per each model service created by user ([#1948](https://github.com/lablup/backend.ai/issues/1948))
* Add the --headless flag that run install as headless mode, skips terminal I/O ([#1958](https://github.com/lablup/backend.ai/issues/1958))

### Deprecations
* Remove the image importer API no longer used and unused since the release of Forklift ([#1896](https://github.com/lablup/backend.ai/issues/1896))

### Fixes
* Write graphene field's deprecation/description message string directly instead of using message generation functions. ([#1734](https://github.com/lablup/backend.ai/issues/1734))
* Let `mgr agent ping` command to use the agent's `ping()` RPC API instead of unimplemented `get_node_hwinfo()`, and fix the mis-interpretation of the compute plugin's metadata reports in the agent's `gather_hwinfo()`. ([#1793](https://github.com/lablup/backend.ai/issues/1793))
* When creating a new user via the client admin CLI, always set the default option of the group to "default" to prevent mistakes of creating users without groups. ([#1860](https://github.com/lablup/backend.ai/issues/1860))
* Fix malfunctioning CLI command `session create-from-template` by reorganizing `click.option` decorators ([#1890](https://github.com/lablup/backend.ai/issues/1890))
* Fix GQL Relay node resolver to parse `filter` and `order` argument into SQL query properly. ([#1916](https://github.com/lablup/backend.ai/issues/1916))
* Allow passing HTTP status codes via the pydantic-based API response model objects ([#1927](https://github.com/lablup/backend.ai/issues/1927))
* Fix the potential missing resource slots when checking the remaining resources lots in the job scheduler ([#1928](https://github.com/lablup/backend.ai/issues/1928))
* Fix inability to download beyond 500 MB via SFTP by preventing dropbear from decreasing the trasnfer window size indefinitely, which happens with non-retrying psftp-based SFTP client implementations ([#1930](https://github.com/lablup/backend.ai/issues/1930))
* Fix CLI `agent info` related issues by replacing `HardwareMetadata` to `dict` when class check and adding parameter to default metric value formatter. ([#1934](https://github.com/lablup/backend.ai/issues/1934))
* Change `endpoints.model` and `endpoint_tokens.endpoint` to nullable and set `ondelete="SET NULL"`. ([#1935](https://github.com/lablup/backend.ai/issues/1935))
* Use `buildDate` instead of `build` to retrieve web static version to follow lablup/backend.ai-webui#2072 ([#1950](https://github.com/lablup/backend.ai/issues/1950))
* Fix graylog log backend not working when `localname` config is set ([#1951](https://github.com/lablup/backend.ai/issues/1951))
* Fix `endpoint.routings` GQL field showing routing ID instead of status enum ([#1952](https://github.com/lablup/backend.ai/issues/1952))

### Documentation Updates
* Update Backend.AI Installation & error guide for Pants version 2.18 and later ([#1904](https://github.com/lablup/backend.ai/issues/1904))

### External Dependency Updates
* Replace `passlib[bcrypt]` to `bcrypt` which is better maintained ([#1932](https://github.com/lablup/backend.ai/issues/1932))
* Upgrade pyzmq and callosum version to improve malformed packet handling in manager-to-agent RPC channels ([#1939](https://github.com/lablup/backend.ai/issues/1939))


## 24.03.0a2 (2024-02-14)

### Breaking Changes
* Drop the support for nvidia-docker v1 from the open source CUDA plugin ([#1755](https://github.com/lablup/backend.ai/issues/1755))

### Features
* Add a new log handler corresponding to graylog ([#1138](https://github.com/lablup/backend.ai/issues/1138))
* Pass `manager.api.RootContext` to plugins for easy access to any Manager's context. ([#1699](https://github.com/lablup/backend.ai/issues/1699))
* Implement async compatible graphql relay node object and implement group/user graphql relay nodes. ([#1719](https://github.com/lablup/backend.ai/issues/1719))
* Use `ui.menu_blocklist` to hide pipeline menu button and delete `pipeline.hide-side-menu-button`. ([#1727](https://github.com/lablup/backend.ai/issues/1727))
* Use `ui.menu_blocklist` to hide and `ui.menu_inactivelist` to disable menu items. ([#1733](https://github.com/lablup/backend.ai/issues/1733))
* Add a `edu_appname_prefix` config on webserver to easily parse image name from app name. ([#1735](https://github.com/lablup/backend.ai/issues/1735))
* GraphQL API log Graphql errors. ([#1737](https://github.com/lablup/backend.ai/issues/1737))
* Implement model data card query support with metadata parser ([#1749](https://github.com/lablup/backend.ai/issues/1749))
* In order to be able to use not only alt_name but also field_ref when using the --format option of session list, add values to FieldSet. ([#1756](https://github.com/lablup/backend.ai/issues/1756))
* Implement the concept of the "main" keypair to make it clear which keypair to use by default and which one holds the user-level resource limits ([#1761](https://github.com/lablup/backend.ai/issues/1761))
* Add the "update" mode for fixtures (specified as the `__mode` key in fixture JSON files) to update existing tables by matching primary keys and setting other columns as bulk-update values, allowing seamless installation with the new `users.main_access_key` column with split insert and update fixtures on the `users` table ([#1785](https://github.com/lablup/backend.ai/issues/1785))
* Implement the DDN storage backend with quota scope support ([#1788](https://github.com/lablup/backend.ai/issues/1788))
* Add `vfolder_mounts` field to session field of client's output. ([#1811](https://github.com/lablup/backend.ai/issues/1811))
* Set timeout for Postgres Advisory lock. ([#1826](https://github.com/lablup/backend.ai/issues/1826))
* Pass the root context to the manager plugins so that they can access database connection pools and other globals ([#1829](https://github.com/lablup/backend.ai/issues/1829))
* Introduce `endpoint.created_user_email` and `endpoint.session_owner_email` GQL field ([#1831](https://github.com/lablup/backend.ai/issues/1831))
* Change default to remove all volumes when execute delete-dev.sh and add "--skip-db" option to skip to remove volumes ([#1852](https://github.com/lablup/backend.ai/issues/1852))
* Refactor the InvalidImageTag exception to include the full container image name for ease of debugging and error handling. ([#1872](https://github.com/lablup/backend.ai/issues/1872))
* Add `pool-recycle` config to drop and replace timed-out connections. ([#1877](https://github.com/lablup/backend.ai/issues/1877))

### Fixes
* Check whether a dependent session has not only succeeded but even terminated. ([#1718](https://github.com/lablup/backend.ai/issues/1718))
* Minimize latency between session insertion and dependency insertion. ([#1720](https://github.com/lablup/backend.ai/issues/1720))
* Restrict destroy of terminated sessions. ([#1721](https://github.com/lablup/backend.ai/issues/1721))
* Improve the installer to use a new default wsproxy port for better compatibility with WSL ([#1722](https://github.com/lablup/backend.ai/issues/1722))
* Fix the installer to use the refactored `common.docker.get_docker_connector()` for system docker detection which now also detects the active docker context if configured ([#1724](https://github.com/lablup/backend.ai/issues/1724))
* Make root partition filesystem type detection compatible with macOS using psutil ([#1728](https://github.com/lablup/backend.ai/issues/1728))
* Fix additional installer issues found in a relatively fresher macOS instance ([#1731](https://github.com/lablup/backend.ai/issues/1731))
* Fix an installer regression in #1724 to inappropriately cache an aiohttp connector instance used to access the local Docker API ([#1732](https://github.com/lablup/backend.ai/issues/1732))
* Change the Redis port number in the webserver conf for `install_dev.sh` installation. ([#1736](https://github.com/lablup/backend.ai/issues/1736))
* Do null-check `rate_limit` value when validate user's rate limit. ([#1738](https://github.com/lablup/backend.ai/issues/1738))
* Fix some trafaret type checkers of redis config from `Float()` to `ToFloat()`. ([#1741](https://github.com/lablup/backend.ai/issues/1741))
* Update the open source version of the CUDA plugin to work with latest NVIDIA container runtimes ([#1755](https://github.com/lablup/backend.ai/issues/1755))
* Change type name of AsyncNode to Node since React's Relay compiler use it to determine relay node. ([#1757](https://github.com/lablup/backend.ai/issues/1757))
* Initialize the `_health_check_task` attribute of the kernel runner explicitly to `None` for safe access. ([#1764](https://github.com/lablup/backend.ai/issues/1764))
* Remove the `containers` field, which is awkward in table format `session list` output, from the `session list --format` item. ([#1766](https://github.com/lablup/backend.ai/issues/1766))
* Improve the E2E CLI-based integration tests to work better with multi-user scenarios and updated `undefined` handling of boolean options ([#1778](https://github.com/lablup/backend.ai/issues/1778))
* Add the missing /folder/recover endpoint.
  Delete the duplicate status field of vfolder. ([#1781](https://github.com/lablup/backend.ai/issues/1781))
* Fix `modify_user` mutation not working ([#1787](https://github.com/lablup/backend.ai/issues/1787))
* Add a missing `ComputeSession.start_service()` functional API in the client SDK with documentation updates ([#1789](https://github.com/lablup/backend.ai/issues/1789))
* Embed webapp response middleware to parse typed response to `web.Response`. ([#1804](https://github.com/lablup/backend.ai/issues/1804))
* Update the default PATH where the `pants` executable is installed in `install-dev.sh` ([#1806](https://github.com/lablup/backend.ai/issues/1806))
* Fix an issue in the `ModifyContainerRegistry` mutation where the `url` was not updating due to a key mismatch. ([#1810](https://github.com/lablup/backend.ai/issues/1810))
* Add `id` column and restore incorrectly dropped unique constraints to DB association tables. ([#1818](https://github.com/lablup/backend.ai/issues/1818))
* Exclude unallocated resources from kernel idle utilization checks. ([#1820](https://github.com/lablup/backend.ai/issues/1820))
* Fix model service health checker reporting invalid healthy status ([#1833](https://github.com/lablup/backend.ai/issues/1833))
* Fix model service endpoint not updated despite session spawned without error ([#1835](https://github.com/lablup/backend.ai/issues/1835))
* Fix `vfolder_list` GQL query not returning `user_email` and `groups_name` field ([#1837](https://github.com/lablup/backend.ai/issues/1837))
* Fix mistakes on SQL queries in the manager's vfolder share API handler when checking target user's status and inconsistent where clauses in the vfolder ownership change API ([#1850](https://github.com/lablup/backend.ai/issues/1850))
* Fix image rescan not working when scanning Harbor v1 registry ([#1854](https://github.com/lablup/backend.ai/issues/1854))
* Fix double-count issue caused by keypairs belonging to multiple projects ([#1869](https://github.com/lablup/backend.ai/issues/1869))
* Improve the resource slot validation logic during session creation and related error messages to display explicit slot names and values with an extra guide on the "shmem" mistake ([#1871](https://github.com/lablup/backend.ai/issues/1871))
* Enqueue session with `use_host_network` field along the scaling_group to which the session belongs. ([#1873](https://github.com/lablup/backend.ai/issues/1873))
* Fix session not created with CentOS 7 based images ([#1878](https://github.com/lablup/backend.ai/issues/1878))
* Bring `watcher.py` back to Backend.AI Agent wheel ([#1880](https://github.com/lablup/backend.ai/issues/1880))
* Fix inconsistent event names reported when making event source channels for already-completed bgtasks (background tasks), which has caused a stale progress bar UI lingering for bgtask operations that finished too quickly ([#1886](https://github.com/lablup/backend.ai/issues/1886))

### Documentation Updates
* Refine and elaborate the Concepts section to reflect all the new features and concepts added in last 3 years ([#1468](https://github.com/lablup/backend.ai/issues/1468))
* Update Backend.AI production installation guide doc ([#1796](https://github.com/lablup/backend.ai/issues/1796))

### Miscellaneous
* Update the Python development tool versions and restyle the codebase with updated Ruff (0.1.7), replacing Black with Ruff ([#1771](https://github.com/lablup/backend.ai/issues/1771))
* Replace all usage of `log.warn()` to  `log.warning()` since [it is now deprecated](https://github.com/python/cpython/blob/bf9cccb2b54ad2c641ea78435a8618a6d251491e/Lib/logging/__init__.py#L1252-L1253) ([#1792](https://github.com/lablup/backend.ai/issues/1792))
* Update aiohttp to 3.9.1 and workaround mypy `TCPConnector` ssl keyword argument type by add custom type `SSLContextType` ([#1855](https://github.com/lablup/backend.ai/issues/1855))
* Upgrade pantsbuild to 2.19.0 release ([#1882](https://github.com/lablup/backend.ai/issues/1882))


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
