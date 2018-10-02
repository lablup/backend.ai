[![asciicast](https://asciinema.org/a/dCkoIy27EwVvO6sVVXNaAWcCp.png)](https://asciinema.org/a/dCkoIy27EwVvO6sVVXNaAWcCp)

For platform-specific instructions, please consult [the official documentation](https://docs.docker.com/engine/installation/).

Alternative way of docker installation on Linux (Ubuntu, CentOS, ...)

```console
$ curl -fsSL https://get.docker.io | sh
```
type your password to install docker. 

## Run docker commands without sudo (required)

By default, you need sudo to execute docker commands.  
To do so without sudo, add yourself to the system `docker` group.

```console
$ sudo usermod -aG docker $USER
```

It will work after restarting your login session.

## Install docker-compose (only for development/single-server setup)

You need to install docker-compose separately.  
Check out [the official documentation](https://docs.docker.com/compose/install/).

## Install nvidia-docker (only for GPU-enabled agents)

Check out [the official repository](https://github.com/NVIDIA/nvidia-docker) for instructions.