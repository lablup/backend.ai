---
name: vfolder-adapter-scenarios
type: reference
description: what the vfolder adapter guarantees: ownership, which scopes can reach a folder, and how bulk operations report results
scope: src/ai/backend/manager/api/adapters/vfolder
keywords: [vfolder, scenario, adapter, rbac, ownership]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 폴더 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

개인 폴더는 만든 사람의 스코프에 생긴다. 그래서 폴더를 만들 권한은 그 사용자 자신에게
걸린다. 폴더가 놓일 스토리지 호스트는 도메인과 키페어 정책이 함께 허용해야 한다.

## 만들기

## 조회

## 누구의 폴더에 닿는가

폴더는 프로젝트 아래에 있다. 개인 폴더는 그 사람의 개인 프로젝트에, 프로젝트 폴더는 그
프로젝트에 있다. 공유는 다른 스코프가 폴더를 제한을 두고 빌려 받는 것이다. 폴더에 닿는지는
폴더를 가진 스코프에 역할이 폴더 읽기를 허용하는지로 정해진다.

## 여러 폴더를 한 번에 읽기

다른 엔티티가 가리키는 폴더들을 id 목록으로 한 번에 읽는다. 답은 id마다 한 자리씩 입력 순서대로
오고, 호출 전체가 거부되지는 않는다. 자리마다 한 폴더 읽기와 같은 기준으로 따로 판정한다.

슈퍼관리자가 아닌 사용자에게는 없는 id도 권한 부족으로 거부된다. 폴더가 없다는 사실은 권한 없는
사용자에게 드러나지 않는다. 빈 값은 슈퍼관리자만 본다.

## 수정

수정은 이름, 복제 가능 여부, 기본 마운트 권한을 바꾼다. 이름은 폴더를 가진 스코프 안에서 겹치지
않아야 한다.

## 여럿 수정, soft delete, restore

여럿 연산은 호출 전체를 거부하지 않는다. 폴더마다 한 폴더 연산과 같은 기준으로 따로 판정해,
처리한 폴더는 처리된 목록에, 처리하지 못한 것은 id 와 이유를 실패 목록에 싣는다. soft delete 와
restore 는 같은 권한을 본다. 여럿 purge 는 이 형태가 아니다.
