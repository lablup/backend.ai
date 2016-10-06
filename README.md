Lablup Sorna
============

Sorna ("Software on Remote Networking Appliances") is a distributed back-end computation service with highly abstracted API.
Unlike AWS Lambda, it provides a preset of kernel images representing various programming environments and allows users to execute their code snippets without a cumbersome packaging process.

Components
----------

### Sorna Manager / API Gateway

It routes external API requests from front-end services to agent instances by checking the instance registry.

 * Package namespace: `sorna.manager`
 * https://github.com/lablup/sorna-manager

### Sorna Agent

It manages individual EC2 instances and launches/destroyes Docker containers where REPL daemons (kernels) run.
Each agent on a new EC2 instance self-registers itself to the instance registry via heartbeats.

 * Package namespace: `sorna.agent`
 * https://github.com/lablup/sorna-agent

### Sorna REPL

A set of small ZMQ-based REPL daemons in various programming languages and configurations.
It also includes a sandbox implemented using ptrace-based sytem call filtering written in Go.

 * https://github.com/lablup/sorna-repl
 * Each daemon is a separate program, usually named "run.{lang-specific-extension}".

### Sorna Common

A collection of utility modules commonly shared throughout Sorna projects, such as logging and messaging protocols.

 * Package namespaces: `sorna.proto`, `sorna`
 * https://github.com/lablup/sorna-common
 
### Sorna Client

A client library to access the Sorna API servers with ease.

 * Package namespaces: `sorna.client`
 * https://github.com/lablup/sorna-client

Development
-----------

### git flow

The sorna repositories use [git flow](http://danielkummer.github.io/git-flow-cheatsheet/index.html) to streamline branching during development and deployment.
We use the default configuration (master -> preparation for release, develop -> main development, feature/ -> features, etc.) as-is.

Deployment
----------

In the simplest setting, you may run sorna-manager and sorna-agnet in a screen or tmux session.
For more "production"-like setup, we recommend to use supervisord.

Example `/etc/supervisor/conf.d/apps.conf`:
```
[program:sorna-manager]
user = ubuntu
stopsignal = TERM
stopasgroup = true
command = /home/sorna/run-manager.sh

[program:sorna-agent]
user = ubuntu
stopsignal = TERM
stopasgroup = true
command = /home/sorna/run-agent.sh
```

Note that the user must have the same UID that the dockerizes sorna-repl daemons have: 1000.
`stopasgroup` must be set true for proper termination.

Example `run-manager.sh`:
```
#! /bin/bash
export HOME=/home/sorna
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
pyenv shell 3.5.2
python3 -m sorna.manager.server
```

The agents may run on the same instance where the manager runs, or multiple EC2 instances in an auto-scaling group.

Example `run-agent.sh`:
```
#! /bin/bash
export HOME=/home/sorna
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
pyenv shell 3.5.2
export AWS_ACCESS_KEY_ID="<your-access-key-for-s3>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key-for-s3>"
python3 -m sorna.agent.server --manager-addr tcp://sorna-manager.lablup:5001 --max-kernels 15
```

