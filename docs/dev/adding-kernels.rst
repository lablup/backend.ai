Adding New Kernel Images
========================

Overview
--------

Backend.AI supports running Docker containers to execute user-requested computations in a resource-constrained and isolated environment.
Most Docker container images can be *imported* as Backend.AI kernels with appropriate metadata annotations.

1. Prepare a Docker image based on Ubuntu 16.04/18.04, CentOS 7.6, or Alpine 3.8.
2. Create a Dockerfile that does:

  - Install the OpenSSL library in the image for the kernel runner (if not installed).
  - Add metadata labels.
  - Add service definition files.
  - Add a jail policy file.

3. Build a derivative image using the Dockerfile.
4. Upload the image to a Docker registry to use with Backend.AI.


Kernel Runner
-------------

Every Backend.AI kernel should run a small daemon called "kernel runner".
It communicates with the Backend.AI Agent running in the host via ZeroMQ, and manages user code execution and in-container service processes.

The kernel runner provides runtime-specific implementations for various code execution modes such as the query mode and the batch mode, compatible with a number of well-known programming languages.
It also manages the process lifecycles of service-port processes.

To decouple the development and update cycles for Docker images and the Backend.AI Agent, we don't install the kernel runner inside images.
Instead, Backend.AI Agent mounts a special "krunner" volume as ``/opt/backend.ai`` inside containers.
This volume includes a customized static build of Python.
The kernel runner daemon package is mounted as one of the site packages of this Python distribution as well.
The agent also uses ``/opt/kernel`` as the directory for mounting other self-contained single-binary utilities.
This way, image authors do not have to bother with installing Python and Backend.AI specific software.
All dirty jobs like volume deployment, its content updates, and mounting for new containers are automatically managed by Backend.AI Agent.

Since the customized Python build and binary utilities need to be built for specific Linux distributions, we only support Docker images built on top of Alpine 3.8+, CentOS 7+, and Ubuntu 16.04+ base images.
Note that these three base distributions practically cover all commonly available Docker images.

Image Prerequisites
~~~~~~~~~~~~~~~~~~~

For glibc-based (most) Linux kernel images, you don't have to add anything to the existing container image as we use a statically built Python distribution with precompiled wheels to run the kernel runner.
The only requirement is that it should be compatible with `manylinux2014 <https://peps.python.org/pep-0599/#the-manylinux2014-policy>`_ or later.

For musl-based Linux kernel images (e.g., Alpine), you have to install ``libffi`` and ``sqlite-libs`` as the minimum.
Please also refer `the Dockerfile to build a minimal compatible image <https://github.com/lablup/backend.ai-krunner-alpine/blob/master/compat-test.Dockerfile>`_.


Metadata Labels
---------------

Any Docker image based on Alpine 3.17+, CentOS 7+, and Ubuntu 16.04+ which satisfies the above prerequisites may become a Backend.AI kernel image if you add the following image labels:

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

    - **python**: This runtime is for Python-based kernels,
      allowing the given Python executable accessible via the query and batch mode, also as a Jupyter kernel service.
    - **app**: This runtime does not support code execution in the query/batch modes but just manages the service port processes.
      For custom kernel images with their own service ports for their main applications,
      this is the most frequently used runtime type for derivative images.
    - For the full list of available runtime types, |ai.backend.kernel modlink|_

  * ``ai.backend.runtime-path``: The path to the language runtime executable.

* Optional Labels

  * ``ai.backend.role``: ``COMPUTE`` (default if unspecified) or ``INFERENCE``
  * ``ai.backend.service-ports``: A list of port mapping declaration strings for services supported by the image. (See the next section for details)
    Backend.AI manages the host-side port mapping and network tunneling via the API gateway automagically.
  * ``ai.backend.endpoint-ports``: A comma-separated name(s) of service port(s) to be bound with the service endpoint. (At least one is required in inference sessions)
  * ``ai.backend.model-path``: The path to mount the target model's target version storage folder. (Required in inference sessions)
  * ``ai.backend.envs.corecount``: A comma-separated string list of environment variable names.
    They are set to the number of available CPU cores to the kernel container.
    It allows the CPU core restriction to be enforced to legacy parallel computation libraries.
    (e.g., ``JULIA_CPU_CORES``, ``OPENBLAS_NUM_THREADS``)

.. |ai.backend.kernel nslink| replace:: the ``ai.backend.kernels`` namespace.
.. _ai.backend.kernel nslink: https://github.com/lablup/backend.ai-agent/tree/main/src/ai/backend/kernel
.. |ai.backend.kernel modlink| replace:: check out the ``lang_map`` variable at the ``ai.backend.kernels`` module code
.. _ai.backend.kernel modlink: https://github.com/lablup/backend.ai-agent/blob/main/src/ai/backend/kernel/__init__.py


Service Ports
-------------

As of Backend.AI v19.03, *service ports* are our preferred way to run computation workloads inside Backend.AI kernels.
It provides tunneled access to Jupyter Notebooks and other daemons running in containers.

As of Backend.AI v19.09, Backend.AI provides SSH (including SFTP and SCP) and ttyd (web-based xterm shell) as intrinsic services for all kernels.
"Intrinsic" means that image authors do not have to do anything to support/enable the services.

As of Backend.AI v20.03, image authors may define their own service ports using service definition JSON files installed at ``/etc/backend.ai/service-defs`` in their images.

Port Mapping Declaration
~~~~~~~~~~~~~~~~~~~~~~~~

A custom service port should define two things.
First, the image label ``ai.backend.service-ports`` contains the port mapping declarations.
Second, the service definition file which specifies how to start the service process.

A port mapping declaration is composed of three values: the service name, the protocol, and the container-side port number.
The label may contain multiple port mapping declarations separated by commas, like the following example:

.. code-block::

   jupyter:http:8080,tensorboard:http:6006

The name may be a non-empty arbitrary ASCII alphanumeric string.
We use the kebab-case for it.
The protocol may be one of ``tcp``, ``http``, and ``pty``, but currently most services use ``http``.

Note that there are a few port numbers reserved for Backend.AI itself and intrinsic service ports.
The TCP port 2000 and 2001 is reserved for the query mode, whereas 2002 and 2003 are reserved for the native pseudo-terminal mode (stdin and stdout combined with stderr), 2200 for the intrinsic SSH service, and 7681 for the intrinsic ttyd service.

Up to Backend.AI 19.09, this was the only method to define a service port for images, and the service-specific launch sequences were all hard-coded in the ``ai.backend.kernel`` module.

Service Definition DSL
~~~~~~~~~~~~~~~~~~~~~~

Now the image author should define the service launch sequences using a DSL (domain-specific language).
The service definitions are written as JSON files in the container's ``/etc/backend.ai/service-defs`` directory.
The file names must be same as the name parts of the port mapping declarations.

For example, a sample service definition file for "jupyter" service (hence its filename must be ``/etc/backend.ai/service-defs/jupyter.json``) looks like:

.. code-block:: json

    {
        "prestart": [
          {
            "action": "write_tempfile",
            "args": {
              "body": [
                "c.NotebookApp.allow_root = True\n",
                "c.NotebookApp.ip = \"0.0.0.0\"\n",
                "c.NotebookApp.port = {ports[0]}\n",
                "c.NotebookApp.token = \"\"\n",
                "c.FileContentsManager.delete_to_trash = False\n"
              ]
            },
            "ref": "jupyter_cfg"
          }
        ],
        "command": [
            "{runtime_path}",
            "-m", "jupyterlab",
            "--no-browser",
            "--config", "{jupyter_cfg}"
        ],
        "url_template": "http://{host}:{port}/"
    }

A service definition is composed of three major fields: ``prestart`` that contains a list of prestart actions, ``command`` as a list of template-enabled strings, and an optional ``url_template`` as a template-enabled string that defines the URL presented to the end-user on CLI or used as the redirection target on GUI with wsproxy.

The "template-enabled" strings may have references to a contextual set of variables in curly braces.
All the variable substitution follows the Python's brace-style formatting syntax and rules.

Available predefined variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are a few predefined variables as follows:

* **ports**: A list of TCP ports used by the service. Most services have only one port. An item in the list may be referenced using bracket notation like ``{ports[0]}``.
* **runtime_path**: A string representing the full path to the runtime, as specified in the ``ai.backend.runtime-path`` image label.

Available prestart actions
^^^^^^^^^^^^^^^^^^^^^^^^^^

A prestart action is composed of two mandatory fields ``action`` and ``args`` (see the table below), and an optional field ``ref``.
The ``ref`` field defines a variable that stores the result of the action and can be referenced in later parts of the service definition file where the arguments are marked as "template-enabled".

.. list-table::
   :widths: 20 60 20
   :header-rows: 1

   * - Action Name
     - Arguments
     - Return
   * - ``write_file``
     - * ``body``: a list of string lines (template-enabled)
       * ``filename``: a string representing the file name (template-enabled)
       * ``mode``: an optional octal number as string, representing UNIX file permission (default: "755")
       * ``append``: an optional boolean. If set true, open the file in the appending mode.
     - None
   * - ``write_tempfile``
     - * ``body``: a list of string line (template-enabled)
       * ``mode``: an optional octal number as string, representing UNIX file permission (default: "755")
     - The generated file path
   * - ``mkdir``
     - * ``path``: the directory path (template-enabled) where parent directories are auto-created
     - None
   * - ``run_command``
     - * ``command``: the command-line argument list as passed to ``exec`` syscall (template-enabled)
     - A dictionary with two fields: ``out`` and ``err`` which contain the console output decoded as the UTF-8 encoding
   * - ``log``
     - * ``body``: a string to send as kernel log (template-enabled)
       * ``debug``: a boolean to lower the logging level to DEBUG (default is INFO)
     - None

.. warning::

   ``run_command`` action should return quickly, otherwise the session creation latency will be increased.
   If you need to run a background process, you must use its own options to let it daemonize or wrap as a background shell command (``["/bin/sh", "-c", "... &"]``).

Interpretation of URL template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``url_template`` field is used by the client SDK and wsproxy to fill up the actual URL presented to the end-user (or the end-user's web browser as the redirection target).
So its template variables are not parsed when starting the service, but they are parsed and interpolated by the clients.
There are only three fixed variables: ``{protocol}``, ``{host}``, and ``{port}``.

Here is a sample service-definition that utilizes the URL template:

.. code-block:: json

    {
      "command": [
        "/opt/noVNC/utils/launch.sh",
        "--vnc", "localhost:5901",
        "--listen", "{ports[0]}"
      ],
      "url_template": "{protocol}://{host}:{port}/vnc.html?host={host}&port={port}&password=backendai&autoconnect=true"
    }



Jail Policy
-----------

**(TODO: jail policy syntax and interpretation)**

.. _custom-jail-policy:

Adding Custom Jail Policy
~~~~~~~~~~~~~~~~~~~~~~~~~

To write a new policy implementation, extend `the jail policy interface <https://github.com/lablup/backend.ai-jail>`_ in Go.
Embed it inside your jail build.
Please give a look to existing jail policies as good references.


Example: An Ubuntu-based Kernel
-------------------------------

.. code-block:: dockerfile

    FROM ubuntu:16.04

    # Add commands for image customization
    RUN apt-get install ...

    # Backend.AI specifics
    RUN apt-get install libssl
    LABEL ai.backend.kernelspec=1 \
          ai.backend.resource.min.cpu=1 \
          ai.backend.resource.min.mem=256m \
          ai.backend.envs.corecount="OPENBLAS_NUM_THREADS,OMP_NUM_THREADS,NPROC" \
          ai.backend.features="batch query uid-match user-input" \
          ai.backend.base-distro="ubuntu16.04" \
          ai.backend.runtime-type="python" \
          ai.backend.runtime-path="/usr/local/bin/python" \
          ai.backend.service-ports="jupyter:http:8080"
    COPY service-defs/*.json /etc/backend.ai/service-defs/
    COPY policy.yml /etc/backend.ai/jail/policy.yml



Custom startup scripts (aka custom entrypoint)
----------------------------------------------

When the image has *preopen* service ports and/or an endpoint port, Backend.AI automatically sets up application proxy tunnels
as if the listening applications have already started.

To initialize and start such applications, put a shell script as ``/opt/container/bootstrap.sh`` when building the image.
This per-image bootstrap script is executed as *root* by the agent-injected ``entrypoint.sh``.

.. warning::

   Since Backend.AI overrides the command and the entrypoint of container images to run the kernel runner regardless of the image content,
   setting ``CMD`` or ``ENTRYPOINT`` in Dockerfile has **no effects**.
   You should use ``/opt/container/bootstrap.sh`` to migrate existing entrypoint/command wrappers.

.. warning::

   ``/opt/container/bootstrap.sh`` **must return immediately** to prevent the session from staying in the ``PREPARING`` status.
   This means that it should run service applications in background by *daemonization*.

To run a process as the user privilege, you should use ``su-exec`` which is also injected by the agent like:

.. code-block:: shell

   /opt/kernel/su-exec "${LOCAL_GROUP_ID}:${LOCAL_USER_ID}" /path/to/your/service


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
It is up to you how you implement the outer daemon, but if you choose Python for it, we recommend using asyncio or similar event loop libraries such as tornado and Twisted to mulitplex sockets and file descriptors for both input/output directions.
When piping the messages, the outer daemon should not apply any specific transformation; it should send and receive all raw data/control byte sequences transparently because the front-end (e.g., terminal.js) is responsible for interpreting them.
Currently we use PUB/SUB ZeroMQ socket types but this may change later.

Optionally, you may run the query-mode loop side-by-side.
For example, our git kernel supports terminal resizing and pinging commands as the query-mode inputs.
There is no fixed specification for such commands yet, but the current CodeOnWeb uses the followings:

 * ``%resize <rows> <cols>``: resize the pseudo-tty's terminal to fit with the web terminal element in user browsers.
 * ``%ping``: just a no-op command to prevent kernel idle timeouts while the web terminal is open in user browsers.

A best practice (not mandatory but recommended) for PTY mode kernels is to automatically respawn the inner program if it terminates (e.g., the user has exited the shell) so that the users are not locked in a "blank screen" terminal.
