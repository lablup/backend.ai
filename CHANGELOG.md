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

## 25.5.2 (2025-03-31)

### Features
* Split `hanging_session_scanner_ctx` into separate stale session and kernel sweepers to more robustly handle orphaned kernels, caused by session status update mismatches ([#3992](https://github.com/lablup/backend.ai/issues/3992))
* Fix typo in keypair resource policy affecting `max_concurrent_sftp_sessions` ([#4050](https://github.com/lablup/backend.ai/issues/4050))
* Add raise exception in action processor ([#4056](https://github.com/lablup/backend.ai/issues/4056))

### Fixes
* Fix image rescanning wrong exception handling logic. ([#4057](https://github.com/lablup/backend.ai/issues/4057))
* Fix docker network not created when bootstraping multi-container session ([#4062](https://github.com/lablup/backend.ai/issues/4062))


## 25.5.1 (2025-03-27)

### Fixes
* Fix exceeding amount of sessions removed when scaling down model service ([#4037](https://github.com/lablup/backend.ai/issues/4037))
* Add missing migration revision history file ([#4039](https://github.com/lablup/backend.ai/issues/4039))
* Missing `watcher` arg in storage volume init methods ([#4041](https://github.com/lablup/backend.ai/issues/4041))
* Do not check storage host permission in VFolder RBAC function ([#4045](https://github.com/lablup/backend.ai/issues/4045))


## 25.5.0 (2025-03-25)

### Features
* Add GQL schema to query total resource slots of compute sessions in scopes or specified conditions. ([#2849](https://github.com/lablup/backend.ai/issues/2849))
* Add `AuditLog` table. ([#3712](https://github.com/lablup/backend.ai/issues/3712))
* Improve performance of vfolder `list_host()` API handler through task parallel execution. ([#3935](https://github.com/lablup/backend.ai/issues/3935))
* Add accelerator quantum size field to GQL scaling group ([#3940](https://github.com/lablup/backend.ai/issues/3940))
* Add container labels to simplify metric queries ([#3980](https://github.com/lablup/backend.ai/issues/3980))
* Separate internal api port ([#3989](https://github.com/lablup/backend.ai/issues/3989))
* Make action processor work with async functions ([#3999](https://github.com/lablup/backend.ai/issues/3999))
* Enhance session status transition management ([#4029](https://github.com/lablup/backend.ai/issues/4029))

### Fixes
* Properly handle zero-value unknown resource limits when creating session. ([#3925](https://github.com/lablup/backend.ai/issues/3925))
* Fix `PurgeImageById` mutation not working when `image_aliass` are present. ([#3972](https://github.com/lablup/backend.ai/issues/3972))
* Fix wrong error message logging when `model_path` does not exist. ([#3990](https://github.com/lablup/backend.ai/issues/3990))
* Allow superadmins to query all GQL agent nodes ([#3996](https://github.com/lablup/backend.ai/issues/3996))
* Fix wrong JSON serialization for response of list presets API handler ([#4006](https://github.com/lablup/backend.ai/issues/4006))
* Fix a potential race condition error in the kernel runner's OOM logger ([#4008](https://github.com/lablup/backend.ai/issues/4008))
* Fix initialization of Storage proxy event dispatcher ([#4010](https://github.com/lablup/backend.ai/issues/4010))
* Update common structure. (Remove `request_id` from `BaseAction`, add `processors_ctx`). ([#4022](https://github.com/lablup/backend.ai/issues/4022))
* Fix wrong parse of auto-mount vfolders inputs ([#4025](https://github.com/lablup/backend.ai/issues/4025))
* Fix `modify_compute_session` GQL mutation error caused by missing kernel loading option. ([#4032](https://github.com/lablup/backend.ai/issues/4032))


## 25.4.0 (2025-03-12)

### Features
* Implement GQL API for scanning GPU allocation map ([#2273](https://github.com/lablup/backend.ai/issues/2273))
* Add image_node and vfolder_node fields to ComputeSession schema ([#2987](https://github.com/lablup/backend.ai/issues/2987))
* Cache `gpu_alloc_map` in Redis, and Add `RescanGPUAllocMaps` mutation for update the `gpu_alloc_map`s. ([#3293](https://github.com/lablup/backend.ai/issues/3293))
* Collect metrics for the RPC server ([#3555](https://github.com/lablup/backend.ai/issues/3555))
* Add `status` Column to the `Image` table, and `ImageRow` unique constraint. ([#3619](https://github.com/lablup/backend.ai/issues/3619))
* Add `status` to `Image`, `ImageNode` GQL Fields. ([#3620](https://github.com/lablup/backend.ai/issues/3620))
* Update `ForgetImage`, `ForgetImageById`, `ClearImages` to perform soft delete and add `PurgeImageById` API for hard delete. ([#3628](https://github.com/lablup/backend.ai/issues/3628))
* Implement noop storage backend ([#3629](https://github.com/lablup/backend.ai/issues/3629))
* Assign the noop storage host to unmanaged vfolders ([#3630](https://github.com/lablup/backend.ai/issues/3630))
* Update vfolder CLI cmd to support unmanaged vfolders ([#3631](https://github.com/lablup/backend.ai/issues/3631))
* Implement `Image` status filtering logics. (e.g. adding an optional argument to the `Image`, `ImageNode` GQL resolvers to enable querying deleted images as well.) ([#3647](https://github.com/lablup/backend.ai/issues/3647))
* Add `enforce_spreading_endpoint_replica` scheduling option to the `ConcentratedAgentSelector`, which prioritizes availability over available resource slots when selecting an agent for inference sessions. ([#3693](https://github.com/lablup/backend.ai/issues/3693))
* Implement `PurgeImages` API for securing storage space on a specific agent. ([#3704](https://github.com/lablup/backend.ai/issues/3704))
* Add sum of resource slots field to scaling group schema ([#3707](https://github.com/lablup/backend.ai/issues/3707))
* Add `scaling_group_name` column to `resource_presets` table. ([#3718](https://github.com/lablup/backend.ai/issues/3718))
* Update resource preset APIs to support mapping a resource group ([#3719](https://github.com/lablup/backend.ai/issues/3719))
* Split redis config for each connection pool ([#3725](https://github.com/lablup/backend.ai/issues/3725))
* Register v2 volume handler to router in storage-proxy ([#3785](https://github.com/lablup/backend.ai/issues/3785))
* Support `application/vnd.oci.image.manifest.v1+json` type images. ([#3814](https://github.com/lablup/backend.ai/issues/3814))
* Add `enable_interactive_login_account_switch` webserver option to control the visibility of the "Sign in with a different account" button on the interactive login page ([#3835](https://github.com/lablup/backend.ai/issues/3835))
* Add centralized action processor design ([#3859](https://github.com/lablup/backend.ai/issues/3859))
* Export utilization metrics to Prometheus ([#3878](https://github.com/lablup/backend.ai/issues/3878))
* Add kernel bootstrap timeout config ([#3880](https://github.com/lablup/backend.ai/issues/3880))
* Add GQL exception and metric middleware ([#3891](https://github.com/lablup/backend.ai/issues/3891))
* Allow delegation of service ownership when purge user ([#3898](https://github.com/lablup/backend.ai/issues/3898))
* Add filter/order argument to GQL `resource_presets` query ([#3916](https://github.com/lablup/backend.ai/issues/3916))

### Fixes
* Fix failure of the whole image rescanning task when there is a misconfigured container registry. ([#3652](https://github.com/lablup/backend.ai/issues/3652))
* Insert default `domain_name` value to vfolders ([#3767](https://github.com/lablup/backend.ai/issues/3767))
* Let Auth API handler check all keypairs owned by user ([#3780](https://github.com/lablup/backend.ai/issues/3780))
* Fix `description` field in user update CLI command, ensuring it is properly omitted when not provided ([#3831](https://github.com/lablup/backend.ai/issues/3831))
* Add missing vfolder mount permission mapping in new RBAC implementation ([#3851](https://github.com/lablup/backend.ai/issues/3851))
* Aggregate multi-kernel session utilization in idle checker ([#3861](https://github.com/lablup/backend.ai/issues/3861))
* Fix rescan only the latest tag in `HarborRegistryV2`. ([#3871](https://github.com/lablup/backend.ai/issues/3871))
* Retry zmq socket connections from kernel ([#3880](https://github.com/lablup/backend.ai/issues/3880))
* Fix intermittent image rescan DB serialization error due to parallel DB access of `rescan_single_registry()` calls. ([#3883](https://github.com/lablup/backend.ai/issues/3883))
* GQL `vfolder_node` query does not resolve `permissions` field ([#3900](https://github.com/lablup/backend.ai/issues/3900))
* Fix GQL Agent `live_stat` resolver to properly parse UUID keys in JSON data as strings ([#3928](https://github.com/lablup/backend.ai/issues/3928))


## 25.3.3 (2025-02-27)

### Features
* Let endpoints with `PROVISIONING` routes deleted without manual session removal ([#3842](https://github.com/lablup/backend.ai/issues/3842))

### Fixes
* Fix `CreateNetwork` GQL mutation not working ([#3843](https://github.com/lablup/backend.ai/issues/3843))
* Fix `EndpointAutoScalingRuleNode` GQL query not working ([#3845](https://github.com/lablup/backend.ai/issues/3845))


## 25.3.2 (2025-02-26)

### Fixes
* Add `service_ports` field resolver to GQL ComputeSessionNode type ([#3782](https://github.com/lablup/backend.ai/issues/3782))
* Fix the GQL VirtualFolderNode resolver to accept a filter argument ([#3799](https://github.com/lablup/backend.ai/issues/3799))
* Fix wrong Python interpreter embedded in the installer scie builds ([#3810](https://github.com/lablup/backend.ai/issues/3810))
* Fix a DB migration script that fails when the system has a default domain with a name other than 'default' ([#3816](https://github.com/lablup/backend.ai/issues/3816))
* Use correct lock ID for schedulers and event producers ([#3817](https://github.com/lablup/backend.ai/issues/3817))
* Broken image rescanning on `HarborRegistry_v1` due to type error of credential value. ([#3821](https://github.com/lablup/backend.ai/issues/3821))
* Ensure that the scie build of install.config also includes the files in the folder and the yaml file. ([#3824](https://github.com/lablup/backend.ai/issues/3824))
* Fix wrong alembic migration scripts ([#3829](https://github.com/lablup/backend.ai/issues/3829))


## 25.3.1 (2025-02-21)

### Features
* Add New API Logging Aligned with Pydantic ([#3731](https://github.com/lablup/backend.ai/issues/3731))
* Configurable global lock lifetime ([#3774](https://github.com/lablup/backend.ai/issues/3774))
* Let metric observers catch base exceptions in event handlers ([#3779](https://github.com/lablup/backend.ai/issues/3779))

### Fixes
* Fix missing argument in Redis event dispatcher initializer ([#3773](https://github.com/lablup/backend.ai/issues/3773))
* Fix wrong Python interpreter versions included in the scie builds ([#3793](https://github.com/lablup/backend.ai/issues/3793))


## 25.3.0 (2025-02-19)

### Features
* Add project scope implementation to Image RBAC. ([#3035](https://github.com/lablup/backend.ai/issues/3035))
* Implement `ImageNode` GQL resolver based on RBAC. ([#3036](https://github.com/lablup/backend.ai/issues/3036))
* Implement `AssociationContainerRegistriesGroups` as m2m table of `container_registries`, and `groups`. ([#3065](https://github.com/lablup/backend.ai/issues/3065))
* Implement CRUD API for managing Harbor per-project Quota. ([#3090](https://github.com/lablup/backend.ai/issues/3090))
* Implement Image Rescanning using Harbor Webhook API. ([#3116](https://github.com/lablup/backend.ai/issues/3116))
* Create KVS Interface ([#3645](https://github.com/lablup/backend.ai/issues/3645))
* Add configurable setup for kernel initialization polling ([#3657](https://github.com/lablup/backend.ai/issues/3657))
* Add a `show_kernel_list` config to webserver to show/hide kernel list in the session detail panel.

  Add configs not specified in sample.toml ([#3671](https://github.com/lablup/backend.ai/issues/3671))
* Make security policy configurable ([#3680](https://github.com/lablup/backend.ai/issues/3680))
* Make CSP configurable ([#3682](https://github.com/lablup/backend.ai/issues/3682))
* Sort vfolder list fields in compute session GQL objects ([#3751](https://github.com/lablup/backend.ai/issues/3751))

### Improvements
* Add the skeleton interface of vfolder CRUD handlers in storage-proxy ([#3516](https://github.com/lablup/backend.ai/issues/3516))
* Apply pydantic handling decorator to VFolder APIs in storage-proxy ([#3565](https://github.com/lablup/backend.ai/issues/3565))
* Move abc.py and storage system modules to volumes package ([#3567](https://github.com/lablup/backend.ai/issues/3567))
* Extract list_volumes and get_volume into pool.py ([#3569](https://github.com/lablup/backend.ai/issues/3569))
* Add Service Layer to Avoid Direct Volume and Vfolder Operations in Storage-Proxy Handler ([#3588](https://github.com/lablup/backend.ai/issues/3588))
* Change Absolute Imports to Relative Imports in Storage-Proxy ([#3685](https://github.com/lablup/backend.ai/issues/3685))

### Fixes
* Revamp `ContainerRegistryNode` API. ([#3424](https://github.com/lablup/backend.ai/issues/3424))
* Change port numbers using ephemeral ports ([#3614](https://github.com/lablup/backend.ai/issues/3614))
* Handle cancel and timeout when creating kernels ([#3648](https://github.com/lablup/backend.ai/issues/3648))
* Correct the number of concurrent SFTP sessions queried from DB ([#3654](https://github.com/lablup/backend.ai/issues/3654))
* Increase Backend.AI Kernel's app startup timeout ([#3679](https://github.com/lablup/backend.ai/issues/3679))
* Fix ContainerRegistry per-project API misc bugs. ([#3701](https://github.com/lablup/backend.ai/issues/3701))
* Fix model service not removed when auto scaling rules are set ([#3711](https://github.com/lablup/backend.ai/issues/3711))
* Validate duplicate session names during compute session modification ([#3715](https://github.com/lablup/backend.ai/issues/3715))
* Revert tmux version upgrade from 3.4 to 3.5a due to compatibility issues on aarch64 architecture ([#3740](https://github.com/lablup/backend.ai/issues/3740))
* Fix compute session rename API handler to query DB correctly ([#3746](https://github.com/lablup/backend.ai/issues/3746))
* Suppress `SELECT statement has a cartesian product between FROM element(s) "endpoints" and FROM element "endpoint_auto_scaling_rules"` log ([#3747](https://github.com/lablup/backend.ai/issues/3747))


## 25.2.0 (2025-02-07)

### Features
* Update tmux version from 3.4 to 3.5a ([#3000](https://github.com/lablup/backend.ai/issues/3000))
* Enable per-user UID/GID set for containers via user creation and update GraphQL APIs ([#3352](https://github.com/lablup/backend.ai/issues/3352))
* Update SDK and CLI to support per-user UID/GID configuration ([#3361](https://github.com/lablup/backend.ai/issues/3361))
* Add timeout configuration for Docker image push ([#3412](https://github.com/lablup/backend.ai/issues/3412))
* Add configurable directory permission for vfolders to support mount vfolders on customized UID/GID containers ([#3510](https://github.com/lablup/backend.ai/issues/3510))
* Add new Pydantic handling api decorator for Request/Response validation ([#3511](https://github.com/lablup/backend.ai/issues/3511))
* Add force delete API for VFolder that bypasses the trash bin ([#3546](https://github.com/lablup/backend.ai/issues/3546))
* Add storage-watcher API to delete VFolders with elevated permissions ([#3548](https://github.com/lablup/backend.ai/issues/3548))

### Improvements
* Add skeleton vFolder handler Interface of manager ([#3493](https://github.com/lablup/backend.ai/issues/3493))

### Fixes
* Add reject middleware for web security ([#2937](https://github.com/lablup/backend.ai/issues/2937))
* Optimize the route selection in App Proxy using `random.choices()` based on the native C implementation in CPython ([#3199](https://github.com/lablup/backend.ai/issues/3199))
* Fix GQL `vfolder_mounts` field resolver of `compute_session` type ([#3461](https://github.com/lablup/backend.ai/issues/3461))
* Fix empty tag image scan error in docker registry. ([#3513](https://github.com/lablup/backend.ai/issues/3513))
* Fixed "permission denied" error by creating the `grafana-data` directory with 757 permissions ([#3570](https://github.com/lablup/backend.ai/issues/3570))
* Fix Broken CSS by allowing `unsafe-inline` content security policy. ([#3572](https://github.com/lablup/backend.ai/issues/3572))
* Updated route pattern to allow any path ending with "login/" for POST requests to `/pipeline/{path:.*login/$}` ([#3574](https://github.com/lablup/backend.ai/issues/3574))
* Fix vfolder delete SDK function to call 'delete by id' API rather than 'delete by name' API ([#3581](https://github.com/lablup/backend.ai/issues/3581))
* Check intrinsic time files exist before mount ([#3583](https://github.com/lablup/backend.ai/issues/3583))
* Fixed to ensure unique values in the mount list of the compute session ([#3593](https://github.com/lablup/backend.ai/issues/3593))
* The installer changes from downloading the checksum files for each package separately to receiving a consolidated checksum file and using them separately. ([#3597](https://github.com/lablup/backend.ai/issues/3597))
* Remove foreign key constraint from `EndpointRow.image` column. ([#3599](https://github.com/lablup/backend.ai/issues/3599))


## 25.1.1 (2025-01-20)
No significant changes.


## 25.1.0 (2025-01-20)

### Features
* Implement fine-grained seccomp profile managed by Backend.AI Agent. ([#3019](https://github.com/lablup/backend.ai/issues/3019))
* Enable image rescanning by project. ([#3237](https://github.com/lablup/backend.ai/issues/3237))
* Support auto-scaling of model services by observing proxy and app-specific metrics as configured by autoscaling rules bound to each endpoint ([#3277](https://github.com/lablup/backend.ai/issues/3277))
* Deprecate the JWT-based `X-BackendAI-SSO` header to reduce complexity in authentication process for the pipeline service ([#3353](https://github.com/lablup/backend.ai/issues/3353))
* Add Grafana and Prometheus to Docker Compose ([#3458](https://github.com/lablup/backend.ai/issues/3458))
* Integrate Pyroscope with Backend.AI ([#3459](https://github.com/lablup/backend.ai/issues/3459))
* Update SDK to retrieve and use IDs for VFolder API operations instead of names ([#3471](https://github.com/lablup/backend.ai/issues/3471))

### Fixes
* Refactor container registries' projects traversal logic of the image rescanning. ([#2979](https://github.com/lablup/backend.ai/issues/2979))
* Fix regression of outdated `vfolder` GQL resolver. ([#3047](https://github.com/lablup/backend.ai/issues/3047))
* Fix image without metadata label not working ([#3341](https://github.com/lablup/backend.ai/issues/3341))
* Enforce VFolder name length restriction through the API schema, not by the DB column constraint ([#3363](https://github.com/lablup/backend.ai/issues/3363))
* Fix password based SSH login not working on sessions based on certain images ([#3387](https://github.com/lablup/backend.ai/issues/3387))
* Fix purge API to allow deletion of owner-deleted VFolders by directly retrieving VFolders using the folder ID ([#3388](https://github.com/lablup/backend.ai/issues/3388))
* Fix certain customized images not being pushed to registry properly ([#3391](https://github.com/lablup/backend.ai/issues/3391))
* Fix formatting errors when logging exceptions raised from the current local process that did not pass our custom serialization step ([#3410](https://github.com/lablup/backend.ai/issues/3410))
* Fix scanning and loading container images with no labels at all (`null` in the image manifests) ([#3411](https://github.com/lablup/backend.ai/issues/3411))
* Fix missing CPU architecture name lookup in `LocalRegistry` to directly scan and load container images from the local Docker daemon in dev setups ([#3420](https://github.com/lablup/backend.ai/issues/3420))
* Utilization idle checker computes kernel resource usages correctly ([#3442](https://github.com/lablup/backend.ai/issues/3442))
* Filter vfolders by status before initiating a vfolder deletion task ([#3446](https://github.com/lablup/backend.ai/issues/3446))
* Fix a mis-implementation that has prevented using UUIDs to indicate an exact vfolder when invoking the vfolder REST API ([#3451](https://github.com/lablup/backend.ai/issues/3451))
* Fix the required state output logic in the openopi reference documentation correctly ([#3460](https://github.com/lablup/backend.ai/issues/3460))
* Raise exception if multiple VFolders exist in decorator ([#3465](https://github.com/lablup/backend.ai/issues/3465))

### Documentation Updates
* Deprecate non relay container registry GQL explicitly. ([#3231](https://github.com/lablup/backend.ai/issues/3231))

### Miscellaneous
* Upgrade pantsbuild from 2.21 to 2.23, replacing the scie plugin with the intrinsic pex's scie build support ([#3377](https://github.com/lablup/backend.ai/issues/3377))


## 24.12.1 (2025-01-04)

### Fixes
* Fix broken session CLI commands due to invalid initialization of `ComputeSession`. ([#3222](https://github.com/lablup/backend.ai/issues/3222))
* Fix a regression that modifying a model service endpoint's replica count always sets it to 1 regardless of the user input ([#3337](https://github.com/lablup/backend.ai/issues/3337))

### Miscellaneous
* Fix the commit message format when assigning the PR number to an anonymous news fragment ([#3309](https://github.com/lablup/backend.ai/issues/3309))


## 24.12.0 (2025-12-30)

### Breaking Changes
* Add `PREPARED` status for compute sessions and kernels to indicate completion of pre-creation tasks such as image pull ([#2647](https://github.com/lablup/backend.ai/issues/2647))
* Add new `CREATING` session status to represent container creation phase, and redefine `PREPARING` status to specifically indicate pre-container preparation phases ([#3114](https://github.com/lablup/backend.ai/issues/3114))

### Features
* Migrate container registry config storage from `Etcd` to `PostgreSQL` ([#1917](https://github.com/lablup/backend.ai/issues/1917))
* Add background task that reports manager DB status. ([#2566](https://github.com/lablup/backend.ai/issues/2566))
* Add manager DB stat API compatible with Prometheus. ([#2567](https://github.com/lablup/backend.ai/issues/2567))
* Allow regular users to assign agent manually if `hide-agent` configuration is disabled ([#2614](https://github.com/lablup/backend.ai/issues/2614))
* Implement ID-based client workflow to ContainerRegistry API. ([#2615](https://github.com/lablup/backend.ai/issues/2615))
* Rafactor Base ContainerRegistry's `scan_tag` and implement `MEDIA_TYPE_DOCKER_MANIFEST` type handling. ([#2620](https://github.com/lablup/backend.ai/issues/2620))
* Support GitHub Container Registry. ([#2621](https://github.com/lablup/backend.ai/issues/2621))
* Support GitLab Container Registry. ([#2622](https://github.com/lablup/backend.ai/issues/2622))
* Support AWS ECR Public Container Registry. ([#2623](https://github.com/lablup/backend.ai/issues/2623))
* Support AWS ECR Private Container Registry. ([#2624](https://github.com/lablup/backend.ai/issues/2624))
* Replace rescan command's `--local` flag with local container registry record. ([#2665](https://github.com/lablup/backend.ai/issues/2665))
* Add public API webapp to allow externel services to query insensitive metrics ([#2695](https://github.com/lablup/backend.ai/issues/2695))
* Add `project` column to the images table and refactoring `ImageRef` logic. ([#2707](https://github.com/lablup/backend.ai/issues/2707))
* Check if agent has the required image before creating compute kernels ([#2721](https://github.com/lablup/backend.ai/issues/2721))
* Introduce network feature ([#2726](https://github.com/lablup/backend.ai/issues/2726))
* Support docker image manifest v2 schema1. ([#2815](https://github.com/lablup/backend.ai/issues/2815))
* Support setting health check interval for model service. ([#2825](https://github.com/lablup/backend.ai/issues/2825))
* Add session status checker GQL mutation. ([#2836](https://github.com/lablup/backend.ai/issues/2836))
* Add `filter` and `order` parameters to Group GQL Relay API. ([#2863](https://github.com/lablup/backend.ai/issues/2863))
* Add GQL `agent` type and resolver ([#2873](https://github.com/lablup/backend.ai/issues/2873))
* Add `vast_use_auth_token` config to utilize VASTData API token optionally. ([#2901](https://github.com/lablup/backend.ai/issues/2901))
* Use a valid value for the `id` field in the GQL schema query resolver for `ContainerRegistry`. ([#2908](https://github.com/lablup/backend.ai/issues/2908))
* Add GQL Relay domain query schema and resolver ([#2934](https://github.com/lablup/backend.ai/issues/2934))
* Add `namespace`, `base_image_name`, `tags` and `version` fields to GQL image schema ([#2939](https://github.com/lablup/backend.ai/issues/2939))
* Allow container user to join extra Linux groups. ([#2944](https://github.com/lablup/backend.ai/issues/2944))
* Add filtering and ordering by `open_to_public` field in endpoint queries ([#2954](https://github.com/lablup/backend.ai/issues/2954))
* Hide FastTrack (`pipeline`) menu by default on installation by `install-dev.sh` script. ([#3010](https://github.com/lablup/backend.ai/issues/3010))
* Support batch session timeout. ([#3066](https://github.com/lablup/backend.ai/issues/3066))
* Add an `show_non_installed_images` option to show all images regardless of installation on environment select section in session/service launcher page. ([#3124](https://github.com/lablup/backend.ai/issues/3124))
* Allow destroying sessions in `PULLING` status for all users ([#3128](https://github.com/lablup/backend.ai/issues/3128))
* Show live stats from inference framework when supported ([#3133](https://github.com/lablup/backend.ai/issues/3133))
* Allow specifying a full shell script string in `start_command` of `model-definition.yaml` while preserving shell variable expansions to allow access to environment variables in service definitions ([#3248](https://github.com/lablup/backend.ai/issues/3248))
* Rename `endpoint.desired_session_count` to `endpoint.replicas` ([#3257](https://github.com/lablup/backend.ai/issues/3257))
* Add several commonly used GPU configuration environment variables defined in containers by default: `GPU_TYPE`, `GPU_COUNT`, `GPU_CONFIG`, `GPU_MODEL_NAME` and `TF_GPU_MEMORY_ALLOC` ([#3275](https://github.com/lablup/backend.ai/issues/3275))
* Populate `BACKEND_MODEL_NAME` environment variable automatically on inference session ([#3281](https://github.com/lablup/backend.ai/issues/3281))
* Fix container cleanup process failing with error `AttributeError: 'DockerKernel' object has no attribute 'network_driver'` ([#3286](https://github.com/lablup/backend.ai/issues/3286))

### Improvements
* Convert VFolder deletion from blocking response to event-driven pattern ([#3063](https://github.com/lablup/backend.ai/issues/3063))

### Fixes
* Explicitly wait for readiness of the Docker daemon and the compose stack before pouring database fixtures in `install-dev.sh` for when installing at the provisioning stage of Codespaces and integration tests in CI. ([#2378](https://github.com/lablup/backend.ai/issues/2378))
* Fix silent failure of `DockerAgent.push_image()`, `DockerAgent.pull_image()`. ([#2572](https://github.com/lablup/backend.ai/issues/2572))
* Fix missing notification of cancellation or failure of background tasks when shutting down the server ([#2579](https://github.com/lablup/backend.ai/issues/2579))
* Add missing implementation of wsproxy and manager CLI's log-level customization options ([#2698](https://github.com/lablup/backend.ai/issues/2698))
* Add missing batch execution call after session starts ([#2884](https://github.com/lablup/backend.ai/issues/2884))
* Fix a regression of the unicode-aware slug update that prevented creation of dot-prefixed (automount) vfolders ([#2892](https://github.com/lablup/backend.ai/issues/2892))
* Fix invalid image format log spam in Agent ([#2894](https://github.com/lablup/backend.ai/issues/2894))
* Fix wrong creation of `raw_configs` in `_create_kernels_in_one_agent` ([#2896](https://github.com/lablup/backend.ai/issues/2896))
* Disallow `None` id encoding in `AsyncNode.to_global_id()`. ([#2898](https://github.com/lablup/backend.ai/issues/2898))
* Assign valid value to `id` field in `ContainerRegistryNode` GQL schema query resolver. ([#2899](https://github.com/lablup/backend.ai/issues/2899))
* Update vast quota rather than raise error when quota exists. ([#2900](https://github.com/lablup/backend.ai/issues/2900))
* Calculate correct expiration time of VAST auth token and add `vast_force_login` config to enable login before every REST API call ([#2911](https://github.com/lablup/backend.ai/issues/2911))
* Update Dellemc OneFS storage backend to correctly initialize volume object and wrong http request arguments ([#2918](https://github.com/lablup/backend.ai/issues/2918))
* Fix `modify_endpoint()` mutation to handle empty `JSONString` properly for environment variables ([#2922](https://github.com/lablup/backend.ai/issues/2922))
* Fix `order` GQL query argument parser of `group_nodes` ([#2927](https://github.com/lablup/backend.ai/issues/2927))
* Set the `postgres_readonly` flag to `false` when begin generic sessions ([#2946](https://github.com/lablup/backend.ai/issues/2946))
* Fix wrong container registry migration script. ([#2949](https://github.com/lablup/backend.ai/issues/2949))
* Let GPFS client keep polling when GPFS job is running ([#2961](https://github.com/lablup/backend.ai/issues/2961))
* Handle `IndexError` when parse string to `BinarySize` ([#2962](https://github.com/lablup/backend.ai/issues/2962))
* Handle error when convert `shmem` string value into `BinarySize` ([#2972](https://github.com/lablup/backend.ai/issues/2972))
* Make image, container_registry table's `project` column nullable and improve container registry storage config migration script. ([#2978](https://github.com/lablup/backend.ai/issues/2978))
* Fix a wrong parameter when call 'recalc_agent_resource_occupancy()' ([#2982](https://github.com/lablup/backend.ai/issues/2982))
* Allow the `modify_compute_session` mutation works without `priority` field in input argument and let the mutation validates `name` value ([#2985](https://github.com/lablup/backend.ai/issues/2985))
* Fix wrong password limit in container registry migration script. ([#2986](https://github.com/lablup/backend.ai/issues/2986))
* Fix `architecture` condition not applied when query `images` rows ([#2989](https://github.com/lablup/backend.ai/issues/2989))
* Deprecate `project_id` GQL argument and add nullable `scope_id` GQL argument ([#2991](https://github.com/lablup/backend.ai/issues/2991))
* Strengthen join condition between kernels and images to prevent incorrect matches ([#2993](https://github.com/lablup/backend.ai/issues/2993))
* Enable session commit to different registry, project. ([#2997](https://github.com/lablup/backend.ai/issues/2997))
* Wrong field reference in `ImageNode` resolver ([#3002](https://github.com/lablup/backend.ai/issues/3002))
* Fix obsolete logic of `untag()` of `HarborRegistry_v2`. ([#3004](https://github.com/lablup/backend.ai/issues/3004))
* Fix `Agent.compute_containers` GraphQL field by adding missing resolver ([#3011](https://github.com/lablup/backend.ai/issues/3011))
* Fix `Agent` GQL Regression error. ([#3013](https://github.com/lablup/backend.ai/issues/3013))
* Fix `backend.ai apps` command's faulty argument handling logic. ([#3015](https://github.com/lablup/backend.ai/issues/3015))
* Check Vast data quota with a given name exists before creating quota and change default value of `force_login` config to true ([#3023](https://github.com/lablup/backend.ai/issues/3023))
* Fix model service traffics not distributed equally to every sessions when there are 10 or more replicas ([#3027](https://github.com/lablup/backend.ai/issues/3027))
* Fix the TUI installer to make the install path always visible ([#3029](https://github.com/lablup/backend.ai/issues/3029))
* Prevent redis password from being logged. ([#3031](https://github.com/lablup/backend.ai/issues/3031))
* Fix `get_logs_from_agent()` to raise `InstanceNotFound` exception for kernels not assigned to agents ([#3032](https://github.com/lablup/backend.ai/issues/3032))
* Fix regression of `ComputeContainer` GraphQL queries due to newly introduced relationship fields ([#3042](https://github.com/lablup/backend.ai/issues/3042))
* Fix regression of the `AgentSummary` resolver caused by an incorrect `batch_load_func` assignment. ([#3045](https://github.com/lablup/backend.ai/issues/3045))
* Fix regression of `LegacyComputeSession` GraphQL queries. ([#3046](https://github.com/lablup/backend.ai/issues/3046))
* Include missing legacy logging module in the pex. ([#3054](https://github.com/lablup/backend.ai/issues/3054))
* Change the name of deleted vfolders with a timestamp suffix when sending them to DELETE_ONGOING status to allow reuse of the vfolder name, for cases when actual deletion takes a long time ([#3061](https://github.com/lablup/backend.ai/issues/3061))
* Fix model service not routing traffics based on traffic ratio ([#3075](https://github.com/lablup/backend.ai/issues/3075))
* Fix the broken `ComputeContainer.batch_load_detail` due to the misuse of `selectinload` as follow-up to #3042 ([#3078](https://github.com/lablup/backend.ai/issues/3078))
* Fix session `status_info` not being updated correctly when batch executions fail, ensuring failed batch execution states are properly reflected in the sessions table ([#3085](https://github.com/lablup/backend.ai/issues/3085))
* agent not loading `krunner-extractor` image when Docker instance does not support loading XZ compressed images ([#3101](https://github.com/lablup/backend.ai/issues/3101))
* Fix outdated image string join logic in `ImageRow.image_ref`. ([#3125](https://github.com/lablup/backend.ai/issues/3125))
* Allow admins to delete other users' vfolders by enabling vfolder fetching for precondition checks ([#3137](https://github.com/lablup/backend.ai/issues/3137))
* Fix Libc version not detected on unlabeled images when image has custom entrypoint set ([#3173](https://github.com/lablup/backend.ai/issues/3173))
* Fix service not started when `[logging].rotation-size` config is set ([#3174](https://github.com/lablup/backend.ai/issues/3174))
* Allow purging vfolders by enabling name-based queries of deleted VFolders ([#3176](https://github.com/lablup/backend.ai/issues/3176))
* Fix the issue where the value of occupying slots abnormally multiplies when creating a compute session ([#3186](https://github.com/lablup/backend.ai/issues/3186))
* Add missing `extra` field to `ContainerRegistryNode` GQL query, mutations. ([#3208](https://github.com/lablup/backend.ai/issues/3208))
* Fix purge functionality that deletes VFolder records by allowing admins to query other users' VFolders ([#3223](https://github.com/lablup/backend.ai/issues/3223))
* Fix CLI test failures caused by `yarl.URL._val` type change. ([#3235](https://github.com/lablup/backend.ai/issues/3235))
* Prevent vfolder `request-download` API from accessing host filesystem. ([#3241](https://github.com/lablup/backend.ai/issues/3241))
* Fix `1d42c726d8a3` revision execution failing ([#3254](https://github.com/lablup/backend.ai/issues/3254))
* Ensure the string formatting of BinarySize values containing subtle fractions to be floating point numbers (instead of scientific notations) always ([#3272](https://github.com/lablup/backend.ai/issues/3272))
* Fix invalid API version checks in the session creation API of Manager. ([#3291](https://github.com/lablup/backend.ai/issues/3291))

### Documentation Updates
* Update the package installation documentation to include instructions on adding the manager's RPC key pair. ([#2052](https://github.com/lablup/backend.ai/issues/2052))

### Miscellaneous
* Upgrade the base CPython version from 3.12.6 to 3.12.8 ([#3302](https://github.com/lablup/backend.ai/issues/3302))


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


## 24.03 and earlier

* [Unified changelog for the core components](https://github.com/lablup/backend.ai/blob/24.03/CHANGELOG.md)
