
Install monitoring and logging tools
====================================

The Backend.AI can use several 3rd-party monitoring and logging services.
Using them is completely optional.

Guide variables
---------------

⚠️ Prepare the values of the following variables before working with this page and replace their occurrences with the values when you follow the guide.


.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Name
     - Description
   * - ``{DDAPIKEY}``
     - >The Datadog API key
   * - ``{DDAPPKEY}``
     - The Datadog application key


Install Datadog agent
---------------------

`Datadog <https://www.datadoghq.com>`_ is a 3rd-party service to monitor the server resource usage.

.. code-block:: console

   $ DD_API_KEY={DDAPIKEY} bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/dd-agent/master/packaging/datadog-agent/source/install_agent.sh)"
