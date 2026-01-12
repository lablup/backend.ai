import json
import pickle

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.common.json import dump_json_str
from ai.backend.common.utils import odict
from ai.backend.manager.errors.kernel import BackendAgentError


class TestError(BackendAIError):
    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode.default()


def test_backend_error_obj():
    eobj = TestError()
    assert eobj.args == (eobj.status_code, eobj.reason, eobj.error_type)
    assert json.loads(eobj.body) == json.loads(
        json.dumps(
            odict(
                ("error_code", str(ErrorCode.default())),
                ("type", eobj.error_type),
                ("title", eobj.error_title),
            )
        ).encode()
    )

    extra_msg = "!@#$"
    eobj = TestError(extra_msg)
    assert extra_msg in str(eobj)
    assert extra_msg in repr(eobj)


def test_backend_error_obj_pickle():
    eobj = TestError()
    encoded = pickle.dumps(eobj)
    decoded = pickle.loads(encoded)
    assert eobj.status_code == decoded.status_code
    assert eobj.error_type == decoded.error_type
    assert eobj.error_title == decoded.error_title
    assert eobj.content_type == decoded.content_type
    assert eobj.extra_msg == decoded.extra_msg


def test_backend_agent_error_obj():
    eobj = BackendAgentError("timeout")

    assert eobj.args == (eobj.status_code, eobj.reason, eobj.error_type, eobj.agent_error_type)
    assert (
        eobj.body
        == dump_json_str(
            odict(
                ("type", eobj.error_type),
                ("title", eobj.error_title),
                (
                    "agent-details",
                    odict(
                        ("type", eobj.agent_error_type),
                        ("title", eobj.agent_error_title),
                    ),
                ),
            )
        ).encode()
    )


def test_backend_agent_error_obj_pickle():
    eobj = BackendAgentError("timeout")
    encoded = pickle.dumps(eobj)
    decoded = pickle.loads(encoded)
    assert eobj.body == decoded.body
    assert eobj.agent_details == decoded.agent_details
