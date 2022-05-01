Backend.AI Manager with API Gateway
===================================

Package Structure
-----------------

* `ai.backend`
  - `manager`: Abstraction of agents and computation kernels
  - `gateway`: User and Admin API (REST/GraphQL) gateway based on aiohttp

Installation
------------

Please visit [the installation guides](https://github.com/lablup/backend.ai/wiki).


### Kernel/system configuration

#### Recommended resource limits:

**`/etc/security/limits.conf`**
```
root hard nofile 512000
root soft nofile 512000
root hard nproc 65536
root soft nproc 65536
user hard nofile 512000
user soft nofile 512000
user hard nproc 65536
user soft nproc 65536
```

**sysctl**
```
fs.file-max=2048000
net.core.somaxconn=1024
net.ipv4.tcp_max_syn_backlog=1024
net.ipv4.tcp_slow_start_after_idle=0
net.ipv4.tcp_fin_timeout=10
net.ipv4.tcp_window_scaling=1
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_early_retrans=1
net.ipv4.ip_local_port_range="10000 65000"
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 12582912 16777216
net.ipv4.tcp_wmem=4096 12582912 16777216
```


### For development

#### Prerequisites

* `libnsappy-dev` or `snappy-devel` system package depending on your distro
* Python 3.6 or higher with [pyenv](https://github.com/pyenv/pyenv)
and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (optional but recommneded)
* Docker 18.03 or later with docker-compose (18.09 or later is recommended)

#### Common steps

Clone [the meta repository](https://github.com/lablup/backend.ai) and install a "halfstack"
configuration.  The halfstack configuration installs and runs several dependency daemons such as etcd in
the background.

```console
$ git clone https://github.com/lablup/backend.ai halfstack
$ cd halfstack
$ docker-compose -f docker-compose.halfstack.yml up -d
```

Then prepare the source clone of the agent as follows.
First install the current working copy.

```console
$ git clone https://github.com/lablup/backend.ai-manager manager
$ cd manager
$ pyenv virtualenv venv-manager
$ pyenv local venv-manager
$ pip install -U pip setuptools
$ pip install -U -r requirements/dev.txt
```

From now on, let's assume all shell commands are executed inside the virtualenv.

### Halfstack (single-node development & testing)

#### Recommended directory structure

* `backend.ai-dev`
  - `manager` (git clone from this repo)
  - `agent` (git clone from [the agent repo](https://github.com/lablup/backend.ai-agent))
  - `common` (git clone from [the common repo](https://github.com/lablup/backend.ai-common))

Install `backend.ai-common` as an editable package in the manager (and the agent) virtualenvs
to keep the codebase up-to-date.

```console
$ cd manager
$ pip install -U -e ../common -r requirements/dev.txt
```

#### Steps

Copy (or symlink) the halfstack configs:
```console
$ cp config/halfstack.toml ./manager.toml
$ cp config/halfstack.alembic.ini ./alembic.ini
```

Set up Redis:
```console
$ backend.ai mgr etcd put config/redis/addr 127.0.0.1:8110
```

> ℹ️ NOTE: You may replace `backend.ai mgr` with `python -m ai.backend.manager.cli` in case your `PATH` is unmodifiable.

Set up the public Docker registry:
```console
$ backend.ai mgr etcd put config/docker/registry/index.docker.io "https://registry-1.docker.io"
$ backend.ai mgr etcd put config/docker/registry/index.docker.io/username "lablup"
$ backend.ai mgr etcd rescan-images index.docker.io
```

Set up the vfolder paths:
```console
$ mkdir -p "$HOME/vfroot/local"
$ backend.ai mgr etcd put volumes/_mount "$HOME/vfroot"
$ backend.ai mgr etcd put volumes/_default_host local
```

Set up the allowed types of vfolder. Allowed values are "user" or "group".
If none is specified, "user" type is set implicitly:
```console
$ backend.ai mgr etcd put volumes/_types/user ""   # enable user vfolder
$ backend.ai mgr etcd put volumes/_types/group ""  # enable group vfolder
```

Set up the database:
```console
$ backend.ai mgr schema oneshot
$ backend.ai mgr fixture populate sample-configs/example-keypairs.json
$ backend.ai mgr fixture populate sample-configs/example-resource-presets.json
```

Then, run it (for debugging, append a `--debug` flag):

```console
$ backend.ai mgr start-server
```

To run tests:

```console
$ python -m flake8 src tests
$ python -m pytest -m 'not integration' tests
```

Now you are ready to install the agent.
Head to [the README of Backend.AI Agent](https://github.com/lablup/backend.ai-agent/blob/master/README.md).

NOTE: To run tests including integration tests, you first need to install and run the agent on the same host.

## Deployment

### Configuration

Put a TOML-formatted manager configuration (see the sample in `config/sample.toml`)
in one of the following locations:

 * `manager.toml` (current working directory)
 * `~/.config/backend.ai/manager.toml` (user-config directory)
 * `/etc/backend.ai/manager.toml` (system-config directory)

Only the first found one is used by the daemon.

Also many configurations shared by both manager and agent are stored in etcd.
As you might have noticed above, the manager provides a CLI interface to access and manipulate the etcd
data.  Check out the help page of our etcd command set:

```console
$ python -m ai.backend.manager.cli etcd --help
```

If you run etcd as a Docker container (e.g., via halfstack), you may use the native client as well.
In this case, PLEASE BE WARNED that you must prefix the keys with "/sorna/{namespace}" manaully:

```console
$ docker exec -it ${ETCD_CONTAINER_ID} /bin/ash -c 'ETCDCTL_API=3 etcdctl ...'
```

### Running from a command line

The minimal command to execute:

```sh
python -m ai.backend.gateway.server
```

For more arguments and options, run the command with `--help` option.

### Writing a wrapper script

To use with systemd, crontab, and other system-level daemons, you may need to write a shell script
that executes specific CLI commands provided by Backend.AI modules.

The following example shows how to set up pyenv and virtualenv for the script-local environment.
It runs the gateway server if no arguments are given, and execute the given arguments as a shell command
if any.
For instance, you may get/set configurations like: `run-manager.sh python -m ai.backend.manager.etcd ...`
where the name of scripts is `run-manager.sh`.

```bash
#! /bin/bash
if [ -z "$HOME" ]; then
  export HOME="/home/devops"
fi
if [ -z "$PYENV_ROOT" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
fi
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate venv-bai-manager

if [ "$#" -eq 0 ]; then
  exec python -m ai.backend.gateway.server
else
  exec "$@"
fi
```

### Networking

The manager and agent should run in the same local network or different
networks reachable via VPNs, whereas the manager's API service must be exposed to
the public network or another private network that users have access to.

The manager requires access to the etcd, the PostgreSQL database, and the Redis server.

| User-to-Manager TCP Ports | Usage |
|:-------------------------:|-------|
| manager:{80,443}          | Backend.AI API access |

| Manager-to-X TCP Ports | Usage |
|:----------------------:|-------|
| etcd:2379              | etcd API access |
| postgres:5432          | Database access |
| redis:6379             | Redis API access |

The manager must also be able to access TCP ports 6001, 6009, and 30000 to 31000 of the agents in default
configurations.  You can of course change those port numbers and ranges in the configuration.

| Manager-to-Agent TCP Ports | Usage |
|:--------------------------:|-------|
| 6001                       | ZeroMQ-based RPC calls from managers to agents |
| 6009                       | HTTP watcher API |
| 30000-31000                | Port pool for in-container services |


LICENSES
--------

[GNU Lesser General Public License](https://github.com/lablup/backend.ai-manager/blob/master/LICENSE)
[Dependencies](https://github.com/lablup/backend.ai-manager/blob/master/DEPENDENCIES.md)
