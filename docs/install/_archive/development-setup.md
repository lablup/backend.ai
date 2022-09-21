# Development Setup

Currently we support only \*NIX-compatible platforms (Linux or macOS).

# Requirement packages
* PostgreSQL: 9.6 
* etcd: v3.2.15
* redis: latest

## Prepare containers for external daemons

First install an appropriate version of Docker (later than 2017.03 version) and docker-compose (later than 1.21).
Check out the [[Install Docker]] guide.

<table><tr><td>:bulb:</td><td>
In this guide, <code>$WORKSPACE</code> means the absolute path to an arbitrary working directory in your system.<br>
To copy-and-paste commands in this guide, set <code>WORKSPACE</code> environment variable.<br>
The directory structure would look like after finishing this guide:
<ul>
<li><code>$WORKSPACE</code>
  <ul><li><code>backend.ai</code>
      <li><code>backend.ai-manager</code>
      <li><code>backend.ai-agent</code>
      <li><code>backend.ai-common</code>
      <li><code>backend.ai-client-py</code>
  </ul>
</ul>
</td></tr></table>

```console
$ cd $WORKSPACE
$ git clone https://github.com/lablup/backend.ai
$ cd backend.ai
$ docker-compose -f docker-compose.halfstack.yml up -d
$ docker ps  # you should see 3 containers running
```
[![asciicast](https://asciinema.org/a/Q2Y3JuwqYoJjG9RB64Ovcpal2.png)](https://asciinema.org/a/Q2Y3JuwqYoJjG9RB64Ovcpal2)

This will create and start PostgreSQL, Redis, and a single-instance etcd containers.
Note that PostgreSQL and Redis uses non-default ports by default (5442 and 6389 instead of 5432 and 6379)
to prevent conflicts with other application development environments.

## Prepare Python 3.6+

Check out [[Install Python via pyenv]] for instructions.  
Create the following virtualenvs: `venv-manager`, `venv-agent`, `venv-common`, and `venv-client`.

[![asciicast](https://asciinema.org/a/xcMY9g5iATrCchoziCbErwgbG.png)](https://asciinema.org/a/xcMY9g5iATrCchoziCbErwgbG)

## Prepare dependent libraries

Install `snappy` (brew on macOS), `libsnappy-dev` (Debian-likes), or `libsnappy-devel` (RHEL-likes) system package depending on your environment.

## Prepare server-side source clones

[![asciicast](https://asciinema.org/a/SKJv19aNu9XKiCTOF0ASXibDq.png)](https://asciinema.org/a/SKJv19aNu9XKiCTOF0ASXibDq)

Clone the Backend.AI source codes.

```console
$ cd $WORKSPACE
$ git clone https://github.com/lablup/backend.ai-manager
$ git clone https://github.com/lablup/backend.ai-agent
$ git clone https://github.com/lablup/backend.ai-common
```

Inside each directory, install the sources as editable packages.

<table><tr><td>:bulb:</td><td>
Editable packages makes Python to apply any changes of the source code in git clones immediately when importing the installed packages.
</td></tr></table>

```console
$ cd $WORKSPACE/backend.ai-manager
$ pyenv local venv-manager
$ pip install -U -r requirements-dev.txt
```

```console
$ cd $WORKSPACE/backend.ai-agent
$ pyenv local venv-agent
$ pip install -U -r requirements-dev.txt
```

```console
$ cd $WORKSPACE/backend.ai-common
$ pyenv local venv-common
$ pip install -U -r requirements-dev.txt
```

### (Optional) Symlink backend.ai-common in the manager and agent directories to the cloned source 

If you do this, your changes in the source code of the backend.ai-common directory will be reflected immediately to the manager and agent.
You should install backend.ai-common dependencies into `venv-manager` and `venv-agent` as well, but this is already done in the previous step.

```console
$ cd "$(pyenv prefix venv-manager)/src"
$ mv backend.ai-common backend.ai-common-backup
$ ln -s "$WORKSPACE/backend.ai-common" backend.ai-common
```

```console
$ cd "$(pyenv prefix venv-agent)/src"
$ mv backend.ai-common backend.ai-common-backup
$ ln -s "$WORKSPACE/backend.ai-common" backend.ai-common
```

## Initialize databases and load fixtures

Check out the [[Prepare Databases for Manager]] guide.

## Prepare Kernel Images

You need to pull the kernel container images first to actually spawn compute sessions.  
The kernel images here must have the tags specified in image-metadata.yml file.

```console
$ docker pull lablup/kernel-python:3.6-debian
```

For the full list of publicly available kernels, [check out the kernels repository.](https://github.com/lablup/backend.ai-kernels)

**NOTE:** You need to restart your agent if you pull images after starting the agent.

## Setting Linux capabilities to Python (Linux-only)

To allow Backend.AI to collect sysfs/cgroup resource usage statistics, the Python executable must have the following Linux capabilities (to run without "root"): `CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, and `CAP_DAC_OVERRIDE`.
You may use the following command to set them to the current virtualenv's Python executable.

```console
$ sudo setcap cap_sys_ptrace,cap_sys_admin,cap_dac_override+eip $(readlink -f $(pyenv which python))
```

## Running daemons from cloned sources

```console
$ cd $WORKSPACE/backend.ai-manager
$ ./scripts/run-with-halfstack.sh python -m ai.backend.gateway.server --service-port=8081 --debug
```

Note that through options, PostgreSQL and Redis ports set above for development environment are used. You may change other options to match your environment and personal configurations. (Check out `-h`/`--help`)

```console
$ cd $WORKSPACE/backend.ai-agent
$ mkdir -p scratches  # used as in-container scratch "home" directories
$ ./scripts/run-with-halfstack.sh python -m ai.backend.agent.server --scratch-root=`pwd`/scratches --debug --idle-timeout 30
```

※ The role of `run-with-halfstack.sh` script is to set appropriate environment variables so that the manager/agent daemons use the halfstack docker containers.


## Prepare client-side source clones

[![asciicast](https://asciinema.org/a/dJQKPrcmIliVkCX4ldSg3rPki.png)](https://asciinema.org/a/dJQKPrcmIliVkCX4ldSg3rPki)

```console
$ cd $WORKSPACE
$ git clone https://github.com/lablup/backend.ai-client-py
```

```console
$ cd $WORKSPACE/backend.ai-client-py
$ pyenv local venv-client
$ pip install -U -r requirements-dev.txt
```

Inside `venv-client`, now you can use the `backend.ai` command for testing and debugging.


## Running the client for the first time!

Write a shell script (e.g., `env_local.sh`) like below to easily switch the API endpoint and credentials for testing:

```sh
#! /bin/sh
export BACKEND_ENDPOINT=http://127.0.0.1:8081/
export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

Load this script (e.g., `source env_local.sh`) before you run the client against your server-side installation.

Now you can do `backend.ai ps` to confirm if there are no sessions running and run the hello-world:

```sh
$ cd $WORKSPACE/backend.ai-client-py
$ source env_local.sh  # check above
$ backend.ai run python -c 'print("hello")'
```