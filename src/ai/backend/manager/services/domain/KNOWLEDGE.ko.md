# 도메인 서비스

도메인은 다른 모든 것이 그 아래에서 생성되는 최상위 스코프다. 위에 부모 엔티티가 없으므로 생성은 global shape 이고, 기존 도메인을 지정하는 연산은 single entity 다.

## processor 구성

`backend.ai mgr ops list --concern organization --entity domain` 는 연결 및 호출 경로로 처리되는 목록을 출력한다. 그 출력은 엔티티 유형, shape, 연산, gate, backing 을 반환한다.

도메인의 dotfile 은 도메인이 own 하는 auto-generated file 이다. 이 service 가 아니라
auto-generated file action 이 처리하며, `services/user/KNOWLEDGE.md` 가 설명한다.
