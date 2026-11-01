# 모델 카드 service: 배경

> 규칙: `../AGENTS.md`. Spec 선택: `../../models/specs/KNOWLEDGE.md`.

모델 카드는 프로젝트 안에서 vfolder 에 담긴 모델을 지정한다. 모델과 함께 실행할 때 필요한
최소 자원도 담으므로, 이 패키지는 테이블 두 개를 다룬다.

## processor 구성

`backend.ai mgr ops list --concern deployment --entity model_card` 는 연결 및 호출 경로로 처리되는 목록을
출력한다. 그 출력이 엔티티 타입, 모양, 연산, gate, backing 을 나타낸다.
