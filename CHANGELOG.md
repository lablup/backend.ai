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

## 22.09.9 (2023-01-25)

Ai.Backend.Manager 22.09.9 (2023-01-25)

### Fixes
* Add comment out on gpfs sample volume when setting up the development environment with ./script/install-dev.sh ([#965](https://github.com/lablup/backend.ai/issues/965))
* Disable the socket-relay container on macOS to avoid UNIX socket bind-mount compatibility issue in for macOS + virtiofs setups ([#986](https://github.com/lablup/backend.ai/issues/986))

### Miscellaneous
* Update the socket-relay container's base distro (Alpine) version to 3.17 to enable support for `AF_VSOCK` in the latest socat 1.7.4 package ([#988](https://github.com/lablup/backend.ai/issues/988))


## 22.09.8 (2023-01-10)

Ai.Backend.Manager 22.09.8 (2023-01-10)

### Features
* Support setting the `use_host_network` option of scaling group in the client-py. ([#941](https://github.com/lablup/backend.ai/issues/941))


## 22.09.7 (2023-01-09)

Ai.Backend.Manager 22.09.7 (2023-01-09)

### Features
* Support IBM Spectrum Scale storage ([#744](https://github.com/lablup/backend.ai/issues/744))
* Add support for Ceph file system in Storage Proxy. ([#760](https://github.com/lablup/backend.ai/issues/760))
* Add `custom-auth` endpoint in Webserver to support custom authentication logic with Manager plugin. ([#936](https://github.com/lablup/backend.ai/issues/936))
* Remove the `Server` HTTP response header from the web server since it could potentially expose more attack surfaces to crackers ([#947](https://github.com/lablup/backend.ai/issues/947))

### Fixes
* Add missing `await` for a jupyter-client API when shutting down the kernel runner, as a follow-up fix to #873 ([#915](https://github.com/lablup/backend.ai/issues/915))
* Improve scriptability of the `session events` CLI command by ensuring stdout flush and providing well-formatted JSON outputs of event data ([#925](https://github.com/lablup/backend.ai/issues/925))
* Continue the server operation with a warning even when the aiomonitor thread could not be started and adjust the default aiomonitor ports out of the ephemeral port range ([#928](https://github.com/lablup/backend.ai/issues/928))
* Fill the request payload with the plain-text request body when the web login handler is called without encryption.  This was a regression after introducing the login payload encryption. ([#929](https://github.com/lablup/backend.ai/issues/929))

### Documentation Updates
* Guide to install Backend.AI with package (wheel). ([#939](https://github.com/lablup/backend.ai/issues/939))


## 22.09.6 (2022-12-09)

Ai.Backend.Manager 22.09.6 (2022-12-09)

### Features
* Add the `local_rank` column in the `kernels` table and the `BACKENDAI_CLUSTER_LOCAL_RANK` environment variable in session containers to simplify execution of distributed computing/ML frameworks with one shell command ([#826](https://github.com/lablup/backend.ai/issues/826))
* Add option to skip verifying SSL certificate of weka endpoint ([#903](https://github.com/lablup/backend.ai/issues/903))

### Fixes
* Always read `.env` from current working directory in the client ([#806](https://github.com/lablup/backend.ai/issues/806))
* Fix request failure that cannot freeze manager using CLI command ([#889](https://github.com/lablup/backend.ai/issues/889))
* Fix invalid cross-reference from `ai.backend.common` to `ai.backend.web` ([#902](https://github.com/lablup/backend.ai/issues/902))
* Fix the invalid default value of the agent's new `affinity-policy` option ([#905](https://github.com/lablup/backend.ai/issues/905))
* Fix occasional random mismatch of cluster hostnames and actual container hostnames in cluster sessions under the host networking mode ([#907](https://github.com/lablup/backend.ai/issues/907))
* Always use the FILL allocation strategy for the main memory to avoid conflicts with NUMA allocator where all the main memory is coerced as a single NUMA node "root" ([#908](https://github.com/lablup/backend.ai/issues/908))
* Rewrite the NUMA-aware device allocation to support 3 or more NUMA nodes properly, mixing interleaved and best-effort filling allocation strategies for non-first subsequent device types depending on the NUMA nodes used for the allocation of first device type ([#909](https://github.com/lablup/backend.ai/issues/909))
* Use more consistently appearing unicode symbols in the CLI's pretty output ([#917](https://github.com/lablup/backend.ai/issues/917))
* Fix spill-over of the DELETING status update to other vfolders with the same name when deleting a vfolder. This did not cause deletion of actual vfolders and their contents whose status is wrongly marked as DELETING, but causes confusion to the users and admins. ([#920](https://github.com/lablup/backend.ai/issues/920))


## 22.09.5 (2022-11-28)

Ai.Backend.Manager 22.09.5 (2022-11-28)

### Features
* Make the listening port of the container metadata server configurable ([#447](https://github.com/lablup/backend.ai/issues/447))
* Add support for NUMA-aware device ordering and affinitization in `AllocMap` classes ([#491](https://github.com/lablup/backend.ai/issues/491))
* Implement atomic vfolder host permission ([#790](https://github.com/lablup/backend.ai/issues/790))
* Add option to run containers under host networking mode when enabled on scaling group option ([#838](https://github.com/lablup/backend.ai/issues/838))
* feat: Group string-literal KernelEvent.reason by KernelLifecycleEventReason class to manage them ([#855](https://github.com/lablup/backend.ai/issues/855))
* Add new `app_download_url` config for Webserver to control the Backend.AI WebUI app download url ([#861](https://github.com/lablup/backend.ai/issues/861))
* Load plugins by reading allowlists from manager local configuration ([#866](https://github.com/lablup/backend.ai/issues/866))
* Now the database connection pool parameters (the default pool size and maximum overflow) is configurable in `manager.toml` ([#871](https://github.com/lablup/backend.ai/issues/871))
* Support client login with authentication header which takes priority over the legacy cookie ([#899](https://github.com/lablup/backend.ai/issues/899))
* Upgrade accelerator plugin entrypoint requirement to v21 ([#900](https://github.com/lablup/backend.ai/issues/900))

### Improvements
* Upgrade the krunner prebuilt runtimes to use Python 3.10 and latest dependency packages ([#873](https://github.com/lablup/backend.ai/issues/873))

### Fixes
* Fix 400 Bad request error triggered by extra decode string with UTF-8 operation in decrypt_payload() as decrypt logic moved to middleware ([#707](https://github.com/lablup/backend.ai/issues/707))
* Prevent session statuses from being rolled backed to PREPARING after successful creation or timeout ([#783](https://github.com/lablup/backend.ai/issues/783))
* Modify `get_time_binned_monthly_stats` logic so that number of sessions and resource usage is calculated appropriately during all session execution times ([#840](https://github.com/lablup/backend.ai/issues/840))
* Modify `ExitCode` to take `enum.IntEnum` as an argument so that `sys.exit()` does not output a message ([#845](https://github.com/lablup/backend.ai/issues/845))
* Fix serialization failures when returning kernel creation results with additional accelerator device information ([#849](https://github.com/lablup/backend.ai/issues/849))
* Fix string parser option to prevent tokenizing WebUI plugin string into characters ([#850](https://github.com/lablup/backend.ai/issues/850))
* Handle kernel creation failure and destroy failed kernel ([#852](https://github.com/lablup/backend.ai/issues/852))
* Fix `backend.ai mgr schema oneshot` command not creating `alembic_version` table alfter populating database chema ([#853](https://github.com/lablup/backend.ai/issues/853))
* Fix `ResourceSlotColumn` to check None type early ([#856](https://github.com/lablup/backend.ai/issues/856))
* Get mutation name from ResolveInfo.field_name in gql mutation middleware ([#882](https://github.com/lablup/backend.ai/issues/882))
* Update wrong vfolder_host_permission value for cli and test codes ([#897](https://github.com/lablup/backend.ai/issues/897))
* Fallback to the legacy logic of getting current allocation if there is no devices in affinity hint which prevented to launch a compute session with CPU and memory only for a single numa node system ([#901](https://github.com/lablup/backend.ai/issues/901))

### Miscellaneous
* Add `--ipc-base-path` option to `install-dev.sh` to ease setting up multiple development environments in a single node ([#841](https://github.com/lablup/backend.ai/issues/841))
* Upgrade Pants from 2.13.1rc2 to 2.14.0 -- Normally it will automatically update itself, but you many need to reset your Pants cache if you encounter any strange behavior ([#857](https://github.com/lablup/backend.ai/issues/857))
* Now `install-dev.sh` and Pants will look for Python versions from `pyenv` only to avoid conflicts/confusion with other Python versions installed together ([#864](https://github.com/lablup/backend.ai/issues/864))


## 22.09.4 (2022-10-26)

### Features
* Improve the agent's CPU core detection to use Docker's cgroup cpusets for better compatibility with other frameworks dedicating CPU cores exclusively ([#804](https://github.com/lablup/backend.ai/issues/804))


## 22.09.3 (2022-10-25)

### Features
* Adopt aiohttp_session implementation as a part of common module ([#752](https://github.com/lablup/backend.ai/issues/752))
* Update aiomonitor-ng to v0.7 and apply cancellation tracking to long-running tasks ([#808](https://github.com/lablup/backend.ai/issues/808))

### Fixes
* Return empty commit status for non-running sessions to prevent constant 400 errors in the frontend. ([#820](https://github.com/lablup/backend.ai/issues/820))
* Fix a typo on response message to describe the status when calling GET session commit API ([#821](https://github.com/lablup/backend.ai/issues/821))

### Miscellaneous
* Bump base Python version from 3.10.7 to 3.10.8 to resolve potential bugs. ([#801](https://github.com/lablup/backend.ai/issues/801))
* Do not create a subshell in executing the `py` and `backend.ai` scripts. ([#819](https://github.com/lablup/backend.ai/issues/819))


## 22.09.2 (2022-10-18)

### Fixes
* Fix missing unpacking of the tar file before downloading a single file from a session container ([#778](https://github.com/lablup/backend.ai/issues/778))
* Update mutation error message for better readability. ([#782](https://github.com/lablup/backend.ai/issues/782))
* Raise error if target kernel is not yet ready to accept RPC call. ([#787](https://github.com/lablup/backend.ai/issues/787))
* Correct agent status compare in resolver. ([#788](https://github.com/lablup/backend.ai/issues/788))
* Resolve error in getting vfolder inode usage by converting the human-readable string of `inode_size` to `inode_count` number. ([#789](https://github.com/lablup/backend.ai/issues/789))
* Fix admin not being able to access some vFolder APIs which referring vFolders that requesting user does not own ([#791](https://github.com/lablup/backend.ai/issues/791))


## 22.09.1 (2022-10-07)

### Features
* Added `shared_vfolder_info` to get shared folder information and `update_shared_vf_permission` and `remove_shared_vf_permission` API to update and delete shared folder permissions. ([#608](https://github.com/lablup/backend.ai/issues/608))
* Add `-a` / `--all` option to `backend.ai ps` like `docker ps -a` to list all sessions regardless of the statuses ([#616](https://github.com/lablup/backend.ai/issues/616))
* Introduce vfolder status to control user access to individual vfolders ([#713](https://github.com/lablup/backend.ai/issues/713))
* Add a new Agent option to (or not to) force terminate abusing kernels to support the use case for admins to watch what the containers actually do before terminating them. ([#764](https://github.com/lablup/backend.ai/issues/764))
* Expose `ComputeSession.id` to query filter to enable GraphQL queries filter items by list of id. ([#772](https://github.com/lablup/backend.ai/issues/772))

### Fixes
* Fix extra vFolder access condition not applied when querying vFolder ([#766](https://github.com/lablup/backend.ai/issues/766))
* Create vfolder status field in DB schema correctly. ([#768](https://github.com/lablup/backend.ai/issues/768))
* Prevent unhandled `read_stream` exception which leads to the stuck of newly created sessions in the `PREPARING` status. ([#771](https://github.com/lablup/backend.ai/issues/771))
* skip resolving fields from dead agent. ([#775](https://github.com/lablup/backend.ai/issues/775))


## 22.09.0 (2022-09-28)

### Breaking Changes
* All installations MUST replace "postgresql://" to "postgresql+asyncpg://" in `alembic.ini` ([#702](https://github.com/lablup/backend.ai/issues/702))

### Features
* Add `shared_user_uuid` paramater to allow superadmins to remove users from shared vfolders. ([#522](https://github.com/lablup/backend.ai/issues/522))
* Allow reading compute plugin blocklists from agent local configuration. ([#624](https://github.com/lablup/backend.ai/issues/624))
* Add `shared_user_uuid` parameter to vfolder's `leave` api to allow superadmins to remove users from shared vfolders. ([#692](https://github.com/lablup/backend.ai/issues/692))
* Implement IP-based client restriction. ([#695](https://github.com/lablup/backend.ai/issues/695))
* Show agent summary information to user only if `manager.hide-agents` config is set to `true`. ([#699](https://github.com/lablup/backend.ai/issues/699))
* Add new `hide_agents` config for Webserver to control the visibility of agent information to normal users. ([#704](https://github.com/lablup/backend.ai/issues/704))
* Agents skip containers owned by other agents in the same host during scanning containers. ([#712](https://github.com/lablup/backend.ai/issues/712))
* Implement retry on vfolder-download when connection error or timeout error occurs. ([#714](https://github.com/lablup/backend.ai/issues/714))
* Add agent configuration option to apply alternative docker network. ([#715](https://github.com/lablup/backend.ai/issues/715))
* Add commit history link between releases in release notes(`CHANGELOG_RELEASE.md`). ([#721](https://github.com/lablup/backend.ai/issues/721))
* Always mount infiniband device if it exists on agent host, without checking if kernel uses multi container or not. ([#731](https://github.com/lablup/backend.ai/issues/731))
* Add webserver option to support session enqueue feature, introduced from lablup/backend.ai-webui#1162 ([#732](https://github.com/lablup/backend.ai/issues/732))
* Introduce abusing container status and agent local_config API ([#737](https://github.com/lablup/backend.ai/issues/737))
* Upgrade aiomonitor-ng to 0.6.0 for improved line-editing in telnet prompts and easier live-debugging with the `console` command via additional `console_locals` variable references ([#743](https://github.com/lablup/backend.ai/issues/743))

### Fixes
* Remove dependency to `psycopg2-binary` completely and make all database operations to run with `asyncpg` ([#702](https://github.com/lablup/backend.ai/issues/702))
* Fix user update in client method and manager's mutation method ([#718](https://github.com/lablup/backend.ai/issues/718))
* Let admins can purge a user account even if there is no related kaypair. ([#725](https://github.com/lablup/backend.ai/issues/725))
* Allow installation of packaged wheels on compatible Python versions (e.g., any of 3.10.x) ([#727](https://github.com/lablup/backend.ai/issues/727))
* Fix wrong type matching in scaling group query method ([#738](https://github.com/lablup/backend.ai/issues/738))

### Miscellaneous
* Refactor session commit functionality and change commit file name format. ([#674](https://github.com/lablup/backend.ai/issues/674))
* Bump base Python version from 3.10.5 to 3.10.7 to reflect Python coroutine bugfix. ([#719](https://github.com/lablup/backend.ai/issues/719))


## 22.09.0b6 (2022-09-02)

### Features
* Update codespace bootstrap script to reflect updated `install-dev.sh` ([#516](https://github.com/lablup/backend.ai/issues/516))
* Allow non-admin users to query agent information by implementing new gql schema. ([#645](https://github.com/lablup/backend.ai/issues/645))

### Fixes
* Fix accelerator specific files created under work directory (`/home/work`) instead of config directory (`/home/config`). ([#701](https://github.com/lablup/backend.ai/issues/701))
* Update `etcetra` (to v0.1.10) to avoid potential accumulation of unreclaimed async tasks


## 22.09.0b5 (2022-08-30)

### Features
* Refactor `decrypt_payload()` as a middleware so that applied to `web_handler()` and `login_handler()` ([#626](https://github.com/lablup/backend.ai/issues/626))
* Preserve the given `reason` value even when a kernel is force-terminated with a fallback to `force-terminated` ([#681](https://github.com/lablup/backend.ai/issues/681))
* Enable the asyncio debug mode when our debug mode is enabled (e.g., `--debug`) and replace `aiomonitor` with `aiomonitor-ng` ([#688](https://github.com/lablup/backend.ai/issues/688))

### Fixes
* Accept both string field names and `FieldSpec` instances in the Client SDK's functional API wrappers ([#613](https://github.com/lablup/backend.ai/issues/613))
* Do not remove lock file when FileLock does not have lock. ([#676](https://github.com/lablup/backend.ai/issues/676))
* Make the Web-UI login work again by fixing missing decrypted payloads as JSON (a regression of #626) ([#689](https://github.com/lablup/backend.ai/issues/689))


## 22.09.0b4 (2022-08-22)

### Features
* Elaborate messaging of `InstanceNotAvailable` errors and log it inside the `status_data` column as the `scheduler.msg` JSON field ([#643](https://github.com/lablup/backend.ai/issues/643))

### Fixes
* Skip non-running sessions for commit status checks by returning null in the `commit_status` GraphQL query field because the agent(s) won't have any information about the non-running kernels ([#667](https://github.com/lablup/backend.ai/issues/667))


## 22.09.0b3 (2022-08-18)
* A follow-up hotfix for [#664](https://github.com/lablup/backend.ai/issues/664)


## 22.09.0b2 (2022-08-18)

### Features
* Reduce the initial startup latency of service daemons and CLI (`./backend.ai`) by more than 50% in the development setups using Pants ([#663](https://github.com/lablup/backend.ai/issues/663))

### Fixes
* Add missing lazy-imported cli modules in the package ([#664](https://github.com/lablup/backend.ai/issues/664))


## 22.09.0b1 (2022-08-18)

### Features
* Add `owner` (replacing the `shared_by` field) and `type` fields ("project" or "user") to the `list_shared_vfolders` API to accurately distinguish the owner and the folder type ([#521](https://github.com/lablup/backend.ai/issues/521))
* Add `keypair_resource.max_session_lifetime` option field to client following the latest schema. ([#543](https://github.com/lablup/backend.ai/issues/543))
* client: Read `.env` files if present to configure the API session using `python-dotenv` ([#566](https://github.com/lablup/backend.ai/issues/566))
* Accept the explicit "s" (seconds) unit suffix as well in `common.validators.TimeDuration` ([#570](https://github.com/lablup/backend.ai/issues/570))
* Add a paginated query for the virtual folder permission list for superadmin. ([#571](https://github.com/lablup/backend.ai/issues/571))
* Add manager REST APIs, agent RPC APIs and backend implementations to commit a running session container as a tar.gz file and check the status of long-running commit tasks (for the docker agent only) ([#601](https://github.com/lablup/backend.ai/issues/601))
* Add `common.logging.LocalLogger` to improve logging outputs in test cases, which does not use the relay handler to send log records to another (parent) process but just the standard Python logging subsystem ([#630](https://github.com/lablup/backend.ai/issues/630))
* Add a new API router (`/func/saml`) and a config `service.single_sign_on_vendors` to integrate SSO login, especially SAML 2.0 in this case. Also, the redirect responses (30X) are now transparently delivered to the downstream without raising `BackendAPIError`. ([#652](https://github.com/lablup/backend.ai/issues/652))
* Add `status_history` to the query field of `get_container_stats_for_period` to know when the status of the session within a given period has changed. ([#653](https://github.com/lablup/backend.ai/issues/653))
* Define interface `generate_mounts` and `get_docker_networks` on compute plugin ([#654](https://github.com/lablup/backend.ai/issues/654))
* webserver: Include the feature flag `service.enable_container_commit` in `/config.toml` which allows users to commit their running session containers and save as images inside the configured path in the corresponding agent host ([#660](https://github.com/lablup/backend.ai/issues/660))
* Use the full terminal width when formatting CLI help texts for better readability ([#662](https://github.com/lablup/backend.ai/issues/662))

### Fixes
* web: Force the keypair-based auth mode regardless to env-vars ([#564](https://github.com/lablup/backend.ai/issues/564))
* Correct misspelled word in ImageNotFound exception message. ([#615](https://github.com/lablup/backend.ai/issues/615))
* Pin `hiredis` version to 1.1.0 (the version auto-inferred from `redis-py` is 2.0) to avoid a potential memory corruption error, such as "free(): invalid pointer" upon termination ([#636](https://github.com/lablup/backend.ai/issues/636))
* Improve null-checks when querying allowed vfolder hosts to prevent internal server errors when there are no allowed vfolder hosts ([#638](https://github.com/lablup/backend.ai/issues/638))
* Fix a spurious insufficient privilege error when running `backend.ai run` command as a normal user due to a mishandling of the default value of `--assign-agent` CLI option ([#639](https://github.com/lablup/backend.ai/issues/639))
* Fix `FileLock` not acquiring lock forever when lock file is created without write permission to manager processes' owner ([#642](https://github.com/lablup/backend.ai/issues/642))
* Change `client.cli` to use `ai.backend.cli.main:main` as its root CommandGroup. ([#650](https://github.com/lablup/backend.ai/issues/650))
* Fix kernel stats not being updated to database ([#661](https://github.com/lablup/backend.ai/issues/661))

### Miscellaneous
* Introduce `ExitCode` enum to give concrete semantics to numeric CLI exit codes ([#559](https://github.com/lablup/backend.ai/issues/559))
* Upgrade Pants to 2.12.0 to 2.13.0rc0 to take advantage of the latest bug fixes and improvements ([#589](https://github.com/lablup/backend.ai/issues/589))
* Revamp and refactor BUILD files to make Pants to handle fine-grained target selection better via per-directory BUILD files and utilize automatic internal-dependency inferences whenever possible, with unification of the source target names to `:src` (previously, `:lib` and `:service`) ([#627](https://github.com/lablup/backend.ai/issues/627))


## 22.06.0b4 (2022-07-28)

### Fixes
* web: Include missing `templates` directory in the package ([#611](https://github.com/lablup/backend.ai/issues/611))


## 22.06.0b3 (2022-07-27)

### Features
* Migrate [accelerator-cuda](https://github.com/lablup/backend.ai-accelerator-cuda) and [accelerator-cuda-mock](https://github.com/lablup/backend.ai-accelerator-cuda-mock) to monorepo setup ([#511](https://github.com/lablup/backend.ai/issues/511))
* Move validator which check scaling group by session type from predicate to enqueue_session. ([#565](https://github.com/lablup/backend.ai/issues/565))
* Support wsproxy v2 when the coordinator's user-accessible URL is different from the manager-accessible URL (usually when the user is separated from the Backend.AI service by NAT) ([#582](https://github.com/lablup/backend.ai/issues/582))
* Add the `static_path` option to `webserver.conf` for site-specific customization and refactor internal configuration handling and request handlers of the webserver ([#599](https://github.com/lablup/backend.ai/issues/599))

### Fixes
* Update deprecated manager APIs, such as `etcd alias` and `etcd rescan-images`. ([#509](https://github.com/lablup/backend.ai/issues/509))
* Use `aioredis.client.Redis.ping()` to ping redis server rather than `aioredis.client.Redis.time()`. ([#512](https://github.com/lablup/backend.ai/issues/512))
* Revert and simplify changes on `sql_json_merge()` with additional test cases to support empty keys. ([#558](https://github.com/lablup/backend.ai/issues/558))
* Fixed a Regex/shell escaping issue when updating var-base-path by changing parsing. ([#567](https://github.com/lablup/backend.ai/issues/567))
* install-dev.sh: Fix "AND" operator when checking `--enable-cuda` &amp; `--enable-cuda-mock` and modify the default-installed `cuda-mock.toml` file ([#578](https://github.com/lablup/backend.ai/issues/578))
* install-dev: Add compatibility checks for `-f` option of the `docker compose` (v2) commands in the user home directory and system-wide directory ([#602](https://github.com/lablup/backend.ai/issues/602))


## 22.06.0b2 (2022-07-18)

### Features
* Add `backend.ai session watch` command to display the event stream of target session. ([#440](https://github.com/lablup/backend.ai/issues/440))
* Add support for Weka.IO storage backend. ([#443](https://github.com/lablup/backend.ai/issues/443))
* Add support for auto-removal of kernels reported for abusing or abnormal activities by separate detectors ([#449](https://github.com/lablup/backend.ai/issues/449))
* Add a watchdog task to `FileLock` to unlock implicitly after given timeout. ([#467](https://github.com/lablup/backend.ai/issues/467))
* Replace redis library from aioredis to redis-py. ([#468](https://github.com/lablup/backend.ai/issues/468))
* Add `kernels.status_history` JSONB column for tracking time record on status transition of compute session. ([#480](https://github.com/lablup/backend.ai/issues/480))
* client,cli: Add `session status-history` command and its corresponding functional API to query the status transition history of compute sessions, with addition of the `status_history` GraphQL field in the manager ([#483](https://github.com/lablup/backend.ai/issues/483))
* Support for openSUSE release versions (both Leap and Tumbleweed) installation ([#485](https://github.com/lablup/backend.ai/issues/485))
* install-dev: Support editable installation of the web UI (`src/ai/backend/webui`) for ease of new frontend developers ([#501](https://github.com/lablup/backend.ai/issues/501))
* Add web handler to sending up-requests to pipeline server ([#503](https://github.com/lablup/backend.ai/issues/503))
* install-dev: Ensure that the user is on the build root directory (the repository's topmost directory). ([#524](https://github.com/lablup/backend.ai/issues/524))
* Allow general users to force termination of their own sessions. ([#525](https://github.com/lablup/backend.ai/issues/525))
* agent: Add `var-base-path` to `config.toml` to persistently store the last registry file, with automatic relocation of existing file upon agent startup ([#529](https://github.com/lablup/backend.ai/issues/529))
* client: Bump the compatible manager API version range to v6.20220615 ([#533](https://github.com/lablup/backend.ai/issues/533))

### Fixes
* Use `uname -m` instead of `uname -p` for better compatibility with many Linux variants and macOS when configuring the image registry and pulling the base Python image ([#505](https://github.com/lablup/backend.ai/issues/505))
* Fix `prepare()` not running when `start_session()` call hangs without raising Exception ([#514](https://github.com/lablup/backend.ai/issues/514))
* Update the sample docker-compose configuration so that the healthcheck for Redis container takes care of "loading" status of the Redis server ([#527](https://github.com/lablup/backend.ai/issues/527))
* Fix background tasks exiting without notice due to inappropriate exception handling inside task ([#530](https://github.com/lablup/backend.ai/issues/530))
* Fix agent crashing with `AttributeError: 'DockerKernel' object has no attribute 'runner'` error. ([#534](https://github.com/lablup/backend.ai/issues/534))
* logging: Fix accessing the missing `level` attribute of `LogRecord` objects ([#538](https://github.com/lablup/backend.ai/issues/538))
* Re-add null-check of the `'level'` key of the log record removed in #538 ([#540](https://github.com/lablup/backend.ai/issues/540))
* Set the minimum redis-py version to 4.3.4 due to an incompatible change of the `XAUTOCLAIM` API ([#541](https://github.com/lablup/backend.ai/issues/541))
* Ignore if a scanned `BUILD` or `build` target is a directory when scanning them to discover plugin entrypoints ([#550](https://github.com/lablup/backend.ai/issues/550))
* Fix typo & check file on install-dev.sh ([#551](https://github.com/lablup/backend.ai/issues/551))
* Upgrade external dependencies which provide new binary wheels for Python 3.10 and latest bug fixes ([#560](https://github.com/lablup/backend.ai/issues/560))

### Documentation Changes
* Add a daily development workflow guide for editable install of a package subset in this mon-repo to other projects ([#513](https://github.com/lablup/backend.ai/issues/513))

### Miscellaneous
* Upgrade the CPython version requirement to 3.10.5 ([#481](https://github.com/lablup/backend.ai/issues/481))
* Introduce `isort` as our linter and formatter to ensure consistency of the code style of import statements ([#495](https://github.com/lablup/backend.ai/issues/495))
* Let git ignore `/scratches` directory that kernels use. ([#497](https://github.com/lablup/backend.ai/issues/497))
* Manually upgrade pex version to 2.1.93 to avoid alternating platform tags in lockfiles depending on at which architecture the lockfiles are generated ([#498](https://github.com/lablup/backend.ai/issues/498))
* Upgrade pex to 2.1.94 which addresses a fresh `./pants expor` regression in #498's manual upgrade to 2.1.93 ([#506](https://github.com/lablup/backend.ai/issues/506))
* Upgrade Pants to 2.12.0rc3 to 2.12.0 ([#508](https://github.com/lablup/backend.ai/issues/508))
* Let `scripts/install-dev.sh` configure the standard git pre-push hook that runs fmt for all files and lint/check against the changed files ([#518](https://github.com/lablup/backend.ai/issues/518))
* Improve the latency of git pre push hook with better defaults and auto-detection of release branches ([#519](https://github.com/lablup/backend.ai/issues/519))
* Add git pre-commit hook to run a quick lint check and improve `install-dev.sh` script to properly create-or-update the git hook scripts ([#520](https://github.com/lablup/backend.ai/issues/520))
* Introduce https://dist.backend.ai/pypi/simple to serve custom prebuilt wheels and workaround upstream issues in a timely manner ([#545](https://github.com/lablup/backend.ai/issues/545))
* Remove manual grpcio wheel building section from `scripts/install-dev.sh` ([#547](https://github.com/lablup/backend.ai/issues/547))
* Upgrade pex to 2.1.99 to resolve intermittent failures in CI and venv generation in development setups ([#552](https://github.com/lablup/backend.ai/issues/552))


## 22.06.0b1 (2022-06-26)

### Breaking Changes
* The manager API version is updated to `v6.20220615`. ([#484](https://github.com/lablup/backend.ai/issues/484))

### Features
* Add optional handling of encrypted request payloads to webserver for environments without SSL termination for clients ([#484](https://github.com/lablup/backend.ai/issues/484))
* Upgrade `etcetra` version to 0.1.8. ([#494](https://github.com/lablup/backend.ai/issues/494))

### Fixes
* Refine `scripts/install-dev.sh`, `./py`, and `./pants-local` scripts to better detect and use an existing CPython available in the host ([#438](https://github.com/lablup/backend.ai/issues/438))
* Update test assertions to utilize the JSON output of mutation commands for forward compatibility ([#442](https://github.com/lablup/backend.ai/issues/442))
* Cli root passes ctx info and client cmds can create ctx from it. ([#457](https://github.com/lablup/backend.ai/issues/457))
* Correct missing dependencies due to different package-import names and indirect module references in the webserver ([#459](https://github.com/lablup/backend.ai/issues/459))
* Apply health check to the test fixture for creating an etcd container ([#460](https://github.com/lablup/backend.ai/issues/460))
* Add `export` keyword to set `BACKENDAI_TEST_CLIENT_ENV` as an environment variable. ([#463](https://github.com/lablup/backend.ai/issues/463))
* Ignore error messages caused in case of plugin-not-found to keep any test case from being interfered. ([#465](https://github.com/lablup/backend.ai/issues/465))
* Generate dummy data for test cases using `faker`. ([#466](https://github.com/lablup/backend.ai/issues/466))
* Let it ignore a permission error when calling Python `os.statvfs()` on a btrfs subvolume (e.g., `/var/lib/docker/btrfs`) as the intention of the call is to retrieve filesystem-level disk usage rather than subvolume statistics ([#473](https://github.com/lablup/backend.ai/issues/473))
* Update PostgreSQL, Redis and etcd versions ([#475](https://github.com/lablup/backend.ai/issues/475))
  - PostgreSQL: 13.1 -> 13.7 (old versions)12.3 -> 12.11
  - Redis: 6.2.6 -> 6.2.7
  - etcd: 3.5.1 -> 3.5.4 (old versions) 3.4.14 -> 3.4.18
* Skip measuring the stat for an agent registry item if it has not yet assigned container ID to prevent the occasional unhandled `UnboundLocalError`. ([#478](https://github.com/lablup/backend.ai/issues/478))
* Fix missing str to UUID conversion for `vfid` parameters in `get_quota` and `set_quota` manager-facing APIs in the storage proxy ([#487](https://github.com/lablup/backend.ai/issues/487))
* Add default value for `is_dir` parameter at rename_file function described in storage-proxy API ([#488](https://github.com/lablup/backend.ai/issues/488))
* Do not delete a virtual folder if there are other folders with the same name (in other folder hosts) and handle by new relevant exception, `TooManyVFoldersFound`, rather than blindly and dangerously deleting the first-queried one. ([#492](https://github.com/lablup/backend.ai/issues/492))

### Documentation Changes
* Mention Git LFS as a prerequisite explicitly and let the install-dev script run `git lfs pull` always ([#446](https://github.com/lablup/backend.ai/issues/446))
* add to require system pip package on Linux distribution for backend.ai installation. ([#461](https://github.com/lablup/backend.ai/issues/461))
* Migrate unmerged doc translation to monorepo, which is about FAQ and Key concept. ([#462](https://github.com/lablup/backend.ai/issues/462))

### Miscellaneous
* Publicly open the service IP address of the manager for when installed as development setup on a virtual machine ([#470](https://github.com/lablup/backend.ai/issues/470))
* Add `scripts/diff-release.py` to check backport status of pull requests ([#472](https://github.com/lablup/backend.ai/issues/472))


## 22.06.0.dev4 (2022-06-09)

### Fixes
* Fix upload failures of the Client SDK wheel packages due to a bogus syntax/rendering error of reST caused by specific backslash patterns ([#455](https://github.com/lablup/backend.ai/issues/455))


## 22.06.0.dev3 (2022-06-09)

### Features
* Add missing options (`parents`, `exist_ok`) for the `mkdir` CLI command and functional API in the client SDK ([#431](https://github.com/lablup/backend.ai/issues/431))
* Execute the keypair bootstrap script for batch compute session as well (previously it was only executed for interactive sessions) ([#437](https://github.com/lablup/backend.ai/issues/437))
* Implement plugin blocklist and utilize it to mutually exclude self-embedded plugins in the manager and agent for when they are executed under a unified virtualenv ([#453](https://github.com/lablup/backend.ai/issues/453))

### Fixes
* Dump kernel registry information to a file upon `KernelStartedEvent` or `KernelTerminatedEvent`. Saving at container start event did not ensure the existence of kernel object's `runner` attribute, which may cause `AttributeError` in restarting the Agent server. ([#441](https://github.com/lablup/backend.ai/issues/441))
* Replace `toml` with `tomli` which is chosen as the stdlib base implementation in Python 3.11 ([#445](https://github.com/lablup/backend.ai/issues/445))
* Always dump kernel registry information to a file upon agent termination. ([#450](https://github.com/lablup/backend.ai/issues/450))
* Agent startup error due to `UnboundLocalError` of `now` variable in dumping the last registry. ([#452](https://github.com/lablup/backend.ai/issues/452))

### Documentation Changes
* Add a guide for plugin related workflow with the new mono-style repository structure ([#434](https://github.com/lablup/backend.ai/issues/434))
* Merge the documentation of the Client SDK for Python into the unified docs ([#435](https://github.com/lablup/backend.ai/issues/435))

### Miscellaneous
* Fix `install-dev.sh` to work with RHEL-like distros by fixing system package names ([#372](https://github.com/lablup/backend.ai/issues/372))
* Improve auto-detection of plugins in development setups so that we no longer need to reinstall them after running `./pants export` ([#439](https://github.com/lablup/backend.ai/issues/439))


## 22.06.0.dev2 (2022-06-03)

* This ia another test release to verify automation of marking pre-releases.

## 22.06.0.dev1 (2022-06-03)

### Miscellaneous
* Migrate to a semi-mono repository that contains all first-party server-side components with automated dependency management via Pants ([#417](https://github.com/lablup/backend.ai/issues/417))
* Add a Pants plugin `towncrier_tool` to allow running towncrier for changelog generation ([#427](https://github.com/lablup/backend.ai/issues/427))
* Update readthedocs.org build configurations ([#428](https://github.com/lablup/backend.ai/issues/428))
* Update documentation for daily development workflows using Pants ([#429](https://github.com/lablup/backend.ai/issues/429))
* Automate creation of the release in GitHub when we commit tags ([#433](https://github.com/lablup/backend.ai/issues/433))


## 22.06.0.dev0 (2022-06-02)

* This is the first test release after migration to the mono-repository and the Pants build system.

## 22.03.3 and earlier

Please refer the following per-package changelogs.

* [Manager](https://github.com/lablup/backend.ai-manager/blob/main/CHANGELOG.md)
* [Agent](https://github.com/lablup/backend.ai-agent/blob/main/CHANGELOG.md)
* [Common](https://github.com/lablup/backend.ai-common/blob/main/CHANGELOG.md)
* [Client SDK for Python](https://github.com/lablup/backend.ai-client-py/blob/main/CHANGELOG.md)
* [Storage Proxy](https://github.com/lablup/backend.ai-storage-proxy/blob/main/CHANGELOG.md)
* [Webserver](https://github.com/lablup/backend.ai-webserver/blob/main/CHANGELOG.md)
