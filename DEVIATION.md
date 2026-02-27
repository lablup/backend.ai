# Deviation Report: BA-4731

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| server.py 수정 불가 | 대안 적용 | server.py의 `_register_newstyle_routes()`에 새 모듈의 `register_routes()` 호출을 추가함. auth 모듈과 동일한 패턴이며, 이것 없이는 새 패턴의 라우트가 등록되지 않음. 서버 부트스트랩 구조 자체는 변경하지 않았음. |
| ratelimit Handler class | 대안 적용 | ratelimit은 라우트 핸들러가 없는 middleware-only 모듈이므로 Handler class 대신 middleware 함수를 `api/rest/ratelimit/handler.py`로 이동하고, `register_routes()`는 빈 구현으로 둠. init/shutdown(Valkey client lifecycle)은 create_app() shim에 유지. |
| logs PrivateContext/GlobalTimer | 대안 적용 | logs의 PrivateContext, GlobalTimer, event dispatcher 연동은 subapp lifecycle에 묶여 있어 create_app() shim에 유지. 핸들러 로직만 새 패턴으로 마이그레이션함. |
