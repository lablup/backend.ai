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
* Add a Pants plulgin `towncrier_tool` to allow running towncrier for changelog generation ([#427](https://github.com/lablup/backend.ai/issues/427))
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
