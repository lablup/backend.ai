Session Templates
=================

Creating and starting session template
--------------------------------------

Users may define commonly used set of session creation parameters as
reusable templates.

A session template includes common session parameters such as resource
slots, vfolder mounts, the kernel image to use, and etc.
It also support an extra feature that automatically clones a Git repository
upon startup as a bootstrap command.

The following sample shows how a session template looks like:

.. code-block:: yaml

  ---
  api_version: v1
  kind: taskTemplate
  metadata:
    name: template1234
    tag: example-tag
  spec:
    kernel:
      environ:
        MYCONFIG: XXX
      git:
        branch: '19.09'
        commit: 10daee9e328876d75e6d0fa4998d4456711730db
        repository: https://github.com/lablup/backend.ai-agent
        destinationDir: /home/work/baiagent
      image: python:3.6-ubuntu18.04
    resources:
      cpu: '2'
      mem: 4g
    mounts:
      hostpath-test: /home/work/hostDesktop
      test-vfolder:
    sessionType: interactive

The ``backend.ai sesstpl`` command set provides the basic CRUD operations
of user-specific session templates.

The ``create`` command accepts the YAML content either piped from the
standard input or read from a file using ``-f`` flag:

.. code-block:: console

  $ backend.ai sesstpl create < session-template.yaml
  # -- or --
  $ backend.ai sesstpl create -f session-template.yaml

Once the session template is uploaded, you may use it to start a new
session:

.. code-block:: console

  $ backend.ai start-template <templateId>

with substituting ``<templateId>`` to your template ID.

Other CRUD command examples are as follows:

.. code-block:: console

  $ backend.ai sesstpl update <templateId> < session-template.yaml
  $ backend.ai sesstpl list
  $ backend.ai sesstpl get <templateId>
  $ backend.ai sesstpl delete <templateId>


Full syntax for task template
-----------------------------

.. code-block:: text

  ---
  api_version or apiVersion: str, required
  kind: Enum['taskTemplate', 'task_template'], required
  metadata: required
    name: str, required
    tag: str (optional)
  spec:
    type or sessionType: Enum['interactive', 'batch'] (optional), default=interactive
    kernel:
      image: str, required
      environ: map[str, str] (optional)
      run: (optional)
        bootstrap: str (optional)
        stratup or startup_command or startupCommand: str (optional)
      git: (optional)
        repository: str, required
        commit: str (optional)
        branch: str (optional)
        credential: (optional)
          username: str
          password: str
        destination_dir or destinationDir: str (optional)
    mounts: map[str, str] (optional)
    resources: map[str, str] (optional)
