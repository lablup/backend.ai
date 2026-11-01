# 용어집: 동작

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 쓰지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 리비전 활성화 | activate revision | deployment 의 revision 을 현재 revision 으로 바꾸는 동작입니다. | 리비전 적용, 리비전 배포 |   |
| 승인 | approve | artifact revision 을 승인하는 동작입니다. |   |   |
| 프로젝트 사용자 배정 | assign users to project | project 에 사용자를 project role 과 함께 배정하는 동작입니다. |   |   |
| batch | batch | 한 SQL 문으로 여러 행을 원자적으로 처리하는 연산 접두사입니다. |   |   |
| bulk | bulk | 여러 entity 를 한 연산으로 다루는 접두사입니다. 일부만 성공할 수 있는지는 partial_bulk, atomic_bulk 표기로 구분합니다. |   |   |
| 클론 | clone | vfolder 를 복제하는 동작입니다. | 복제 |   |
| 삭제 | delete | row 를 남기고 삭제로 표시하는 동작입니다. 영구 삭제는 purge 입니다. | soft delete, soft-delete, 소프트 삭제 |   |
| 등록 해제 | deregister | 등록된 service instance 를 등록 목록에서 빼는 동작입니다. |   |   |
| 종료 | destroy | 세션을 종료하는 operation 값입니다. |   |   |
| 대기열 추가 | enqueue session | 새 세션 을 대기열에 넣는 동작입니다. |   |   |
| 실행 | execute | 사용자 코드를 격리된 세션 에서 실행하는 user API 의 핵심 호출입니다. |   |   |
| force purge | force purge | 정리를 기다리지 않고 행을 바로 지우는 탈출구입니다. |   |   |
| 권한 부여 | grant | 사용자에게 role 을 부여하는 동작입니다. 권한 비트였던 grant:* 는 폐기됐고, entity 를 넘기는 일은 entity share 가 맡습니다. |   |   |
| 영구 삭제 | purge | 엔티티를 되살릴 수 없이 완전히 제거하는 동작입니다. | hard delete, 퍼지 |   |
| 재스캔 | rescan | 외부 레지스트리의 메타데이터를 다시 훑어 DB 를 갱신하는 동작입니다. |   |   |
| 복원 | restore | delete 를 되돌려 되살리는 동작입니다. |   |   |
| 해지 | revocation | 권한을 거두는 동작입니다. | 회수 |   |
| 해지 | revoke | 부여한 자격을 거두는 동작으로 keypair, login session, role, 공유에 씁니다. |   |   |
| 스캔 | scan | 레지스트리에서 이미지와 아티팩트를 읽어 등록하고 갱신하는 동작입니다. |   |   |
| scoped search | scoped search | 범위 식별자를 필수 인자로 받아 그 범위 안에서 검색하는 조회 방식입니다. |   |   |
| 세션 커밋 | session commit | session 의 container 상태를 새 image 로 남기는 동작입니다. | container commit, imagify, 컨테이너 커밋 |   |
| upsert | upsert | 새 행을 만들거나 기존 행을 바꾸는 쓰기 동작입니다. |   |   |
| vfolder 초대 | vfolder invitation | 다른 사용자를 vfolder 협업에 초대하는 공유 장치입니다. | 초대된 폴더, 가상 폴더 초대 |   |
| vfolder 공유 취소 | vfolder leave | 공유받은 vfolder 에서 나가는 동작입니다. | 나가기, leave |   |
