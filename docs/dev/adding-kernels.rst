Adding New Kernel Images
========================

Overview
--------

Backend.AI supports running Docker containers to execute user-requested computations in a resource-constrained and isolated environment.
Most Docker container images can be *imported* as Backend.AI kernels with appropriate metadata annotations.


Kernel Runner
-------------

Every Backend.AI kernel should run a small daemon called "kernel runner".
It communicates with the Backend.AI Agent running in the host via ZeroMQ, and manages user code execution and in-container service processes.

The kernel runner provides runtime-specific implementations for various code execution modes such as the query mode and the batch mode, compatible with a number of well-known programming languages.
It also manages the process lifecycles of service-port processess.

To decouple the development and update cycles for Docker images and the Backend.AI Agent, we don't install the kernel runner inside images.
Instead, Backend.AI Agent mounts a special "krunner" volume as ``/opt/backend.ai`` inside containers.
This volume includes a customized static build of Python.
The kernel runner daemon package is mounted as one of the site packages of this Python distribution as well.
The agent also uses ``/opt/kernel`` as the directory for mounting other self-contained single-binary utilties.
This way, image authors do not have to bother with installing Python and Backend.AI specific software.
All dirty jobs like volume deployment, its content updates, and mounting for new containers are automatically managed by Backend.AI Agent.

Since the customized Python build and binary utilities need to be built for specific Linux distributions, we only support Docker images built on top of Alpine 3.8+, CentOS 7+, and Ubuntu 16.04+ base images.
Note that these three base distributions practically cover all commonly available Docker images.


Service Ports
-------------

As of Backend.AI v19.03, *service ports* are our preferred way to run computation workloads inside Backend.AI kernels.
It provides tunneled access to Jupyter Notebooks and other daemons running in containers.

As of Backend.AI v19.09, Backend.AI provides SSH (including SFTP and SCP) and ttyd (web-based xterm shell) as intrinsic services for all kernels.

As of Backend.AI v20.03, image authors may define their own service ports using service definition JSON files installed at ``/etc/backend.ai/service-defs`` in their images.

**(TODO: service-def syntax and interpretation)**

Note that there are a few TCP ports reserved for Backend.AI itself and intrinsic service ports.
The TCP port 2000 and 2001 is reserved for the query mode, whereas 2002 and 2003 are reserved for the native pseudo-terminal mode (stdin and stdout combined with stderr).


Metadata Labels
---------------

Any Docker image based on Alpine 3.8+, CentOS 7+, and Ubuntu 16.04+ become a Backend.AI kernel image if you add the following image labels:

* Required Labels

  * ``ai.backend.kernelspec``: ``1`` (this will be used for future versioning of the metadata specification)
  * ``ai.backend.features``: A list of constant strings indicating which Backend.AI kernel features are available for the kernel.

    - **batch**: Can execute user programs passed as files.
    - **query**: Can execute user programs passed as code snippets while keeping the context across multiple executions.
    - **uid-match**: As of 19.03, this must be specified always.
    - **user-input**: The query/batch mode supports interactive user inputs.

  * ``ai.backend.resource.min.*``: The minimum amount of resource to launch this kernel.
    At least, you must define the CPU core (``cpu``) and the main memory (``mem``).
    In the memory size values, you may use binary scale-suffixes such as ``m`` for ``MiB``, ``g`` for ``GiB``, etc.
  * ``ai.backend.base-distro``: Either "ubuntu16.04" or "alpine3.8".  Note that Ubuntu
    18.04-based kernels also need to use "ubuntu16.04" here.
  * ``ai.backend.runtime-type``: The type of kernel runner to use. (One of the
    directories in |ai.backend.kernel nslink|_)
  * ``ai.backend.runtime-path``: The path to the language runtime executable.

* Optional Labels

  * ``ai.backend.service-ports``: A list of 3-tuple strings specifying services available via network tunneling.
    Each tuple consists of the service name, the service type (one of **pty**, **http**, or **tcp**) and the container-side port number.
    Backend.AI manages the host-side port mapping and network tunneling via the API gateway automagically.
  * ``ai.backend.envs.corecount``: A comma-separated string list of environment variable names.
    They are set to the number of available CPU cores to the kernel container.
    It allows the CPU core restriction to be enforced to legacy parallel computation libraries.
    (e.g., ``JULIA_CPU_CORES``, ``OPENBLAS_NUM_THREADS``)

.. |ai.backend.kernel nslink| replace:: the ``ai.backend.kernels`` namespace.
.. _ai.backend.kernel nslink: https://github.com/lablup/backend.ai-agent/tree/master/src/ai/backend/kernel


Jail Policy
-----------

**(TODO: jail policy syntax and interpretation)**

.. _custom-jail-policy:

Adding Custom Jail Policy
~~~~~~~~~~~~~~~~~~~~~~~~~

To write a new policy implementation, extend `the jail policy interface <https://github.com/lablup/backend.ai-jail>`_ in Go.
Ebmed it inside your jail build.
Please give a look to existing jail policies as good references.


Example: An Ubuntu-based Kernel
-------------------------------

.. code-block:: dockerfile

    FROM ubuntu:16.04

    # Add commands for image customization
    RUN apt-get install ...

    # Backend.AI specifics
    COPY policy.yml /etc/backend.ai/jail/policy.yml
    LABEL ai.backend.kernelspec=1 \
          ai.backend.resource.min.cpu=1 \
          ai.backend.resource.min.mem=256m \
          ai.backend.envs.corecount="OPENBLAS_NUM_THREADS,OMP_NUM_THREADS,NPROC" \
          ai.backend.features="batch query uid-match user-input" \
          ai.backend.base-distro="ubuntu16.04" \
          ai.backend.runtime-type="python" \
          ai.backend.runtime-path="/usr/local/bin/python" \
          ai.backend.service-ports="ipython:pty:3000,jupyter:http:8080"


Implementation details
----------------------

The query mode I/O protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The input is a ZeroMQ's multipart message with two payloads.
The first payload should contain a unique identifier for the code snippet (usually a hash of it), but currently it is ignored (reserved for future caching implementations).
The second payload should contain a UTF-8 encoded source code string.

The reply is a ZeroMQ's multipart message with a single payload, containing a UTF-8 encoded string of the following JSON object:

.. code-block:: json

    {
        "stdout": "hello world!",
        "stderr": "oops!",
        "exceptions": [
            ["exception-name", ["arg1", "arg2"], false, null]
        ],
        "media": [
            ["image/png", "data:image/base64,...."]
        ],
        "options": {
            "upload_output_files": true
        }
    }

.. code-block: text


Each item in ``exceptions`` is an array composed of four items:
exception name,
exception arguments (optional),
a boolean indicating if the exception is raised outside the user code (mostly false),
and a traceback string (optional).

Each item in ``media`` is an array of two items: MIME-type and the data string.
Specific formats are defined and handled by the Backend.AI Media module.

The ``options`` field may present optionally.
If ``upload_output_files`` is true (default), then the agent uploads the files generated by user code in the working directory (``/home/work``) to AWS S3 bucket and make their URLs available in the front-end.

The pseudo-terminal mode protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to allow users to have real-time interactions with your kernel using web-based terminals, you should implement the PTY mode as well.
A good example is `our "git" kernel runner <https://github.com/lablup/backend.ai-kernel-runner/blob/master/src/ai/backend/kernel/git/__init__.py>`_.

The key concept is separation of the "outer" daemon and the "inner" target program (e.g., a shell).
The outer daemon should wrap the inner program inside a pseudo-tty.
As the outer daemon is completely hidden in terminal interaction by the end-users, the programming language may differ from the inner program.
The challenge is that you need to implement piping of ZeroMQ sockets from/to pseudo-tty file descriptors.
It is up to you how you implement the outer daemon, but if you choose Python for it, we recommend to use asyncio or similar event loop libraries such as tornado and Twisted to mulitplex sockets and file descriptors for both input/output directions.
When piping the messages, the outer daemon should not apply any specific transformation; it should send and receive all raw data/control byte sequences transparently because the front-end (e.g., terminal.js) is responsible for interpreting them.
Currently we use PUB/SUB ZeroMQ socket types but this may change later.

Optionally, you may run the query-mode loop side-by-side.
For example, our git kernel supports terminal resizing and pinging commands as the query-mode inputs.
There is no fixed specification for such commands yet, but the current CodeOnWeb uses the followings:

 * ``%resize <rows> <cols>``: resize the pseudo-tty's terminal to fit with the web terminal element in user browsers.
 * ``%ping``: just a no-op command to prevent kernel idle timeouts while the web terminal is open in user browsers.

A best practice (not mandatory but recommended) for PTY mode kernels is to automatically respawn the inner program if it terminates (e.g., the user has exited the shell) so that the users are not locked in a "blank screen" terminal.
