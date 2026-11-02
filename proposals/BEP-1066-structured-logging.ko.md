# 컴포넌트 전반의 structured logging

## 관련 이슈

- Epic: BA-7025, Backend.AI 컴포넌트 전반의 structured logging
- JIRA: BA-7029(이 BEP)

## 동기

- log 값이 message 문자열에 삽입된다. 값으로 필터링하거나 집계할 수 없다.
  - `log.<level>()` 호출 1,996개 중 약 1,600개가 위치 인자 interpolation 을 사용하고, 값을 field 로 전달하는 호출은 0개다.
- field 를 추가하는 합의된 방법이 없다.
  - 호출 지점: `BraceStyleAdapter` kwargs 는 이름 interpolation(`"{name}"`)에 사용되고 field 가 되지 않는다. `extra=` 는 임의 dict 를 받으므로 이름이 합의되지 않는다.
  - 상위 계층: `with_log_context_fields()` 가 임의 dict 를 받는다. 사용처 3곳이 각자 이름을 지정한다.
- 목표: **log field 를 추가하는 interface 두 가지**를 정하고, **field 를 추가하는 시점과 대상**을 합의한다.

| interface | 담는 값 | 설정 위치 |
|---|---|---|
| scope field | scope 안의 모든 log line 이, 어디서 기록되든 담는 값 | 작업 단위(request, action, event, RPC, schedule 등)의 진입점 |
| 호출 지점 field | log line 하나에만 필요한 값 | log 호출 |

두 interface 의 field 는 OTel log record 의 attribute 로 나간다. 저장 backend(Loki, Elasticsearch 등)는 범위 밖이다.

## 현재 설계

| 항목 | 현재 |
|---|---|
| logger | `BraceStyleAdapter`. 571개 file. `BraceMessage` 로 지연 `str.format` |
| 호출 kwargs | 이름 interpolation 인자. `tests/unit/logging/test_adapter.py` 가 이를 계약으로 검증한다 |
| context field | `with_log_context_fields(dict)` → contextvar → adapter 의 `process()` 가 `extra` 로 병합 |
| context field 사용처 | request_id middleware, REST 인증 middleware(`user_id`), `MessageMetadata.apply_context()`, 3곳 |
| `contexts.*` | `request_id`, `user`, `triggered_user`, `client_ip` contextvar. log field 와 별도로 설정한다 |
| OTel handler | `apply_otel_loggers()` 가 `CustomJsonFormatter` 를 붙여 body 가 JSON 문자열이 되고 같은 field 가 attribute 에도 나온다 |
| OTel 범위 | handler 는 호출 시점에 존재하는 logger 에만 붙는다. 이후에 생성된 logger 의 log 는 OTel 에 도달하지 않는다(Appendix D-2 OTel 전달 손실) |
| trace 연관 | OTel SDK 가 span 안에서 나간 log 에 `trace_id`/`span_id` 를 붙인다(Appendix H-2 trace 연관) |

## 제안 설계

### 1. 호출 지점 field: logger interface

새 logger `StructuredLogger` 는 `ai.backend.logging.structured` 에 둔다. message 는 상수이고 값은 field 다.

```python
log = StructuredLogger(logging.getLogger(__spec__.name))

log.info("kernel creation started")
log.warning("image pull retried", attempt=3, delay_sec=1.5)
log.exception("kernel creation failed", kernel_id=kernel_id)
log.debug("allocation candidates: {}", candidates, resource_group_id=rg_id)   # formatting only in debug/trace
```

```python
type LogValue = str | int | float | bool | None | UUID | Enum | Path | Decimal | datetime

class StructuredLogger:
    def trace(self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def debug(self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def info(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def warning(self, msg: LiteralString, /, *, exc_info: ExcInfo = None, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def error(self, msg: LiteralString, /, *, exc_info: ExcInfo = None, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def exception(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None: ...
```

| 규칙 | 내용 |
|---|---|
| message(`info` 이상) | 상수. 형식을 사용하지 않는다. 같은 event 는 같은 message 를 가지므로 collector 에서 하나의 bucket 으로 묶인다 |
| message(`debug`, `trace`) | `{}` 형식과 위치 인자를 받는다. level 검사 뒤에만 format 한다 |
| 위치 인자 | `info` 이상은 받지 않는다. 모든 값은 keyword field 다 |
| 값 type | `LogValue` 만. `list`/`dict` 는 안 된다(혼합 type sequence 는 OTel 이 조용히 삭제한다, Appendix E 값 type) |
| 값 정규화 | `UUID`/`Path`/`Decimal` → `str`, `Enum` → `.value`, `datetime` → ISO 8601. 나머지는 그대로 |
| field 이름 접두사 | 모든 field 는 `log_tag_<name>` 로 나간다. field 이름이 `LogRecord` attribute 와 충돌하지 않으므로(Appendix H-1 `LogRecord` attribute 충돌) log 호출이 예외를 내지 않는다 |
| scope 와 충돌 | 같은 이름이면 호출 지점 값이 우선한다 |
| level 비활성 | field 를 정규화하지 않는다(`isEnabledFor` 를 먼저 본다) |

#### log level

| level | 용도 |
|---|---|
| error | server 결함. 발생한 곳에서 한 번 기록한다. 예외를 잡은 곳에서는 `exception()` 으로 기록해 traceback 을 남긴다 |
| warning | 일시적 server 측 실패, 재시도, 성능 저하 |
| info | 운영자가 알아야 하는 server 수명 주기 event(시작, 중지, 설정 적용, leader 변경) |
| debug | 주기 작업의 회차별 요약, 진행 단계 |
| trace | 사용자 요청의 결과(스케줄링 실패, 자원 소진, quota 초과, 4xx). 이력과 API 가 기록한다 |

#### guardrail: `info` 이상에서 형식 없음

| 수단 | 잡는 것 |
|---|---|
| signature | mypy 가 `info`/`warning`/`error`/`exception` 에 전달된 위치 인자를 거부한다 |
| message type | message 가 `LiteralString` 이라 mypy 가 f-string, `.format()`, `%`, `+` 로 만든 message 를 거부한다 |

ruff `G001`~`G004` 는 비활성 상태로 둔다. `StructuredLogger` signature 가 guardrail 이고, `BraceStyleAdapter` 호출 지점은 이전할 때까지 그대로 둔다.

`StructuredLogger` 는 `BraceStyleAdapter` 와 아무것도 공유하지 않는다. `BraceStyleAdapter` 와 `with_log_context_fields` 는 그대로 두고 `with_log_context` field 를 받지 않는다. 둘 다 호출 지점이 `StructuredLogger` 와 `with_log_context` 로 옮겨진 뒤 제거한다. 새 code 와 수정하는 log line 은 `StructuredLogger` 를 사용한다.

### 2. scope field: `with_log_context`

상위 계층에서 field 를 추가하는 하나의 공개 interface 는 `ai.backend.logging.structured` 의 `with_log_context` 다. `with_log_context_fields` 와 분리된 자기 contextvar 를 둔다.

```python
@contextmanager
def with_log_context(**fields: LogValue) -> Iterator[None]: ...

with with_log_context(action_id=action_id, action_name=action_name):
    ...   # every log line inside carries both fields
```

| 규칙 | 내용 |
|---|---|
| 형태 | keyword 인자만. 값 type, 정규화, field 이름 접두사는 앞에서 정한 `StructuredLogger` 규칙을 따른다 |
| 중첩 | 바깥 field 로 병합된다. 같은 이름이면 안쪽 값이 우선한다 |
| loop 안 | 여러 entity 를 순회하는 loop 는 회차마다 하나씩 연다(예: 세션 loop 의 `session_id`) |
| wrapper | 자주 사용하는 조합이나 `contexts.*` 와 함께 설정해야 하는 값은 wrapper 함수를 둔다. wrapper 는 `with_log_context` 를 호출하고 대응하는 `contexts.*` contextvar 를 같은 값으로 설정한다. wrapper 는 `ai.backend.common.contexts` 에 둔다 |
| 기존 API | dict 를 받는 `with_log_context_fields` 는 `with_log_context` 로 대체하고 `BraceStyleAdapter` 와 함께 제거한다 |

| wrapper | field | 함께 설정하는 `contexts` |
|---|---|---|
| `with_request_context` | `request_id` | `contexts.request_id` |
| `with_user_context` | `user_id`, `triggered_user_id`(다른 사용자를 대신해 작업할 때만) | `contexts.user`, `contexts.triggered_user` |

process 수명 동안 변하지 않는 값(컴포넌트 이름, node)은 scope 가 아니라 OTel Resource attribute(`service.name`, `host.name`)에 둔다. `agent_id` 는 Resource attribute 가 아니다. agent process 하나가 agent 여럿을 실행할 수 있으므로 `with_log_context` 로 추가한다.

### 3. OTel 전달 계약

| 항목 | 계약 |
|---|---|
| body | message 문자열만 |
| attributes | scope field + 호출 지점 field + SDK 자동 attribute(`code.*`, `trace_id`, `span_id`) |
| handler 분리 | 새 OTel handler 가 message type(`StructuredMessage`)으로 구분해 `StructuredLogger` record 를 보낸다. legacy handler 는 그것을 필터링해 제외하고 그 외에는 제거될 때까지 그대로 둔다 |
| formatter | 새 handler 는 formatter 가 없고 다른 handler 의 formatter 를 변경하지 않는다 |
| 범위 | 새 handler 는 logger snapshot 대신 root 와 `pkg-ns` logger(전파 경계)에 붙인다 |
| Resource | 새 handler 의 Resource 에 `host.name` 을 추가한다 |
| 명시 field 수 | line 당 최대 10개, `with_log_context` 와 호출 지점 field 를 합한 수. 자동 attribute 는 세지 않는다 |

### 4. field 이름 규칙

규칙은 `log_tag_` 접두사 앞의 이름에 적용한다.

| 종류 | 형태 | 예 |
|---|---|---|
| 식별자 | `<entity>_id` | `session_id`, `kernel_id`, `resource_group_id` |
| 이름 | `<thing>_name` | `action_name`, `task_name`, `handler_name` |
| 종류 / 상태 | `<thing>_type`, `<thing>_status` | `operation_type`, `schedule_type` |
| 개수 | `<thing>_count` | `allocation_count` |
| 기간 | `_sec`, `_ms` 접미사 | `delay_sec`, `elapsed_ms` |
| 크기 | `_bytes` 접미사 | `transferred_bytes` |
| 금지 | `id`, `name`, `entity_id` 같은 일반 이름 | — |

### 5. field 배치

#### 5.1 주입 지점과 field

| 주입 지점 | field | 방법 |
|---|---|---|
| manager REST request_id middleware, storage-proxy manager/client API, appproxy coordinator 와 worker request middleware, account-manager API middleware, webserver(신규 middleware) | `request_id` | `with_request_context` |
| manager REST 인증 middleware, `MessageMetadata.apply_context()` | `user_id`, `triggered_user_id` | `with_user_context` |
| `actions/v2/*` processor 의 `run`, 16곳(single_entity, field, scope, global_scope x3, bulk x2, field bulk x2, lookup x2, membership, relation) | `action_id`, `action_name` | `with_log_context` |
| `EventDispatcher._handle`. metadata 복원과 그 안의 예외 log 를 한 scope 로 묶는다 | `event_name`, `handler_name` | `with_log_context` |
| bgtask `_observe_bgtask`/`_execute_new_task`/`_revive_task` | `task_name`, `bgtask_id` | `with_log_context` |
| `LeaderCron._run_task`, `LocalCron._run_task`, `GlobalTimer` tick | `task_name` | `with_log_context` |
| sokovan `coordinator._process_*_schedule` | `schedule_type`, `handler_name` | `with_log_context` |
| sokovan `_process_resource_group`, provisioner `schedule_resource_group` | `resource_group_id` | `with_log_context` |
| provisioner 세션 loop, launcher `_start_single_session`, terminator `_terminate_kernel` | `session_id` | `with_log_context` |
| deployment coordinator `_run_handler`, route coordinator `process_route_lifecycle` | `lifecycle_type`, `handler_name` | `with_log_context` |
| agent `RPCFunctionRegistry`/`RPCFunctionRegistryV2`, v3 RPC routing | `rpc_method` | `with_log_context` |
| agent `create_kernels`(kernel 별), `destroy_kernel`, `restart_kernel`, `execute`, container 수명 주기 event 처리 | `session_id`, `kernel_id` | `with_log_context` |
| storage `VolumeService` method | `volume_id`, `vfolder_id` 또는 `quota_scope_id` | `with_log_context` |
| appproxy worker proxy `ensure_slot_middleware` | `circuit_id` | `with_log_context` |

요청 하나가 도달하는 가장 깊은 중첩(manager): `request_id`, `user_id`, `triggered_user_id`, `action_id`, `action_name` = 5개 field.

여러 지점에서 반복되는 field 조합은 wrapper 로 승격한다.

#### 5.2 경계를 넘는 scope 전달

| 경계 | 방법 |
|---|---|
| event 발행 → 소비 | 현재 `MessageMetadata` 를 유지한다 |
| manager → agent RPC | `MessageMetadata` 와 같은 형태를 RPC 요청에 담고 agent RPC 진입점에서 `with_request_context` 와 `with_user_context` 로 복원한다 |
| manager → storage-proxy HTTP | `X-BackendAI-RequestID` header 를 전달한다 |
| webserver → manager HTTP | `X-BackendAI-RequestID` header 를 전달한다 |
| appproxy worker → coordinator | 현재 header 전달을 유지한다 |
| `loop.run_in_executor` | contextvar 를 복사하는 공통 helper 를 거친다(162곳: agent 72, storage 52, accelerator 26, 기타 12) |
| `threading.Thread` | 2곳은 개별 처리한다 |

#### 5.3 호출 지점 field 이전 대상

scope 가 표현할 수 없는 값만 호출 지점 field 로 옮긴다. log 호출이 가장 많은 file 부터 시작한다.

| file | log 호출 |
|---|---|
| agent/agent.py | 131 |
| agent/server.py | 67 |
| kernel/base.py | 55 |
| storage/services/artifacts/reservoir.py | 41 |
| manager/sokovan/scheduler/coordinator.py | 41 |
| agent/docker/agent.py | 38 |
| appproxy/coordinator/server.py | 33 |
| storage/services/artifacts/huggingface.py | 31 |
| appproxy/worker/server.py | 28 |
| manager/sokovan/deployment/route/executor.py | 22 |

변환 예:

| 현재 | 이후 |
|---|---|
| `"Processing {} allocations, {} reservations, {} failures and {} skips in resource group {}"` | 회차별 요약이므로 `debug`: `"resource group scheduled"`, `allocation_count`, `reservation_count`, `failure_count`, `skip_count`(`resource_group_id` 는 scope 에서 온다). 세션별 스케줄링 결과(실패, skip, 우선순위를 낮춤)는 `trace` 다 |
| `"Evicted unreachable route {} after {}s"` | `"unreachable route evicted"`, `route_address`, `unreachable_sec` |

### 6. interface 검증

| 대상 | 시나리오 |
|---|---|
| `StructuredLogger` | message 가 그대로 body 로 가고 field 가 record attribute 가 된다 |
| | 값 정규화: `UUID`, `Enum`, `Path`, `Decimal`, `datetime` |
| | 모든 field 에 `log_tag_` 접두사가 붙고, `LogRecord` attribute 이름도 마찬가지이며 log line 은 남는다 |
| | 호출 지점 field 가 같은 이름의 scope field 보다 우선한다 |
| | level 이 비활성이면 field 를 정규화하지 않는다 |
| | `debug`/`trace` 는 위치 인자를 포맷하고 field 도 함께 담는다 |
| | `info` 이상은 위치 인자를 거부한다(mypy 거부, runtime `TypeError`) |
| | `exception()` 이 traceback 을 담고 `stacklevel` 이 호출자 지점을 나타낸다 |
| `with_log_context` | scope 안의 모든 log line 이 field 를 담고, scope 를 벗어나면 사라진다 |
| | 중첩 병합에서 안쪽이 우선한다 |
| | 값 정규화와 field 이름 접두사가 `StructuredLogger` 와 같다 |
| wrapper | log field 가 대응하는 `contexts.*` 값과 같다 |
| | `create_task`/`gather` 를 거쳐 전달되고, executor 에는 context 복사 helper 를 통해 전달된다 |
| `BraceStyleAdapter` | 기존 test 를 유지한다. `with_log_context` field 를 받지 않고, `StructuredLogger` 는 `with_log_context_fields` field 를 받지 않는다 |
| OTel | 새 handler: body = message, attributes = field. handler 를 붙인 뒤 생성된 logger 의 log 도 도착한다. `BraceStyleAdapter` record 는 보내지 않는다 |
| | legacy handler: `StructuredLogger` record 는 보내지 않고 `BraceStyleAdapter` record 는 이전처럼 보낸다 |

## migration / 호환

| 항목 | 영향 |
|---|---|
| 기존 호출 지점 | 변화 없음. scope field 는 그 호출 지점이 `StructuredLogger` 로 옮겨진 뒤에 log line 에 도달한다 |
| OTel body | 호출 지점이 `StructuredLogger` 로 옮겨진 line 마다 JSON 문자열에서 message 문자열로 바뀐다. body 안 field 에 의존하던 질의는 attribute 로 옮긴다. 전환 기간에는 OTel log exporter 둘이 실행된다 |
| console/file/graylog | relay 가 field 를 전달한다. console 은 message 뒤에 `name=value` 로 보여 주고, file 과 graylog record 는 `log_tag_*` 를 담는다 |
| logstash | 변화 없음. 고정 key 만 보낸다 |
| `with_log_context_fields`, `BraceStyleAdapter` | 호출 지점이 `with_log_context` 또는 wrapper 와 `StructuredLogger` 로 옮겨진 뒤 제거한다 |

## 구현 계획

| 단계 | 내용 |
|---|---|
| 1(이 BEP PR) | commit 1: BEP. commit 2: `StructuredLogger`, `LogValue` 와 정규화, field 이름 접두사, `with_log_context`, 그리고 6절 interface 검증 test |
| 2 | `AGENTS.md` logging 규칙 |
| 3 | `StructuredLogger` OTel handler 와 legacy handler 와의 record 분리(3절 OTel 전달 계약) |
| 4 | wrapper 2개, 5.1 주입 지점과 field 연결 |
| 5 | 5.2 경계를 넘는 scope 전달: RPC metadata, HTTP header, executor helper 이전 |
| 6 | 계열별 이슈가 모든 호출 지점을 `StructuredLogger` 로 옮기고, 그 뒤 `BraceStyleAdapter`, `with_log_context_fields`, legacy OTel handler 를 제거한다 |

interface 의 핵심 계약은 signature(type)이므로 BEP 와 같은 PR 에서 code 로 리뷰한다.

## 열린 질문

없다.

## 결정 기록

| 날짜 | 결정 | 근거 |
|------|----------|-----------|
| 2026-09-27 | executor helper 이전 162곳을 단계 5 이슈 하나로 묶는다 | helper 와 첫 사용처가 함께 들어오고 나머지 이전은 기계적이다 |
| 2026-09-27 | 회차별 요약은 `debug`, 세션별 스케줄링 결과는 `trace` | 이력과 API 가 사용자 요청 결과의 기록이다 |
| 2026-09-27 | `agent_id` 는 Resource attribute 가 아니라 `with_log_context` 로 추가한다 | agent process 하나가 agent 여럿을 실행할 수 있다 |
| 2026-09-27 | ruff `G001`~`G004` 는 비활성 상태로 둔다 | `StructuredLogger` signature 가 이미 차단하고, 기존 호출 지점은 이전되면서 사라진다 |
| 2026-09-27 | 새 OTel handler 를 추가하고 legacy handler 는 제거 전까지 유지한다 | 기존 log 가 그대로 OTel 에 도달하고, 모든 호출 지점이 교체되면 legacy handler 를 제거한다 |

## 참고

- code: `src/ai/backend/logging/{utils,otel,formatter}.py`, `src/ai/backend/common/contexts/`, `src/ai/backend/common/message_queue/types.py`
- test: `tests/unit/logging/test_adapter.py`
- 강제 선례: `pyproject.toml` `[tool.ruff.lint.flake8-tidy-imports.banned-api]`

---

## Appendix. 측정

Environment: opentelemetry-sdk 1.39.1, halfstack `observability` profile.

### A: OTel 이 받는 것

| 호출 | body(formatter 부착) | attributes |
|---|---|---|
| `log.info("started session {} on agent {}", sid, aid)` | `{"message": "started session sess-abc on agent agent-01", ...}` | field 없음(`code.*` 만) |
| `log.info("session started", extra={"session_id": ...})` | `{"message": "session started", "session_id": "sess-abc", ...}` | `session_id` |
| `log.info("session {sid} started", sid=...)` | `{"message": "session sess-abc started", ...}` | field 없음 |

formatter 를 제거하면 body 는 `session started` 가 되고 attributes 는 같다.

### D: 손실

```
D-1  keys sent by the relay: [levelname, levelno, lineno, msg, name, pathname, process, processName] → no fields
D-2  logger created before apply_otel → reaches OTel / created after → does not reach OTel
```

### E: 값 type

| 입력 | 결과 |
|---|---|
| `str`, `int`, `float`, `bool`, `None` | 그대로 |
| `UUID`, `Path`, `Decimal`, `set` | `str` |
| `["a", "b"]` | tuple |
| `["a", 1]` | `None`. warning 뒤에 버려진다 |
| `{"cpu": 4}` | dict |
| `StrEnum` member | Enum 객체 그대로 |

### G: contextvar 전파 경계

```
OK    await / create_task / gather / call_soon / asyncio.to_thread
LOST  loop.run_in_executor
LOST  threading.Thread
```

### H: `LogRecord` attribute 충돌, trace, overhead

H-1 `extra=` 를 깨뜨리는 `LogRecord` attribute(충돌 시 `KeyError: Attempt to overwrite '<name>' in LogRecord` 이고 log line 이 유실된다):

```
name  module  message  asctime  process  processName  thread  threadName
filename  lineno  levelname  msg  args  exc_text  created  taskName
```

H-2 span 안의 log 는 `trace_id`/`span_id` 를 자동으로 담는다.

H-3 호출당 비용(200,000회):

| 조건 | ns/call |
|---|---|
| level 비활성, field 0 / 10 | 299 / 300 |
| level 활성, field 0 / 2 / 10 | 4,622 / 4,832 / 5,673 |