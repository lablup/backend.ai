# Install Agent

We assume that your system is configured with a sudoable admin user named `devops`.
Your Backend.AI manager should be already set up and running.

## Guide variables

⚠️ Prepare the values of the following variables before working with this page and replace their occurrences with the values when you follow the guide.

<table>
<tr><td><code>{NS}</code></td><td>The etcd namespace (just create a unique string like domain names)</td></tr>
<tr><td><code>{ETCDADDR}</code></td><td>The etcd cluster address (<code>{ETCDHOST}:{ETCDPORT}</code>, <code>localhost:2379</code> for development setup)</td></tr>
</table>

### Optional variables
<table>
<tr><td><code>{SSLCERT}</code></td><td>The path to your SSL certificate (bundled with CA chain certificates)</td></tr>
<tr><td><code>{SSLPKEY}</code></td><td>The path to your SSL private key</td></tr>
<tr><td><code>{S3AKEY}</code></td><td>The access key for AWS S3 or compatible services<sup><a href="#fn1">[1]</a></sup></td></tr>
<tr><td><code>{S3SKEY}</code></td><td>The secret key for AWS S3 or compatible services</td></tr>
<tr><td><code>{DDAPIKEY}</code></td><td>The Datadog API key</td></tr>
<tr><td><code>{DDAPPKEY}</code></td><td>The Datadog application key</td></tr>
<tr><td><code>{SENTRYURL}</code></td><td>The private Sentry report URL</td></tr>
</table>

## Install dependencies for daemonization

### Ubuntu

```console
$ sudo apt-get -y update
$ sudo apt-get -y dist-upgrade
$ sudo apt-get install -y ca-certificates git-core supervisor
```

Here are some optional but useful packages:

```console
$ sudo apt-get install -y vim tmux htop
```

### CentOS / RHEL

(TODO)

## Prepare CUDA (if available)

Check out the [[Install CUDA]] guide.

## Prepare Python 3.6+

Check out [[Install Python via pyenv]] for instructions.
Create a virtualenv named `venv-agent`.

**(Only in Linux)** To enable detailed resource statistics, give the Python executable to have `CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, and `CAP_DAC_OVERRIDE` capabilities.

```console
$ sudo setcap cap_sys_ptrace,cap_sys_admin,cap_dac_override+eip "$(readlink -f $(pyenv which python))"
```

## Install Backend.AI Agent as Package

```console
$ pyenv shell venv-agent
$ pip install -U setuptools pip
$ pip install -U backend.ai-agent
```

## Monitoring and Logging

Check out the [[Install Monitoring and Logging Tools]] guide.

## Configure supervisord

#### supervisord application config

```console
$ sudo vi /etc/supervisor/conf.d/apps.conf
```

```dosini
[program:backendai-agent]
user = devops
stopsignal = TERM
stopasgroup = true
command = /home/devops/run-agent.sh
```

#### pyenv + venv initialization script for non-login shells

```console
$ vi /home/devops/init-venv.sh
```

```shell
#!/bin/bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv shell venv-agent
```

#### Prepare scratch directory (place for kernel containers' `/home/work`)

```console
$ sudo mkdir -p /var/cache/scratches
$ sudo chown devops:devops /var/cache/scratches
```

#### The main program managed by supervisord

```console
$ vi /home/devops/run-agent.sh
```

```shell
source /home/devops/init-venv.sh
umask 0002
export AWS_ACCESS_KEY_ID="{S3AKEY}"
export AWS_SECRET_ACCESS_KEY="{S3SEKEY}"
export DATADOG_API_KEY={DDAPIKEY}
export DATADOG_APP_KEY={DDAPPKEY}
export RAVEN_URI="{SENTRYURL}"
exec python -m ai.backend.agent.server \
            --etcd-addr {ETCDADDR} \
            --namespace {NS} \
            --scratch-root=/var/cache/scratches
```

## Prepare Kernel Images

You need to pull the kernel container images first to actually spawn compute sessions.
The name and tag pairs of images must be also specified in `backend.ai-manager/sample-configs/image-metadata.yml` file imported into etcd.

Here are the pull commands for a few commonly used Python-based images:
```console
$ docker pull lablup/kernel-python:3.6-debian
$ docker pull lablup/kernel-python-tensorflow:1.8-py36
$ docker pull lablup/kernel-python-tensorflow:1.8-py36-gpu
```

For the full list of publicly available kernels, [check out the kernels repository.](https://github.com/lablup/backend.ai-kernels)

## Finally, Run!

```console
$ sudo supervisorctl reread
$ sudo supervisorctl start backendai-agent
```