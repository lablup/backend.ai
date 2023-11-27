Migrating from the Docker Hub to cr.backend.ai
==============================================

As of November 2020, the Docker Hub has begun to limit the retention time and the rate of pulls of public images.
Since Backend.AI uses a number of Docker images with variety of access frequencies, we decided to migrate to our own container registry, https://cr.backend.ai.

It is strongly recommended to set a maintenance period if there are active users of the Backend.AI cluster to prevent new session starts during migration.
This registry migration does not affect existing running sessions, though the Docker image removal in the agent nodes can only be done after terminating all existing containers started with the old images and there will be brief disconnection of service ports as the manager requires to be restarted.

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

      $ sudo systemctl stop backendai-manager  # stop the manager daemon (may differ by setup)
      $ backend.ai mgr etcd put-json '' registry-config.json
      $ backend.ai mgr image rescan cr.backend.ai
      $ sudo systemctl start backendai-manager  # start the manager daemon (may differ by setup)

   * The agents will automatically pull the images since the image references are changed even when the new images are actually same to the existing ones.
     It is recommended to pull the essential images by yourself in the agents to avoid long waiting times when starting sessions using the ``docker pull`` command
     in the agent nodes.

   * Now the images are categorized with additional path prefix, such as ``stable`` and ``community``. More prefixes may be introduced in the future and some
     prefixes may be set only available to specific set of users/user groups, with dedicated credentials.

     For example, ``lablup/python:3.6-ubuntu18.04`` is now referred as ``cr.backend.ai/stable/python:3.6-ubuntu18.04``.

   * If you have configured image aliases, you need to update them manually as well, using the ``backend.ai mgr image alias`` command.
     This does not affect existing sessions running with old aliases.

4. Update the allowed docker registries policy for each domain using the ``backend.ai mgr dbshell`` command. Remove "index.docker.io" from the existing values and replace "..." below with your own domain names and additional registries.

   .. code-block:: sql

      SELECT name, allowed_docker_registries FROM domains;  -- check the current config
      UPDATE domains SET allowed_docker_registries = '{cr.backend.ai,...}' WHERE name = '...';

5. Now you may start new sessions using the images from the new registry.
6. After terminating all existing sessions using the old images from the Docker Hub (i.e., images whose names start with ``lablup/`` prefix), remove the image metadata and registry configuration using the manager CLI:

   .. code-block:: console

      $ backend.ai mgr etcd delete --prefix images/index.docker.io
      $ backend.ai mgr etcd delete --prefix config/docker/registry/index.docker.io

7. Run ``docker rmi`` commands to clean up the pulled images in the agent nodes.
   (Automatic/managed removal of images will be implemented in the future versions of Backend.AI)
