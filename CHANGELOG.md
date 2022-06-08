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
