# Backend.AI Web Server

[![GitHub version](https://badge.fury.io/gh/lablup%2Fbackend.ai-webserver.svg)](https://badge.fury.io/gh/lablup%2Fbackend.ai-webserver) [![PyPI version](https://badge.fury.io/py/backend.ai-webserver.svg)](https://badge.fury.io/py/backend.ai-webserver)

A webapp hosting daemon which serves our `webui` as a SPA and proxies API requests


## Installation

Prepare a Python virtualenv (Python 3.9 or higher) and a Redis server (6.2 or higher).

```console
$ git clone https://github.com/lablup/backend.ai-webserver webserver
$ cd webserver
$ pip install -U -e .
$ cp webserver.sample.conf webserver.conf
```

## Mode

If `service.mode` is set "webui" (the default), the webserver handles
PWA-style fallbacks (e.g., serving `index.html` when there are no matching
files for the requested URL path).
The PWA must exclude `/server` and `/func` URL prefixes from its own routing
to work with the webserver's web sessions and the API proxy.

If it is set "static", the webserver serves the static files as-is,
without any fallbacks or hooking, while preserving the `/server` and `/func`
prefixed URLs and their functionalities.

If you want to serve web UI in webserver with "webui" mode, prepare static web UI source by choosing one of the followings.

### Option 1: Build web UI from source

Build **[backend.ai-webui](https://github.com/lablup/backend.ai-webui)** and copy all files under `build/bundle`
into the `src/ai/backend/web/static` directory.

### Option 2: Use pre-built web UI

To download and deploy web UI from pre-built source, do the following:

```console
cd src/ai/backend/web
curl --fail -sL https://github.com/lablup/backend.ai-webui/releases/download/v$TARGET_VERSION/backend.ai-webui-bundle-$TARGET_VERSION.zip > /tmp/bai-webui.zip
rm -rf static
mkdir static
cd static
unzip /tmp/bai-webui.zip
```
### Setup configuration for webserver

You don't have to write `config.toml` for the web UI as this webserver auto-generates it on-the-fly.

Edit `webserver.conf` to match with your environment.


## Usage

To execute web server, run command below. (for debugging, append a `--debug` flag)


```console
$ python -m ai.backend.web.server
```
