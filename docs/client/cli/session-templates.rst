Session Templates
=================

Creating and starting session template
--------------------------------------

Users may define commonly used set of session creation parameters as
reusable templates.

A session template includes common session parameters such as resource
slots, vfolder mounts, the kernel iamge to use, and etc.
It also support an extra feature that automatically clones a Git repository
upon startup as a bootstrap command.

The following sample shows how a session template looks like:

.. code-block:: yaml

  session_templates:
    - template:
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
              branch: '22.03'
              commit: e59bd61a196a74eb158f9fbcbccd37e1c48dcb55
              repository: https://github.com/lablup/backend.ai
              destinationDir: /home/work/bai
            image: cr.backend.ai/multiarch/python:3.9-ubuntu20.04
          resources:
            cpu: '2'
            mem: 4g
          mounts:
            hostpath-test: /home/work/hostDesktop
            test-vfloder:
          sessionType: 'interactive'

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

  $ backend.ai session create-from-template <templateId>

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

  session_templates:
    - template:
        api_version or apiVersion: str, required
        kind: Enum['taskTemplate', 'task_template'], required
        metadata:
          name: str, required
          tag: str (optional)
        spec:
          type or session_type or sessionType: Enum['interactive', 'batch'] (optional), default=interactive
          kernel:
            image: str, required
            architecture: str (optional), default=x86_64
            environ: map[str, str] (optional)
              MYCONFIG: XXX
            run: (optional)
              bootstrap: str (optional)
              startup or startup_command or startupCommand: str (optional)
            git: (optional)
              repository: str, required
              commit: str (optional)
              branch: str (optional)
              credential: (optional)
                username: str
                password: str
              destination_dir or destinationDir: str (optional)
          scaling_group: str (optional)
          mounts: map[str, str] (optional)
          resources: map[str, str] (optional)
            cpu: '1'
            mem: '320m'
          agent_list or agentList: list[str] (optional)
