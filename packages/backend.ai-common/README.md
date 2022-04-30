Backend.AI Commons
==================

[![PyPI release version](https://badge.fury.io/py/backend.ai-common.svg)](https://pypi.org/project/backend.ai-common/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai-common.svg)
[![Build Status](https://travis-ci.com/lablup/backend.ai-common.svg?branch=master)](https://travis-ci.com/lablup/backend.ai-common)
[![Gitter](https://badges.gitter.im/lablup/backend.ai-common.svg)](https://gitter.im/lablup/backend.ai-common)

Common utilities library for Backend.AI


## Installation

```console
$ pip install backend.ai-common
```

## For development

```console
$ pip install -U pip setuptools
$ pip install -U -r requirements/dev.txt
```

### Running test suite

```console
$ python -m pytest
```

With the default halfstack setup, you may need to set the environment variable `BACKEND_ETCD_ADDR`
to specify the non-standard etcd service port (e.g., `localhost:8110`).

The tests for `common.redis` module requires availability of local TCP ports 16379, 16380, 16381,
26379, 26380, and 26381 to launch a temporary Redis sentinel cluster via `docker compose`.

In macOS, they require a local `redis-server` executable to be installed, preferably via `brew`,
because `docker compose` in macOS does not support host-mode networking and Redis *cannot* be
configured to use different self IP addresses to announce to the cluster nodes and clients.
