# 엔티티 공유 service

엔티티 공유는 공유하는 쪽의 엔티티를 사람이나 프로젝트에 빌려주고, 받는 쪽이 이를 수락, 거절, 반납한다. 이 패키지는 각 답을 검사하는 스코프를 정한다.

## processor 구성

`backend.ai mgr ops list --concern rbac --entity entity_share` 는 연결된 목록을 출력한다. 그 출력은 엔티티 유형, shape, 연산, gate, backing 을 반환한다.

## 답은 그 공유에 답하는 스코프에서 검사한다

- `accept`, `reject`, `leave` 는 `answering_scope` 를 스코프로 하는 scope shape 이다. 호출자는 그 스코프나 그 스코프를 관할하는 스코프에서 `entity_share` 의 `update` 권한(`leave` 는 `soft_delete`)을 받아 있어야 한다.
- `answering_scope` 는 공유가 수신자로 지정한 노드, 즉 프로젝트나 사용자다.
- 이메일로 보낸 공유는 답하기 전까지 노드가 없으므로, 그 이메일을 가진 사용자가 답한다.
- write guard 는 같은 문장 안에서 공유의 수신자와 `answering_scope` 를 맞춰 보므로, 공유가 지정하지 않은 스코프로는 아무것도 처리되지 않는다.

## 답하는 스코프는 lookup 으로 먼저 찾고, 찾으려면 그 스코프를 읽을 수 있어야 한다

- `lookup_answering_scope` 는 공유를 id 로 읽고 공유가 지정한 스코프를 반환한다. row 를 읽기 전에는 답이 자기 스코프를 정할 수 없다.
- 아직 스코프를 지정하지 않은 공유는 주소로 그 이메일을 가진 사용자를 찾으며, 이메일로 한 번 더 읽는다.
- `group.lookup` 으로 연결하므로 호출자는 찾은 스코프(자기 자신이나 프로젝트)를 읽을 수 있어야 한다. 읽을 수 없는 호출자는 없는 공유와 같은 응답을 받는다.
- 뒤따르는 답은 같은 스코프에서 `update`(`leave` 는 `soft_delete`)로 검사한다.
