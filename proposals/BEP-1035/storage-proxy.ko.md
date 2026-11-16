# Storage-Proxy 컴포넌트

Storage-Proxy 는 vfolder 의 파일 스토리지 동작을 처리한다. 파일 업로드, 다운로드, 관리 동작을 위한 HTTP API 를 제공한다.

## 현재 상태

Storage-Proxy 는 표준화된 request_id 지원이 없다.

- request ID 용 HTTP middleware 가 없다
- 응답에 `X-Backend-Request-ID` 가 없다
- background task 에 request_id 가 없다

## 제안 변경

### HTTP middleware

request ID 처리를 위해 HTTP middleware 를 적용한다.

- Manager 에서 오는 요청(`X-Backend-Request-ID` 포함)
- client 직접 요청(새 request_id 생성)

### Background 동작

background task 에 context 바인딩 decorator 를 적용한다.

- 파일 정리 task
- 스토리지 동기화 동작
- 클론, 복사 동작

### Request 흐름

**Manager 경유:**
```
Manager                       Storage-Proxy
   │                               │
   │  POST /folders/upload         │
   │  X-Backend-Request-ID         │
   ├──────────────────────────────▶│
   │                               │
   │         extract request_id    │
   │         from header           │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID         │
   │◀──────────────────────────────┤
```

**client 직접 접근(StorageProxyClientFacingInfo 경유):**
```
Client                        Storage-Proxy
   │                               │
   │  GET /download/...            │
   │  (no X-Backend-Request-ID)    │
   ├──────────────────────────────▶│
   │                               │
   │         generate new          │
   │         request_id            │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID         │
   │◀──────────────────────────────┤
```

client 가 Storage-Proxy 에 직접 접근하면(presigned URL 등) Storage-Proxy 가 자체 request_id 를 생성한다.

## 구현 체크리스트

- [ ] main app 에 HTTP middleware 를 적용한다
- [ ] 응답에 `X-Backend-Request-ID` 를 포함한다
- [ ] background task 에 context 바인딩 decorator 를 적용한다
