# Storage Proxy — 가드레일

> 컴포넌트 개요는 `src/ai/backend/storage/README.md`.

## API 핸들러

- 모든 핸들러는 타입 핸들러 클래스의 메서드여야 한다 — 모듈 레벨 async 함수 금지.
- `@api_handler` 또는 `@stream_api_handler` 데코레이터를 쓴다.
- 요청은 `PathParam[T]`, `BodyParam[T]`로 파싱한다 — raw request 객체에 직접 접근 금지.

## 예외

- 모든 예외는 `StorageProxyError`(이는 `BackendAIError` 상속)를 상속해야 한다.
- `storage/exception.py`는 legacy — 새 예외를 여기 추가하지 않는다.
- 새 예외는 `storage/errors/`에만, 기능별로 둔다: `object.py`, `quota.py`, `vfolder.py`,
  `volume.py`, `process.py`.

## 스토리지 볼륨 플러그인

- 새 스토리지 백엔드는 `storage/volumes/` 아래 플러그인으로 추가한다.
- 모든 플러그인은 추상 볼륨 인터페이스를 구현해야 한다 — 덕 타이핑 단축 금지.

## 상태 저장

- Storage는 관계형 DB를 쓰지 않는다 — 상태는 etcd·redis만 사용한다.

## 여기 속하는 것

- 파일/볼륨 연산, 쿼터 관리, vfolder 라이프사이클.
- 스토리지 관련 백그라운드 태스크(스캔, 정리, 마이그레이션).
