---
name: app-config-fragment-adapter-scenarios
type: reference
description: what the app config fragment adapter guarantees; one config name holds a fragment per scope (public, each domain, each user) that the app_config adapter merges by allow-list rank, and this adapter writes, reads, searches and purges those fragments one by one at their owner's scope, the public fragment written behind the superadmin role and read by anyone signed in, and the allow-list entry as the write gate
scope: src/ai/backend/manager/api/adapters/app_config_fragment
keywords: [app config fragment, scenario, adapter, upsert, scope, public, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# app_config_fragment 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`config_name` 하나에는 스코프마다 `app_config_fragment` 하나가 있다. 공개 `fragment` 하나, 도메인마다
하나, 사용자마다 하나가 같은 이름 아래 함께 있고, 설정을 읽는 `app_config` 어댑터는 그 `fragment` 행을
`app_config_allow_list` 항목의 `rank` 값 순으로 병합한 값을 반환한다. 이 어댑터는 병합 전의 `fragment`
하나하나를 쓰고 조회하고 검색하고 삭제한다. 소유자는 도메인이거나 사용자이고, 소유자가 없으면 공개
`fragment`에 해당한다. `scope_type` 필드는 소유자의 종류에서 결정되므로 따로 저장하지 않는다. 한
스코프에서 같은 이름을 다시 쓰면 그 스코프의 `fragment` 행이 바뀐다.

`allow_list` 항목이 쓰기의 전제 조건이다. 그 이름을 그 `scope_type` 값에 허용하는 항목이 있어야 쓸 수
있고, 항목이 사라지면 `fragment` 행도 함께 사라진다. 그래서 허용되지 않은 `fragment` 행이 남아 있는
상황은 생기지 않는다.

권한 검사 방식은 소유자가 있는지에 따라 다르다. 소유자가 있는 쓰기와 한 스코프 조회는 그 소유자의
스코프에 부여된 권한을 검사한다. 공개 `fragment`는 대응하는 스코프가 없어, 쓰기는 호출한 사용자가
슈퍼관리자인지 검사하고 스코프로 조회할 때는 인증만 확인한다. 하나를 id로 조회하고 삭제하는 호출은 권한 그래프를
검사하고, 여러 id를 한 번에 조회하고 삭제하는 호출은 항목마다 결과를 따로 반환한다. 전체 검색은
슈퍼관리자인지 검사한다.

쓰기 권한은 생성 권한과 수정 권한 둘 다 필요하다. 쓰기가 새 `fragment` 행을 만들 수도 있고 기존
`fragment` 행을 바꿀 수도 있으므로 한쪽만으로는 통과하지 못한다.

응답 필드는 id, `config_name`, `scope_type`, `scope_id`, `config`, 시각이다. 공개 `fragment`의 `scope_id`
필드는 비어 있다. 쓰기는 하나라도 실패하면 전부 실패한다. 쓰기는 `scoped_atomic_bulk_upsert`,
`my_atomic_bulk_upsert`이고 응답에는 쓴 노드만 있다. 옛 GQL mutation과 REST 경로는 deprecated이고
같은 쓰기에 언제나 비어 있는 `failed` 필드를 붙여 반환한다.

## 자기 `fragment` 쓰기

허용되지 않은 이름이 섞이는 시나리오는 쓰기가 하나라도 실패하면 전부 실패한다는 것을 확인한다. 허용
검사는 항목 하나마다 실행하지만, 하나가 거부되면 나머지도 롤백되어 허용된 이름의 `fragment`도 남지
않는다. 시나리오는 응답만 확인하므로 남지 않는 것은 시나리오에 적지 않는다.

등록되지 않은 이름도, `scope_type` 값이 `user`일 때 허용되지 않은 이름도 같은 이유로 거부된다. 검사는
하나이고, 그 이름을 그 `scope_type` 값에 허용하는 `allow_list` 항목이 있는지만 확인한다.

빈 항목 목록과 이름이 비어 있거나 너무 긴 요청은 시나리오로 두지 않는다. 요청 타입의 검증이 이미
거부하기 때문이다.

## 지정한 스코프에 쓰기

슈퍼관리자가 아닌 사용자가 공개 `fragment`를 쓰는 시나리오와 권한 검사를 꺼도 쓸 수 없는 시나리오는
자기 `fragment` 쓰기 절과 반대 결과를 갖는다. 공개 쓰기는 권한 그래프가 아니라 슈퍼관리자 검사로 보호되므로
스코프 권한이 있어도 통과하지 못한다.

소유자가 있는지는 권한 그래프에서 확인한다. 행은 먼저 쓰이고 그래프에 소유자가 없어 롤백되므로,
거부돼도 `fragment` 행은 남지 않는다. 이 거부는 현재 요청 오류가 아니라 서버 오류로 응답한다.
시나리오를 적기 전에 "대상을 찾을 수 없어 거부"로 바꿀 것인지 정한다.

`scope_type` 값이 `public`인데 `scope_id` 값을 지정한 요청과 `scope_type` 값이 `domain`이나 `user`인데
`scope_id` 값을 생략한 요청은 시나리오로 두지 않는다. 요청 타입의 검증이 이미 거부하기 때문이다.

## 자기 `fragment`를 이름으로 조회

이 조회는 사용자 스코프 하나만 대상으로 한다. 병합된 `config` 값이 아니라 자기가 쓴 `config` 값을
수정하기 전에 읽는 용도이므로, 도메인 `fragment`와 공개 `fragment`가 섞이지 않는 시나리오를 둔다.

## 지정한 스코프의 `fragment`를 이름으로 조회

공개 `fragment`를 누구나 조회하는 시나리오가 있는 이유는, 공개 `fragment`에는 보호할 스코프가 없기
때문이다. 그 `config` 값은 로그인 전에도 병합되어 보이는 값이므로 인증만 확인하고 응답한다. 조회 절의
공개 `fragment` 시나리오가 같은 결과를 요구한다.

존재하지 않는 도메인은 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되고 소유자가 있는지는 그 뒤에 확인하므로, 그 검사를 통과하는 슈퍼관리자만 대상을 찾을 수 없어
거부된다. 아래 절에서 존재하지 않는 소유자를 지정하는 시나리오도 같다.

## 한 스코프 검색

스코프를 둘 지정하는 시나리오는 어댑터가 막는다. 요청 타입은 여러 스코프를 받지만 이 검색은 한
스코프에서만 실행되므로, 나머지를 조용히 무시하는 대신 거부한다. 아무 스코프도 지정하지 않은 요청은
요청 타입의 검증이 거부하므로 시나리오로 두지 않는다.

## 전체 검색

슈퍼관리자가 아닌 사용자가 검색하는 시나리오의 상황에 읽기 권한을 함께 두는 이유는, 한 스코프 검색과
전체 검색의 권한 검사가 다르다는 것을 확인하기 위해서다.

필터·정렬·페이지네이션은 검색 공통 계약이라 이 어댑터의 시나리오로 검증하지 않는다.

## 조회

공개 `fragment`를 id로 조회하는 시나리오는 현재 코드에서 실패하므로 실행에서 뺐다 (BA-7933). 스코프
조회는 공개 `fragment`에 대응하는 스코프가 없어 인증만 확인하고 통과시키지만, id 조회는 그 `fragment`
자체에 부여된 권한을 검사한다. 공개 `fragment`는 어느 스코프에도 속하지 않아 그 `fragment`에 직접
부여된 역할 말고는 권한을 부여하는 역할이 없으므로, 슈퍼관리자가 아닌 누구에게나 권한 부족으로
거부된다. 공개 `fragment`는 스코프로 조회할 때와 같이 인증만 확인하고 응답해야 하고, 시나리오에는 그
기대 결과를 적어 두었다. 고쳐지면 실행에 되돌린다.

## 여러 id로 조회

없는 id도 슈퍼관리자가 아닌 사용자에게는 거부되는 항목이다. 권한 검사가 항목마다 먼저 실행되는데 없는
행에는 부여된 권한도 없기 때문이고, 그 검사를 통과하는 슈퍼관리자에게만 없는 id가 빈 항목으로 반환된다.

## 삭제

삭제는 `allow_list` 항목을 확인하지 않는다. `fragment` 행은 `allow_list` 항목이 있는 동안만 존재하므로,
있는 `fragment` 행은 언제나 자기 스코프에서 삭제할 수 있다.

`fragment`를 삭제한 뒤 병합 결과에서 그 `config` 값이 빠지고 `rank` 값이 그 아래인 스코프의 `config` 값이 대신
나타나는 것은 병합 조회 문서가 다룬다. 그 문서는 `fragment`를 처음부터 빼고 만들어 두므로, 여기서
삭제한 뒤 병합을 다시 확인하지 않는다.

이 어댑터에는 soft delete가 없다. 삭제하면 행이 사라지고 되살리는 호출도 없다.

## 여러 개 삭제

권한이 없으면 요청 전체가 거부되지 않고 그 항목만 `failed` 목록에 들어가며, 남의 `fragment`는 남는다.
없는 id와 삭제할 수 없는 id가 같은 `failed` 목록에 들어가므로 자기 `fragment`, 남의 `fragment`, 없는 id를
한 요청에 섞어 순서를 확인한다. 실패 이유는 문자열로 반환되고 문자열은 바뀌어도 되는 값이므로
시나리오가 확인하지 않는다.

빈 목록은 시나리오로 두지 않는다. 요청 타입의 검증이 이미 거부하기 때문이다.

여러 개 삭제는 `partial_bulk_purge`이고 삭제한 노드를 반환한다. 옛 REST `POST /bulk-delete`는
deprecated이고 같은 삭제의 id만 반환한다.
