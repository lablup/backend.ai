Migrating from the Docker Hub to cr.backend.ai
==============================================

As of November 2020, the Docker Hub has begun to limit the retention time and the rate of pulls of public images.
Since Backend.AI uses a number of Docker images with variety of access frequencies, we decided to migrate to our own container registry, https://cr.backend.ai.

Migration Steps
---------------

1. Update your Backend.AI installation to the latest version (manager 20.03.11 or 20.09.0b2) to get support for Harbor v2 container registries.
2. Save the following JSON snippet as ``registry-config.json``.

   .. code-block:: json

      {
        "config": {
          "docker": {
            "registry": {
              "cr.backend.ai": {
                "": "https://cr.backend.ai",
                "type": "harbor2",
                "project": "stable,community"
              }
            }
          }
        }
      }

3. Run the following using the manager CLI on one of the manager nodes:

   .. code-block:: console

      $ backend.ai mgr etcd put-json '' registry-config.json
      $ backend.ai mgr etcd rescan-images cr.backend.ai

   * The agents will automatically pull the images since the image references are changed even when the new images are actually same to the existing ones.
     It is recommended to pull the essential images by yourself in the agents to avoid long waiting times when starting sessions using the ``docker pull`` command
     in the agent nodes.

   * Now the images are categorized with additional path prefix, such as ``stable`` and ``community``. More prefixes may be introduced in the future and some
     prefixes may be set only available to specific set of users/user groups, with dedicated credentials.

     For example, ``lablup/python:3.6-ubuntu18.04`` is now referred as ``cr.backend.ai/stable/python:3.6-ubuntu18.04``.

   * If you have configured image aliases, you need to udpate them manually as well, using the ``backend.ai mgr etcd alias`` command.
     This does not affect existing sessions running with old aliases.

4. Now you may start new sessions using the images from the new registry.
5. After terminating all existing sessions using the images from the Docker Hub (i.e., images whose names start with ``lablup/`` prefix), remove the registry configuration in the manager CLI:

   .. code-block:: console

      $ backend.ai mgr etcd delete --prefix images  # remove all image metadata
      $ backend.ai mgr etcd delete --prefix config/docker/registry/index.docker.io  # remove docker hub config
      $ backend.ai mgr etcd rescan-images  # recan from all registries

6. Run ``docker rmi`` commands to clean up the pulled images in the agent nodes.
   (Automatic/managed removal of images will be implemented in the future versions of Backend.AI)
