# Demo Setup

[This meta-repository](https://github.com/lablup/backend.ai) provides a docker-compose configuration to fire up a single-node Backend.AI cluster running on your PC (http://localhost:8081).  

## Prerequisites
* All: [install Docker 17.06 or later](https://docs.docker.com/install/) with [docker-compose v1.21 or later](https://docs.docker.com/compose/install/)
* Linux users: change "docker.for.mac.localhost" in docker-compose.yml to "172.17.0.1"

### Notes
* This demo setup does *not* support GPUs.

## All you have to do

* Clone the repository
* Check out the prerequisites above
* `docker-compose up -d`
  - For Windows, `docker-compose -f docker-compose.win-demo.yml up -d`
* Pull some kernel images to try out

### Pulling kernel images

Pull the images on your host Docker daemon like:

```
$ docker pull lablup/kernel-python:latest
$ docker pull lablup/kernel-python-tensorflow:latest-dense
$ docker pull lablup/kernel-c:latest
```

By default this demo cluster already has metadata/alias information for [all publicly available Backend.AI kernels](https://github.com/lablup/backend.ai-kernels), so you don't have to manually register the pulled kernel information to the cluster but only have to *pull* those you want to try out.

### Using Clients

To access this local cluster, set the following configurations to your favoriate Backend.AI client:

```console
$ export BACKEND_ENDPOINT="http://localhost:8081"
$ export BACKEND_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
$ export BACKEND_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

With [our official Python client](http://pypi.python.org/pypi/backend.ai-client), you can do:

```console
$ backend.ai run python -c "print('hello world')"
✔ Session 9c737d84724173354fa10445d0b35fe0 is ready.
hello world
✔ Finished. (exit code = 0)

$ backend.ai run python-tensorflow:latest-dense -c "import tensorflow as tf; print(tf.__version__)"
✔ Session 950713741d5ed43a191704f2cd375ff0 is ready.
1.5.0
✔ Finished. (exit code = 0)
```

WARNING: This demo configuration is highly insecure. DO NOT USE in production!

## FAQ

* When launching a kernel, it says "Service Unavailable"!
  - Each image has different default resource requirements and your Docker daemon may have a too small amount of resources. For example, TensorFlow images require 8 GiB or more RAM for your Docker daemon.
  - Or, you might have launched 30 kernel sessions already, which is the default limit for this demo setup.
* What does the "dense" tag mean in the TensorFlow kernel images?
  - Images with "dense" tags are optimized for shared multi-tenancy environments. There is no difference in functionalities.