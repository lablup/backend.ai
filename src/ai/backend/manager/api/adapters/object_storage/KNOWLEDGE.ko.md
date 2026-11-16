# object_storage adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 문장을 먼저 의심한다.

object storage row 는 global 에만 속하여 생성된다. 하나나 여럿을 지정해 수정하거나 영구 삭제하는 호출은 그 row 에 부여된 권한을 검사한다. 그 권한은 global 에서만 나오므로 superadmin 만 통과한다.

## 조회

단건 조회, 검색, DataLoader 어느 경로든 adapter 가 반환하는 노드는 호출자가 superadmin 일 때만 저장된 `secret_key` 를 담는다. 그 밖의 호출자는 global 목록을 읽는 monitor 를 포함해 `secret_key` 에 `*****` 를 받는다. 필드 타입은 그대로라 스키마는 바뀌지 않는다.

## 수정

## 영구 삭제

옛 이름의 삭제는 같은 영구 삭제를 호출한다.

## 여럿 수정

## 여럿 영구 삭제

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 object storage row 는 처리된 목록에, 처리하지 못한 항목은 id 와 이유를 실패 목록에 담는다.
