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

TODO: Retrieving the app proxy address to a container application

.. code-block:: python

    from ai.backend.client.session import Session

    with Session() as api_session:
        my_session = api_session.ComputeSession.get_or_create(...)
        print(...)


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
