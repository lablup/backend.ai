Examples
========

Synchronous-mode execution
--------------------------

Query mode
~~~~~~~~~~

This is the minimal code to execute a code snippet with this client SDK.

.. code-block:: python3

  import sys
  from ai.backend.client.session import Session

  with Session() as session:
      kern = session.ComputeSession.get_or_create('cr.backend.ai/multiarch/python:3.9-ubuntu20.04')
      code = 'print("hello world")'
      mode = 'query'
      run_id = None
      while True:
          result = kern.execute(run_id, code, mode=mode)
          run_id = result['runId']  # keeps track of this particular run loop
          for rec in result.get('console', []):
              if rec[0] == 'stdout':
                  print(rec[1], end='', file=sys.stdout)
              elif rec[0] == 'stderr':
                  print(rec[1], end='', file=sys.stderr)
              else:
                  handle_media(rec)
          sys.stdout.flush()
          if result['status'] == 'finished':
              break
          else:
              mode = 'continue'
              code = ''
      kern.destroy()

You need to take care of ``client_token`` because it determines whether to
reuse kernel sessions or not.
Backend.AI cloud has a timeout so that it terminates long-idle kernel sessions,
but within the timeout, any kernel creation requests with the same ``client_token``
let Backend.AI cloud to reuse the kernel.


Batch mode
~~~~~~~~~~

You first need to upload the files after creating the session and construct a
``opts`` struct.

.. code-block:: python3

  import sys
  from ai.backend.client.session import Session

  with Session() as session:
      kern = session.ComputeSession.get_or_create('cr.backend.ai/multiarch/python:3.9-ubuntu20.04')
      kern.upload(['mycode.py', 'setup.py'])
      code = ''
      mode = 'batch'
      run_id = None
      opts = {
          'build': '*',  # calls "python setup.py install"
          'exec': 'python mycode.py arg1 arg2',
      }
      while True:
          result = kern.execute(run_id, code, mode=mode, opts=opts)
          opts.clear()
          run_id = result['runId']
          for rec in result.get('console', []):
              if rec[0] == 'stdout':
                  print(rec[1], end='', file=sys.stdout)
              elif rec[0] == 'stderr':
                  print(rec[1], end='', file=sys.stderr)
              else:
                  handle_media(rec)
          sys.stdout.flush()
          if result['status'] == 'finished':
              break
          else:
              mode = 'continue'
              code = ''
      kern.destroy()


Handling user inputs
~~~~~~~~~~~~~~~~~~~~

Inside the while-loop for ``kern.execute()`` above,
change the if-block for ``result['status']`` as follows:

.. code:: python3

  ...
  if result['status'] == 'finished':
      break
  elif result['status'] == 'waiting-input':
      mode = 'input'
      if result['options'].get('is_password', False):
          code = getpass.getpass()
      else:
          code = input()
  else:
      mode = 'continue'
      code = ''
  ...

A common gotcha is to miss setting ``mode = 'input'``. Be careful!


Handling multi-media outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``handle_media()`` function used above examples would look like:

.. code-block:: python3

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


Asynchronous-mode Execution
---------------------------

The async version has all sync-version interfaces as coroutines but comes with additional
features such as ``stream_execute()`` which streams the execution results via websockets and
``stream_pty()`` for interactive terminal streaming.

.. code-block:: python3

  import asyncio
  import getpass
  import json
  import sys
  import aiohttp
  from ai.backend.client.session import AsyncSession

  async def main():
      async with AsyncSession() as session:
          kern = await session.ComputeSession.get_or_create('cr.backend.ai/multiarch/python:3.9-ubuntu20.04')
          code = 'print("hello world")'
          mode = 'query'
          async with kern.stream_execute(code, mode=mode) as stream:
              # no need for explicit run_id since WebSocket connection represents it!
              async for result in stream:
                  if result.type != aiohttp.WSMsgType.TEXT:
                      continue
                  result = json.loads(result.data)
                  for rec in result.get('console', []):
                      if rec[0] == 'stdout':
                          print(rec[1], end='', file=sys.stdout)
                      elif rec[0] == 'stderr':
                          print(rec[1], end='', file=sys.stderr)
                      else:
                          handle_media(rec)
                  sys.stdout.flush()
                  if result['status'] == 'finished':
                      break
                  elif result['status'] == 'waiting-input':
                      mode = 'input'
                      if result['options'].get('is_password', False):
                          code = getpass.getpass()
                      else:
                          code = input()
                      await stream.send_text(code)
                  else:
                      mode = 'continue'
                      code = ''
          await kern.destroy()

  loop = asyncio.new_event_loop()
  try:
      loop.run_until_complete(main())
  finally:
      loop.stop()

.. versionadded:: 1.5
