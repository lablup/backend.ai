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

## 22.03.13 (2022-08-18)
* A follow-up hotfix for [#664](https://github.com/lablup/backend.ai/issues/664)


## 22.03.12 (2022-08-18)

### Fixes
* Add missing lazy-imported cli modules in the package ([#664](https://github.com/lablup/backend.ai/issues/664))


## 22.03.11 (2022-08-18)

### Features
* Accept the explicit "s" (seconds) unit suffix as well in `common.validators.TimeDuration` ([#570](https://github.com/lablup/backend.ai/issues/570))
* Support wsproxy v2 when the coordinator's user-accessible URL is different from the manager-accessible URL (usually when the user is separated from the Backend.AI service by NAT) ([#582](https://github.com/lablup/backend.ai/issues/582))
* Add `common.logging.LocalLogger` to improve logging outputs in test cases, which does not use the relay handler to send log records to another (parent) process but just the standard Python logging subsystem ([#630](https://github.com/lablup/backend.ai/issues/630))
* Use the full terminal width when formatting CLI help texts for better readability ([#662](https://github.com/lablup/backend.ai/issues/662))

### Fixes
* Ignore if a scanned `BUILD` or `build` target is a directory when scanning them to discover plugin entrypoints ([#550](https://github.com/lablup/backend.ai/issues/550))
* web: Force the keypair-based auth mode regardless to env-vars ([#564](https://github.com/lablup/backend.ai/issues/564))
* Fixed a Regex/shell escaping issue when updating var-base-path by changing parsing. ([#567](https://github.com/lablup/backend.ai/issues/567))
* install-dev: Add compatibility checks for `-f` option of the `docker compose` (v2) commands in the user home directory and system-wide directory ([#602](https://github.com/lablup/backend.ai/issues/602))
* Pin `hiredis` version to 1.1.0 (the version auto-inferred from `redis-py` is 2.0) to avoid a potential memory corruption error, such as "free(): invalid pointer" upon termination ([#636](https://github.com/lablup/backend.ai/issues/636))
* Improve null-checks when querying allowed vfolder hosts to prevent internal server errors when there are no allowed vfolder hosts ([#638](https://github.com/lablup/backend.ai/issues/638))
* Fix a spurious insufficient privilege error when running `backend.ai run` command as a normal user due to a mishandling of the default value of `--assign-agent` CLI option ([#639](https://github.com/lablup/backend.ai/issues/639))
* Fix `FileLock` not acquiring lock forever when lock file is created without write permission to manager processes' owner ([#642](https://github.com/lablup/backend.ai/issues/642))
* Change `client.cli` to use `ai.backend.cli.main:main` as its root CommandGroup. ([#650](https://github.com/lablup/backend.ai/issues/650))

### Miscellaneous
* Upgrade Pants to 2.12.0 to 2.13.0rc0 to take advantage of the latest bug fixes and improvements ([#589](https://github.com/lablup/backend.ai/issues/589))
* Revamp and refactor BUILD files to make Pants to handle fine-grained target selection better via per-directory BUILD files and utilize automatic internal-dependency inferences whenever possible, with unification of the source target names to `:src` (previously, `:lib` and `:service`) ([#627](https://github.com/lablup/backend.ai/issues/627))


## 22.03.10 (2022-07-18)

### Features
* install-dev: Support editable installation of the web UI (`src/ai/backend/webui`) for ease of new frontend developers ([#501](https://github.com/lablup/backend.ai/issues/501))
* Allow general users to force termination of their own sessions. ([#525](https://github.com/lablup/backend.ai/issues/525))
* agent: Add `var-base-path` to `config.toml` to persistently store the last registry file, with automatic relocation of existing file upon agent startup ([#529](https://github.com/lablup/backend.ai/issues/529))

### Fixes
* Fix agent crashing with `AttributeError: 'DockerKernel' object has no attribute 'runner'` error. ([#534](https://github.com/lablup/backend.ai/issues/534))
* logging: Fix accessing the missing `level` attribute of `LogRecord` objects ([#538](https://github.com/lablup/backend.ai/issues/538))
* Re-add null-check of the `'level'` key of the log record removed in #538 ([#540](https://github.com/lablup/backend.ai/issues/540))
* Fix typo & check file on install-dev.sh ([#551](https://github.com/lablup/backend.ai/issues/551))
* Upgrade external dependencies which provide new binary wheels for Python 3.10 and latest bug fixes ([#560](https://github.com/lablup/backend.ai/issues/560))

### Miscellaneous
* Introduce https://dist.backend.ai/pypi/simple to serve custom prebuilt wheels and workaround upstream issues in a timely manner ([#545](https://github.com/lablup/backend.ai/issues/545))
* Remove manual grpcio wheel building section from `scripts/install-dev.sh` ([#547](https://github.com/lablup/backend.ai/issues/547))
* Upgrade pex to 2.1.99 to resolve intermittent failures in CI and venv generation in development setups ([#552](https://github.com/lablup/backend.ai/issues/552))


## 22.03.9 (2022-07-10)

### Features
* install-dev: Ensure that the user is on the build root directory (the repository's topmost directory). ([#524](https://github.com/lablup/backend.ai/issues/524))
* client: Bump the compatible manager API version range to v6.20220615 ([#533](https://github.com/lablup/backend.ai/issues/533))

### Fixes
* Use `uname -m` instead of `uname -p` for better compatibility with many Linux variants and macOS when configuring the image registry and pulling the base Python image ([#505](https://github.com/lablup/backend.ai/issues/505))
* Fix `prepare()` not running when `start_session()` call hangs without raising Exception ([#514](https://github.com/lablup/backend.ai/issues/514))
* Update the sample docker-compose configuration so that the healthcheck for Redis container takes care of "loading" status of the Redis server ([#527](https://github.com/lablup/backend.ai/issues/527))
* Fix background tasks exiting without notice due to inappropriate exception handling inside task ([#530](https://github.com/lablup/backend.ai/issues/530))

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


## 22.03.8 (2022-06-26)

### Breaking Changes
* The manager API version is updated to `v6.20220615`. ([#484](https://github.com/lablup/backend.ai/issues/484))

### Features
* Add optional handling of encrypted request payloads to webserver for environments without SSL termination for clients ([#484](https://github.com/lablup/backend.ai/issues/484))

### Fixes
* Skip measuring the stat for an agent registry item if it has not yet assigned container ID to prevent the occasional unhandled `UnboundLocalError`. ([#478](https://github.com/lablup/backend.ai/issues/478))
* Fix missing str to UUID conversion for `vfid` parameters in `get_quota` and `set_quota` manager-facing APIs in the storage proxy ([#487](https://github.com/lablup/backend.ai/issues/487))
* Add default value for `is_dir` parameter at rename_file function described in storage-proxy API ([#488](https://github.com/lablup/backend.ai/issues/488))
* Do not delete a virtual folder if there are other folders with the same name (in other folder hosts) and handle by new relevant exception, `TooManyVFoldersFound`, rather than blindly and dangerously deleting the first-queried one. ([#492](https://github.com/lablup/backend.ai/issues/492))


## 22.03.7 (2022-06-16)

### Fixes
* Update test assertions to utilize the JSON output of mutation commands for forward compatibility ([#442](https://github.com/lablup/backend.ai/issues/442))
* Cli root passes ctx info and client cmds can create ctx from it. ([#457](https://github.com/lablup/backend.ai/issues/457))
* Apply health check to the test fixture for creating an etcd container ([#460](https://github.com/lablup/backend.ai/issues/460))
* Add `export` keyword to set `BACKENDAI_TEST_CLIENT_ENV` as an environment variable. ([#463](https://github.com/lablup/backend.ai/issues/463))
* Ignore error messages caused in case of plugin-not-found to keep any test case from being interfered. ([#465](https://github.com/lablup/backend.ai/issues/465))
* Generate dummy data for test cases using `faker`. ([#466](https://github.com/lablup/backend.ai/issues/466))
* Let it ignore a permission error when calling Python `os.statvfs()` on a btrfs subvolume (e.g., `/var/lib/docker/btrfs`) as the intention of the call is to retrieve filesystem-level disk usage rather than subvolume statistics ([#473](https://github.com/lablup/backend.ai/issues/473))
* Update PostgreSQL, Redis and etcd versions ([#475](https://github.com/lablup/backend.ai/issues/475))
   - PostgreSQL: 13.1 -> 13.7 (old versions)12.3 -> 12.11
   - Redis: 6.2.6 -> 6.2.7
   - etcd: 3.5.1 -> 3.5.4 (old versions) 3.4.14 -> 3.4.18

### Miscellaneous
* Publicly open the service IP address of the manager for when installed as development setup on a virtual machine ([#470](https://github.com/lablup/backend.ai/issues/470))


## 22.03.6 (2022-06-10)

### Fixes
* Refine `scripts/install-dev.sh`, `./py`, and `./pants-local` scripts to better detect and use an existing CPython available in the host ([#438](https://github.com/lablup/backend.ai/issues/438))
* Fix upload failures of the Client SDK wheel packages due to a bogus syntax/rendering error of reST caused by specific backslash patterns ([#455](https://github.com/lablup/backend.ai/issues/455))
* Correct missing dependencies due to different package-import names and indirect module references in the webserver ([#459](https://github.com/lablup/backend.ai/issues/459))

### Documentation Changes
* Mention Git LFS as a prerequisite explicitly and let the install-dev script run `git lfs pull` always ([#446](https://github.com/lablup/backend.ai/issues/446))


## 22.03.5 (2022-06-08)

### Features
* Implement plugin blocklist and utilize it to mutually exclude self-embedded plugins in the manager and agent for when they are executed under a unified virtualenv ([#453](https://github.com/lablup/backend.ai/issues/453))

### Fixes
* Agent startup error due to `UnboundLocalError` of `now` variable in dumping the last registry. ([#452](https://github.com/lablup/backend.ai/issues/452))


## 22.03.4 (2022-06-08)

### Fixes
* Always dump kernel registry information to a file upon agent termination. ([#450](https://github.com/lablup/backend.ai/issues/450))


## 22.03.4rc1 (2022-06-08)

### Features
* Add missing options (`parents`, `exist_ok`) for the `mkdir` CLI command and functional API in the client SDK ([#431](https://github.com/lablup/backend.ai/issues/431))
* Execute the keypair bootstrap script for batch compute session as well (previously it was only executed for interactive sessions) ([#437](https://github.com/lablup/backend.ai/issues/437))

### Fixes
* Dump kernel registry information to a file upon `KernelStartedEvent` or `KernelTerminatedEvent`. Saving at container start event did not ensure the existence of kernel object's `runner` attribute, which may cause `AttributeError` in restarting the Agent server. ([#441](https://github.com/lablup/backend.ai/issues/441))

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
