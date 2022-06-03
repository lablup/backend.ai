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
