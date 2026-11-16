# 배포 service

## processor 구성

`backend.ai mgr ops list --concern deployment --entity deployment` 는 연결된 목록을 출력한다. 그 출력은 엔티티 유형, shape, 연산, gate, backing 을 반환한다.

## 두 배포 검색은 service 메서드를 둔다

- `global_search` 와 `scoped_search` 는 범용 action 을 그대로 쓰므로, gate 와 used-by 검사도 범용 그대로다.
- 결과 항목마다 배포의 정책이 실리는데, 정책은 별도 row 에 있다. `DeploymentSearcher` 는 배포 row 만 읽으므로 범용 검색 service 는 정책을 채울 수 없다.
- `DeploymentDBSource` 는 한 read 트랜잭션에서 페이지와 그 배포들의 정책을 읽는다.
