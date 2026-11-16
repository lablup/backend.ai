# session_lifecycle_handler adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 이 문서를 먼저 의심한다.

adapter 가 제공하는 호출은 목록 조회 하나다.

이 호출은 sokovan coordinator 에 등록된 session lifecycle handler 를 반환한다.

자원 그룹의 기본 세션 옵션은 handler 별 설정을 handler 이름으로 참조한다. 그 옵션을 교체하는 요청에 sokovan coordinator 에 등록되지 않은 이름이 있으면 거부된다. 이 호출은 같은 sokovan coordinator 의 handler 를 반환하므로, 여기서 받은 이름은 그 교체 요청에서 거부되지 않는다.

adapter 는 권한을 검사하지 않는다. superadmin 검사는 REST handler 의 미들웨어와 GQL resolver 가 한다. 따라서 권한이 있는 경우와 없는 경우의 짝을 이 문서에 두지 않는다.

## 목록 조회
