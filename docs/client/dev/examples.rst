Examples
========

Here are several examples to demonstrate the functional API usage.

Initialization of the API Client
--------------------------------

Implicit configuration from environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ai.backend.client.session import Session

    def main():
        with Session() as api_session:
            print(api_session.System.get_versions())

    if __name__ == "__main__":
        main()

.. seealso:: :doc:`/client/gsg/config`


Explicit configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ai.backend.client.config import APIConfig
    from ai.backend.client.session import Session

    def main():
        config = APIConfig(
            endpoint="https://api.backend.ai.local",
            endpoint_type="api",
            domain="default",
            group="default",  # the default project name to use
        )
        with Session(config=config) as api_session:
            print(api_session.System.get_versions())

    if __name__ == "__main__":
        main()

.. seealso:: :class:`ai.backend.client.config.APIConfig`

Asyncio-native API session
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    from ai.backend.client.session import AsyncSession

    async def main():
        async with AsyncSession() as api_session:
            print(api_session.System.get_versions())

    if __name__ == "__main__":
        asyncio.run(main())

.. seealso:: The interface of API client session objects: :mod:`ai.backend.client.session`


Working with Compute Sessions
-----------------------------

.. note::

   From here, we omit the ``main()`` function structure in the sample codes.

Listing currently running compute sessions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import functools
    from ai.backend.client.session import Session

    with Session() as api_session:
        fetch_func = functools.partial(
            api_session.ComputeSession.paginated_list,
            status="RUNNING",
        )
        current_offset = 0
        while True:
            result = fetch_func(page_offset=current_offset, page_size=20)
            if result.total_count == 0:
                # no items found
                break
            current_offset += len(result.items)
            for item in result.items:
               print(item)
            if current_offset >= result.total_count:
                # end of list
                break

Creating and destroying a compute session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ai.backend.client.session import Session

    with Session() as api_session:
        my_session = api_session.ComputeSession.get_or_create(
            "python:3.9-ubuntu20.04",      # registered container image name
            mounts=["mydata", "mymodel"],  # vfolder names
            resources={"cpu": 8, "mem": "32g", "cuda.device": 2},
        )
        print(my_session.id)
        my_session.destroy()



Accessing Container Applications
--------------------------------

    Launchable apps may vary for sessions. From here we illustrate
    an example to create a ttyd (web-based terminal) app,
    which is available for all Backend.AI sessions.

.. note::

    This example is only applicable for the Backend.AI cluster with
    AppProxy v2 enabled and configured. AppProxy v2 only ships with
    enterprise version of Backend.AI.


The ``ComputeSession.start_service()`` API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import requests

    from ai.backend.client.request import Request
    from ai.backend.client.session import Session

    app_name = "ttyd"

    with Session() as api_session:
        sess = api_session.ComputeSession.get_or_create(...)
        service_info = sess.start_service(app_name, login_session_token="dummy")
        app_proxy_url = f"{service_info['wsproxy_addr']}/v2/proxy/{service_info['token']}/{sess.id}/add?app={app_name}"
        resp = requests.get(app_proxy_url)
        body = resp.json()
        auth_url = body["url"]
        print(auth_url)  # opening this link from browser will navigate user to the terminal session

.. versionadded:: 23.09.8

   :meth:`ai.backend.client.func.session.ComputeSession.start_service()`

Set the value ``login_session_token`` to a dummy string like ``"dummy"`` as it is a trace of the legacy interface, which is no longer used.

Alternatively, in versions before 23.09.8, you may use the raw :class:`ai.backend.client.Request` to call the server-side ``start_service`` API.

.. code-block:: python

    import asyncio

    import aiohttp

    from ai.backend.client.request import Request
    from ai.backend.client.session import AsyncSession

    app_name = "ttyd"

    async def main():
        async with AsyncSession() as api_session:
            sess = api_session.ComputeSession.get_or_create(...)
            rqst = Request(
                "POST",
                f"/session/{sess.id}/start-service",
            )
            rqst.set_json({"app": app_name, "login_session_token": "dummy"})
            async with rqst.fetch() as resp:
                body = await resp.json()
                app_proxy_url = f"{body['wsproxy_addr']}/v2/proxy/{body['token']}/{sess.id}/add?app={app_name}"

            async with aiohttp.ClientSession() as client:
                async with client.get(app_proxy_url) as resp:
                    body = await resp.json()
                    auth_url = body["url"]
                    print(auth_url)  # opening this link from browser will navigate user to the terminal session

    if __name__ == "__main__":
        asyncio.run(main())


Code Execution via API
----------------------

Synchronous mode
~~~~~~~~~~~~~~~~

Snippet execution (query mode)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the minimal code to execute a code snippet with this client SDK.

.. code-block:: python

    import sys
    from ai.backend.client.session import Session

    with Session() as api_session:
        my_session = api_session.ComputeSession.get_or_create("python:3.9-ubuntu20.04")
        code = 'print("hello world")'
        mode = "query"
        run_id = None
        try:
            while True:
                result = my_session.execute(run_id, code, mode=mode)
                run_id = result["runId"]  # keeps track of this particular run loop
                for rec in result.get("console", []):
                    if rec[0] == "stdout":
                        print(rec[1], end="", file=sys.stdout)
                    elif rec[0] == "stderr":
                        print(rec[1], end="", file=sys.stderr)
                    else:
                        handle_media(rec)
                sys.stdout.flush()
                if result["status"] == "finished":
                    break
                else:
                    mode = "continued"
                    code = ""
        finally:
            my_session.destroy()

You need to take care of ``client_token`` because it determines whether to
reuse kernel sessions or not.
Backend.AI cloud has a timeout so that it terminates long-idle kernel sessions,
but within the timeout, any kernel creation requests with the same ``client_token``
let Backend.AI cloud to reuse the kernel.


Script execution (batch mode)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You first need to upload the files after creating the session and construct a
``opts`` struct.

.. code-block:: python

    import sys
    from ai.backend.client.session import Session

    with Session() as session:
        compute_sess = session.ComputeSession.get_or_create("python:3.6-ubuntu18.04")
        compute_sess.upload(["mycode.py", "setup.py"])
        code = ""
        mode = "batch"
        run_id = None
        opts = {
            "build": "*",  # calls "python setup.py install"
            "exec": "python mycode.py arg1 arg2",
        }
        try:
            while True:
                result = kern.execute(run_id, code, mode=mode, opts=opts)
                opts.clear()
                run_id = result["runId"]
                for rec in result.get("console", []):
                    if rec[0] == "stdout":
                        print(rec[1], end="", file=sys.stdout)
                    elif rec[0] == "stderr":
                        print(rec[1], end="", file=sys.stderr)
                    else:
                        handle_media(rec)
                sys.stdout.flush()
                if result["status"] == "finished":
                    break
                else:
                    mode = "continued"
                    code = ""
        finally:
            compute_sess.destroy()


Handling user inputs
^^^^^^^^^^^^^^^^^^^^

Inside the while-loop for ``kern.execute()`` above,
change the if-block for ``result['status']`` as follows:

.. code:: python

  ...
  if result["status"] == "finished":
      break
  elif result["status"] == "waiting-input":
      mode = "input"
      if result["options"].get("is_password", False):
          code = getpass.getpass()
      else:
          code = input()
  else:
      mode = "continued"
      code = ""
  ...

A common gotcha is to miss setting ``mode = "input"``. Be careful!


Handling multi-media outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``handle_media()`` function used above examples would look like:

.. code-block:: python

  def handle_media(record):
      media_type = record[0]  # MIME-Type string
      media_data = record[1]  # content
      ...

The exact method to process ``media_data`` depends on the ``media_type``.
Currently the following behaviors are well-defined:

* For (binary-format) images, the content is a dataURI-encoded string.
* For SVG (scalable vector graphics) images, the content is an XML string.
* For ``application/x-sorna-drawing``, the content is a JSON string that represents a
  set of vector drawing commands to be replayed the client-side (e.g., Javascript on
  browsers)


Asynchronous mode
~~~~~~~~~~~~~~~~~

The async version has all sync-version interfaces as coroutines but comes with additional
features such as ``stream_execute()`` which streams the execution results via websockets and
``stream_pty()`` for interactive terminal streaming.

.. code-block:: python

  import asyncio
  import json
  import sys
  import aiohttp
  from ai.backend.client.session import AsyncSession

  async def main():
      async with AsyncSession() as api_session:
          compute_sess = await api_session.ComputeSession.get_or_create(
              "python:3.6-ubuntu18.04",
              client_token="mysession",
          )
          code = 'print("hello world")'
          mode = "query"
          try:
              async with compute_sess.stream_execute(code, mode=mode) as stream:
                  # no need for explicit run_id since WebSocket connection represents it!
                  async for result in stream:
                      if result.type != aiohttp.WSMsgType.TEXT:
                          continue
                      result = json.loads(result.data)
                      for rec in result.get("console", []):
                          if rec[0] == "stdout":
                              print(rec[1], end="", file=sys.stdout)
                          elif rec[0] == "stderr":
                              print(rec[1], end="", file=sys.stderr)
                          else:
                              handle_media(rec)
                      sys.stdout.flush()
                      if result["status"] == "finished":
                          break
                      elif result["status"] == "waiting-input":
                          mode = "input"
                          if result["options"].get("is_password", False):
                              code = getpass.getpass()
                          else:
                              code = input()
                          await stream.send_text(code)
                      else:
                          mode = "continued"
                          code = ""
          finally:
              await compute_sess.destroy()

  if __name__ == "__main__":
      asyncio.run(main())

.. versionadded:: 19.03


Working with model service
--------------------------

Along with working AppProxy v2 deployments, model service requires a resource group configured to accept the inference workload.

Starting model service
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ai.backend.client.session import Session

    with Session() as api_session:
        compute_sess = api_session.Service.create(
            "python:3.6-ubuntu18.04",
            "Llama2-70B",
            1,
            service_name="Llama2-service",
            resources={"cuda.shares": 2, "cpu": 8, "mem": "64g"},
            open_to_public=False,
        )

If you set ``open_to_public=True``, the endpoint accepts anonymous traffic without the authentication token (see below).


Making request to model service endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ai.backend.client.session import Session

    with Session() as api_session:
        compute_sess = api_session.Service.create(...)
        service_info = compute_sess.info()
        endpoint = service_info["url"]  # this value can be None if no successful inference service deployment has been made

        token_info = compute_sess.generate_api_token("3600s")
        token = token_info["token"]
        headers = {"Authorization": f"BackendAI {token}"}  # providing token is not required for public model services
        resp = requests.get(f"{endpoint}/v1/models", headers=headers)

The token returned by the ``generate_api_token()`` method is a JSON web token (JWT), which conveys all required information to authenticate the inference request.
Once generated, it cannot be revoked.  A token may have its own expiration date/time.
The lifetime of a token is configured by the user who deploys the inference model, and currently there is no intrinsic minimum/maximum limits of the lifetime.

.. versionadded:: 23.09
