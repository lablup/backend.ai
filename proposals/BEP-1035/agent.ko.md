# Agent 컴포넌트

Agent 컴포넌트는 compute kernel 을 관리하고 Callosum RPC 로 Manager 와 통신한다.

## Callosum 제약

Callosum 은 Manager 와 Agent 사이 통신에 사용하는 RPC 라이브러리다.

- **별도 header 채널 없음**: HTTP 와 달리 메시지 body 와 분리된 metadata 수단이 없다
- **바이너리 프로토콜**: 메시지를 msgpack 으로 직렬화해 하나의 payload 로 보낸다

**영향**: request metadata(request_id 포함)를 메시지 body 안에 담아야 한다.

## 현재 상태

- Agent RPC 는 request_id 전파를 지원하지 않는다
- 요청, 응답에 metadata 구조가 없다

## 제안 설계

### 요청, 응답 구조

header 를 메시지 body 에 담는다.

**요청:**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "args": ["kernel-id-123"],
    "kwargs": {"timeout": 30}
}
```

**응답(성공):**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "result": {"kernel_id": "kernel-abc", "status": "running"}
}
```

**응답(에러):**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "error": {"type": "KernelNotFoundError", "message": "..."}
}
```

### Headers 모델(예시)

```python
# Pydantic model for RPC headers
class RPCHeadersModel(BaseModel):
    request_id: str | None = None
    # Extensible for future tracing
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    class Config:
        extra = "allow"
```

## 하위 호환

### 요청 형식 판별

| 요청 형식 | 판별 | 처리 |
|----------------|-----------|----------|
| `headers` 있음 | `"headers" in body` | request_id 추출 |
| `headers` 없음 | 기존 형식 | request_id 자동 생성 |

기존 Agent 는 알 수 없는 `headers` 필드를 무시한다. 새 Agent 는 이 필드를 추적에 사용한다.

## 이관 전략

1. **1단계**: Agent 가 두 형식을 모두 받는다(호환 유지)
2. **2단계**: Manager 가 새 형식을 처리할 수 있는 Agent 에게 새 형식을 보낸다
3. **3단계**: 기존 형식에 deprecation 경고를 표시한다
4. **4단계**: 기존 형식 지원을 제거한다(호환 깨짐)

## 구현 체크리스트

- [ ] Agent 에 RPC headers 모델을 추가한다
- [ ] Agent RPC dispatcher 를 새 형식에 맞게 수정한다
- [ ] 기존 형식 fallback 을 추가한다
- [ ] Manager 가 header 를 보내도록 수정한다
- [ ] capability 광고를 추가한다

## 참고

- [Callosum](https://github.com/lablup/callosum) - RPC Transport Library for asyncio
