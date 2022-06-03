import os
import socket
import sys

input_host = '127.0.0.1'
input_port = 65000

batch_enabled = int(os.environ.get('_BACKEND_BATCH_MODE', '0'))
if batch_enabled:
    # Since latest Python 2 has `builtins`and `input`,
    # we cannot detect Python 2 with the existence of them.
    if sys.version_info.major > 2:
        import builtins

        def _input(prompt=''):
            sys.stdout.write(prompt)
            sys.stdout.flush()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect((input_host, input_port))
                    userdata = sock.recv(1024)
                except ConnectionRefusedError:
                    userdata = b'<user-input-unavailable>'
            return userdata.decode()
        builtins._input = input  # type: ignore
        builtins.input = _input
    else:
        # __builtins__ is an alias dict for __builtin__ in modules other than __main__.
        # Thus, we have to explicitly import __builtin__ module in Python 2.
        import __builtin__
        builtins = __builtin__

        def _raw_input(prompt=''):
            sys.stdout.write(prompt)
            sys.stdout.flush()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((input_host, input_port))
                userdata = sock.recv(1024)
            except socket.error:
                userdata = b'<user-input-unavailable>'
            finally:
                sock.close()
            return userdata.decode()
        builtins._raw_input = builtins.raw_input  # type: ignore
        builtins.raw_input = _raw_input           # type: ignore
