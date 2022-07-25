from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class AppendEntriesRequest(_message.Message):
    __slots__ = ["entries", "leader_commit", "leader_id", "prev_log_index", "prev_log_term", "term"]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    LEADER_COMMIT_FIELD_NUMBER: _ClassVar[int]
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    PREV_LOG_INDEX_FIELD_NUMBER: _ClassVar[int]
    PREV_LOG_TERM_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[Log]
    leader_commit: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    term: int
    def __init__(
        self,
        term: _Optional[int] = ...,
        leader_id: _Optional[str] = ...,
        prev_log_index: _Optional[int] = ...,
        prev_log_term: _Optional[int] = ...,
        entries: _Optional[_Iterable[_Union[Log, _Mapping]]] = ...,
        leader_commit: _Optional[int] = ...,
    ) -> None: ...

class AppendEntriesResponse(_message.Message):
    __slots__ = ["success", "term"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    success: bool
    term: int
    def __init__(self, term: _Optional[int] = ..., success: bool = ...) -> None: ...

class CommandRequest(_message.Message):
    __slots__ = ["command", "id"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    command: str
    id: str
    def __init__(self, id: _Optional[str] = ..., command: _Optional[str] = ...) -> None: ...

class CommandResponse(_message.Message):
    __slots__ = ["redirect", "success"]
    REDIRECT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    redirect: str
    success: bool
    def __init__(self, success: bool = ..., redirect: _Optional[str] = ...) -> None: ...

class InstallSnapshotRequest(_message.Message):
    __slots__ = [
        "data",
        "done",
        "last_included_index",
        "last_included_term",
        "leader_id",
        "offset",
        "term",
    ]
    DATA_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    LAST_INCLUDED_INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_INCLUDED_TERM_FIELD_NUMBER: _ClassVar[int]
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    done: bool
    last_included_index: int
    last_included_term: int
    leader_id: str
    offset: int
    term: int
    def __init__(
        self,
        term: _Optional[int] = ...,
        leader_id: _Optional[str] = ...,
        last_included_index: _Optional[int] = ...,
        last_included_term: _Optional[int] = ...,
        offset: _Optional[int] = ...,
        data: _Optional[bytes] = ...,
        done: bool = ...,
    ) -> None: ...

class InstallSnapshotResponse(_message.Message):
    __slots__ = ["term"]
    TERM_FIELD_NUMBER: _ClassVar[int]
    term: int
    def __init__(self, term: _Optional[int] = ...) -> None: ...

class Log(_message.Message):
    __slots__ = ["command", "index", "term"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    command: str
    index: int
    term: int
    def __init__(
        self, index: _Optional[int] = ..., term: _Optional[int] = ..., command: _Optional[str] = ...
    ) -> None: ...

class RequestVoteRequest(_message.Message):
    __slots__ = ["candidate_id", "last_log_index", "last_log_term", "term"]
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_TERM_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    candidate_id: str
    last_log_index: int
    last_log_term: int
    term: int
    def __init__(
        self,
        term: _Optional[int] = ...,
        candidate_id: _Optional[str] = ...,
        last_log_index: _Optional[int] = ...,
        last_log_term: _Optional[int] = ...,
    ) -> None: ...

class RequestVoteResponse(_message.Message):
    __slots__ = ["term", "vote_granted"]
    TERM_FIELD_NUMBER: _ClassVar[int]
    VOTE_GRANTED_FIELD_NUMBER: _ClassVar[int]
    term: int
    vote_granted: bool
    def __init__(self, term: _Optional[int] = ..., vote_granted: bool = ...) -> None: ...
