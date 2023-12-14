import secrets
import tempfile
import textwrap
import time
from pathlib import Path

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session

# module-level marker
pytestmark = pytest.mark.integration


def aggregate_console(c):
    return {
        "stdout": "".join(item[1] for item in c if item[0] == "stdout"),
        "stderr": "".join(item[1] for item in c if item[0] == "stderr"),
        "html": "".join(item[1] for item in c if item[0] == "html"),
        "media": list(item[1] for item in c if item[0] == "media"),
    }


def exec_loop(kernel, mode, code, opts=None, user_inputs=None):
    # The server may return continuation if kernel preparation
    # takes a little longer time (a few seconds).
    console = []
    num_queries = 0
    run_id = secrets.token_hex(8)
    if user_inputs is None:
        user_inputs = []
    while True:
        result = kernel.execute(
            run_id, code=code if num_queries == 0 or mode == "input" else "", mode=mode, opts=opts
        )
        num_queries += 1
        console.extend(result["console"])
        if result["status"] == "finished":
            break
        elif result["status"] == "waiting-input":
            mode = "input"
            code = user_inputs.pop(0)
            opts = None
        else:
            mode = "continue"
            code = ""
            opts = None
    return aggregate_console(console), num_queries


@pytest.fixture
def py3_kernel():
    with Session() as sess:
        kernel = sess.Kernel.get_or_create("python:3.6-ubuntu18.04")
        yield kernel
        kernel.destroy()


def test_hello():
    with Session() as sess:
        result = sess.Kernel.hello()
    assert "version" in result


def test_kernel_lifecycles():
    with Session() as sess:
        kernel = sess.Kernel.get_or_create("python:3.6-ubuntu18.04")
        kernel_id = kernel.kernel_id
        info = kernel.get_info()
        # the tag may be different depending on alias/metadata config.
        lang = info["lang"]
        assert lang.startswith("index.docker.io/lablup/python:")
        assert info["numQueriesExecuted"] == 1
        info = kernel.get_info()
        assert info["numQueriesExecuted"] == 2
        kernel.destroy()
        # kernel destruction is no longer synchronous!
        time.sleep(2.0)
        with pytest.raises(BackendAPIError) as e:
            info = sess.Kernel(kernel_id).get_info()
        assert e.value.status == 404


def test_kernel_execution_query_mode(py3_kernel):
    code = 'print("hello world"); x = 1 / 0'
    console, n = exec_loop(py3_kernel, "query", code, None)
    assert "hello world" in console["stdout"]
    assert "ZeroDivisionError" in console["stderr"]
    assert len(console["media"]) == 0
    info = py3_kernel.get_info()
    assert info["numQueriesExecuted"] == n + 1


def test_kernel_execution_query_mode_user_input(py3_kernel):
    name = secrets.token_hex(8)
    code = 'name = input("your name? "); print(f"hello, {name}!")'
    console, n = exec_loop(py3_kernel, "query", code, None, user_inputs=[name])
    assert "your name?" in console["stdout"]
    assert "hello, {}!".format(name) in console["stdout"]


def test_kernel_get_or_create_reuse():
    with Session() as sess:
        try:
            # Sessions with same token and same language must be reused.
            t = secrets.token_hex(6)
            kernel1 = sess.Kernel.get_or_create("python:3.6-ubuntu18.04", client_token=t)
            kernel2 = sess.Kernel.get_or_create("python:3.6-ubuntu18.04", client_token=t)
            assert kernel1.kernel_id == kernel2.kernel_id
        finally:
            kernel1.destroy()


def test_kernel_execution_batch_mode(py3_kernel):
    with tempfile.NamedTemporaryFile("w", suffix=".py", dir=Path.cwd()) as f:
        f.write('print("hello world")\nx = 1 / 0\n')
        f.flush()
        f.seek(0)
        py3_kernel.upload([f.name])
    console, _ = exec_loop(
        py3_kernel,
        "batch",
        "",
        {
            "build": "",
            "exec": "python {}".format(Path(f.name).name),
        },
    )
    assert "hello world" in console["stdout"]
    assert "ZeroDivisionError" in console["stderr"]
    assert len(console["media"]) == 0


def test_kernel_execution_batch_mode_user_input(py3_kernel):
    name = secrets.token_hex(8)
    with tempfile.NamedTemporaryFile("w", suffix=".py", dir=Path.cwd()) as f:
        f.write('name = input("your name? "); print(f"hello, {name}!")')
        f.flush()
        f.seek(0)
        py3_kernel.upload([f.name])
    console, _ = exec_loop(
        py3_kernel,
        "batch",
        "",
        {
            "build": "",
            "exec": "python {}".format(Path(f.name).name),
        },
        user_inputs=[name],
    )
    assert "your name?" in console["stdout"]
    assert "hello, {}!".format(name) in console["stdout"]


def test_kernel_execution_with_vfolder_mounts():
    with Session() as sess:
        vfname = "vftest-" + secrets.token_hex(4)
        sess.VFolder.create(vfname)
        vfolder = sess.VFolder(vfname)
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", dir=Path.cwd()) as f:
                f.write('print("hello world")\nx = 1 / 0\n')
                f.flush()
                f.seek(0)
                vfolder.upload([f.name])
            kernel = sess.Kernel.get_or_create("python:3.6-ubuntu18.04", mounts=[vfname])
            try:
                console, n = exec_loop(
                    kernel,
                    "batch",
                    "",
                    {
                        "build": "",
                        "exec": "python {}/{}".format(vfname, Path(f.name).name),
                    },
                )
                assert "hello world" in console["stdout"]
                assert "ZeroDivisionError" in console["stderr"]
                assert len(console["media"]) == 0
            finally:
                kernel.destroy()
        finally:
            vfolder.delete()


def test_kernel_restart(py3_kernel):
    num_queries = 1  # first query is done by py3_kernel fixture (creation)
    first_code = textwrap.dedent(
        """
    a = "first"
    with open("test.txt", "w") as f:
        f.write("helloo?")
    print(a)
    """
    ).strip()
    second_code_name_error = textwrap.dedent(
        """
    print(a)
    """
    ).strip()
    second_code_file_check = textwrap.dedent(
        """
    with open("test.txt", "r") as f:
        print(f.read())
    """
    ).strip()
    console, n = exec_loop(py3_kernel, "query", first_code)
    num_queries += n
    assert "first" in console["stdout"]
    assert console["stderr"] == ""
    assert len(console["media"]) == 0
    py3_kernel.restart()
    num_queries += 1
    console, n = exec_loop(py3_kernel, "query", second_code_name_error)
    num_queries += n
    assert "NameError" in console["stderr"]
    assert len(console["media"]) == 0
    console, n = exec_loop(py3_kernel, "query", second_code_file_check)
    num_queries += n
    assert "helloo?" in console["stdout"]
    assert console["stderr"] == ""
    assert len(console["media"]) == 0
    info = py3_kernel.get_info()
    # FIXME: this varies between 2~4
    assert info["numQueriesExecuted"] == num_queries


def test_admin_api(py3_kernel):
    sess = py3_kernel.session
    q = """
    query($ak: String!) {
        compute_sessions(access_key: $ak, status: "RUNNING") {
            lang
        }
    }"""
    resp = sess.Admin.query(
        q,
        {
            "ak": sess.config.access_key,
        },
    )
    assert "compute_sessions" in resp
    assert len(resp["compute_sessions"]) >= 1
    lang = resp["compute_sessions"][0]["lang"]
    assert lang.startswith("index.docker.io/lablup/python:")
