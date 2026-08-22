---
name: user-service-composition
type: decision-table
description: 사용자 처리기의 모양 선택, 키페어가 사용자의 field 행인 이유, 이메일 기반 연산이 사라진 이유
scope: src/ai/backend/manager/services/user
keywords:
  - UserProcessors
  - keypair_group
  - LookupKeypairOwnerByAccessKeyAction
  - KeypairDotfilesUpdater
  - bootstrap_script
sources:
  - src/ai/backend/manager/services/user/processors.py
  - src/ai/backend/manager/models/keypair
generated:
  by: claude-code/opus-5
  at: 2026-08-19
status: draft
---

# 사용자 서비스

사용자는 도메인 아래에 놓이므로 생성은 도메인을 scope로 하는 scope 모양이고, 이미
만들어진 사용자를 지목하는 연산은 single_entity다. 키페어는 사용자의 field 행이므로
키페어에 대한 모든 연산은 소유 사용자가 답한다.

## 이메일로 지목하던 연산이 사라졌다

수정·삭제·완전삭제가 이메일용과 id용으로 나뉘어 있었고 둘의 구현이 같았다. 이제 하나만
남고 id를 받는다. 이메일을 들고 온 호출자는 lookup으로 먼저 id를 얻는다.

## 키페어 연산의 모양

키페어 행은 자기 멤버십이 없다. 접근 키로 키페어를 지목한 요청은 key owner lookup으로
소유 사용자를 먼저 얻고, 그 뒤 연산은 사용자를 지목한다. 쓰기는 전부 UPDATE다 — 키페어
행을 더하고 지우는 것은 그 사용자에 대한 변경이다.

## dotfile과 bootstrap script는 키페어 행의 컬럼이다

`keypairs.dotfiles`와 `keypairs.bootstrap_script`이며, 판정은 도메인·프로젝트와 같은
`DotfileEntries`가 답한다.

## 서비스가 남은 연산

생성(키페어 동반 생성), 완전삭제(vfolder·세션·엔드포인트 정리), 일괄 연산 셋, 키페어
연산 전부, 월간 통계, dotfile 쓰기 셋이 서비스에 남는다. 읽기 넷(전역·도메인·프로젝트·
역할)은 ops로 직행한다.

## 역할은 사용자가 속하는 scope가 아니다

`search_users_by_role`은 scope 검색이 아니라 조건이 붙은 전역 검색이다.
