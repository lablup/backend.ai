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
