## deployment

[배경](/src/ai/backend/manager/api/adapters/deployment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/deployment/adapter.py)

시나리오: 미완성 33 / 47

- ops 구성 (22)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_replicas: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - admin_search_revisions: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_access_tokens_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_auto_scaling_rules_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_policies_by_endpoint_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_policies_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_replicas_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_revisions_by_ids: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_routes_by_ids: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - get_access_token: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - get_replica: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - get_revision: 대표 성공 ✓ · 대표 거부 ✓
  - project_search: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - search_access_tokens: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_policies: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_replicas: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_revisions: 대표 성공 ✓ · 대표 거부 ✓
  - search_routes: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
  - search_rules: 대표 성공 ✗ · 대표 거부 ✗: SCENARIO-GAP
- ops + 직접 구현 (1)
  - get_current_revision: 성공 없음 · 거부 있음 1 (get_ops, single_entity): SCENARIO-GAP
- 직접 구현 (24)
  - activate_revision: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - add_revision: 성공 있음 4 · 거부 있음 7 (single_entity)
  - admin_refresh_deployment_revisions: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - bulk_delete_access_tokens: 성공 없음 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - bulk_delete_rules: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - create: 성공 있음 3 · 거부 있음 2 (scope)
  - create_access_token: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - create_rule: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - delete: 성공 있음 2 · 거부 있음 2 (single_entity)
  - get: 성공 있음 2 · 거부 있음 3 (single_entity)
  - get_policy: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - get_rule: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - partial_bulk_purge_access_tokens: 성공 있음 2 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_purge_rules: 성공 있음 3 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_update_rules: 성공 있음 2 · 거부 없음 (partial_bulk_field): SCENARIO-GAP
  - purge_access_token: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - purge_rule: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - replace_options: 성공 있음 4 · 거부 있음 3 (single_entity)
  - search_revision_resource_slots: 성공 있음 1 · 거부 있음 1 (single_field)
  - sync_replicas: 성공 있음 1 · 거부 있음 1 (single_entity)
  - update: 성공 있음 5 · 거부 있음 2 (single_entity)
  - update_route_traffic: 성공 없음 · 거부 없음 (single_field): SCENARIO-GAP
  - update_rule: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - upsert_policy: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [배포 셋이 있고 superadmin 이 필터 없이 전체를 조회하면, 셋을 모두 셉니다](#searching-the-superadmin-counts-every-deployment) | 성공 |
| [배포 읽기 권한을 받았지만 superadmin 이 아닌 사용자가 전체를 조회하면, 역할로 거부됩니다. 이 동작은 권한 그래프가 아니라 역할이 검사합니다](#searching-a-user-granted-read-may-not-search-every-deployment) | 거부 |

**admin_search_revisions**

| 시나리오 | 판정 |
|---|---|
| [두 프로젝트의 배포에 리비전이 나뉘어 있고 superadmin 이 필터 없이 전체를 조회하면, 둘의 것을 모두 셉니다. 이 동작은 역할이 검사합니다](#searching_revisions-the-superadmin-counts-every-revision) | 성공 |
| [모든 배포에 읽기 권한을 받았지만 superadmin 이 아닌 사용자가 전체 리비전을 조회하면, 역할로 거부됩니다](#searching_revisions-a-user-granted-read-may-not-search-every-revision) | 거부 |

**batch_load_revisions_by_ids**

| 시나리오 | 판정 |
|---|---|
| [한 프로젝트에서만 배포 읽기 권한을 받은 사용자가 읽을 수 있는 리비전, 다른 프로젝트의 리비전, 아무것도 갖지 않은 id 를 한 번에 조회하면, 지정한 순서대로 리비전, 거부, 빈 항목이 옵니다](#reading_revisions-loading-revisions-by-id-answers-each-id-on-its-own) | 성공 |

**get_revision**

| 시나리오 | 판정 |
|---|---|
| [배포 읽기 권한을 받은 사용자가 그 배포의 리비전을 id 로 조회하면, 그 리비전이 옵니다](#reading_revisions-a-user-granted-read-reads-a-revision-by-id) | 성공 |
| [superadmin 이 아무것도 갖지 않은 id 로 리비전을 조회하면, 대상이 없다는 것으로 거부됩니다. 모든 검사를 지나가는 사람에게는 감출 것이 없습니다](#reading_revisions-a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |
| [배포 읽기 권한을 받은 사용자가 아무것도 갖지 않은 id 로 리비전을 조회하면, 볼 수 없는 id 와 같은 이유로 거부됩니다](#reading_revisions-a-revision-id-nothing-answers-to-is-refused-as-unresolvable) | 거부 |
| [아무 배포 권한도 받지 않은 사용자가 리비전을 id 로 조회하면, 키를 풀 수 없다는 이유로 거부됩니다](#reading_revisions-a-user-granted-nothing-may-not-read-a-revision) | 거부 |

**project_search**

| 시나리오 | 판정 |
|---|---|
| [두 프로젝트에 배포가 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그 프로젝트를 조회하면, 그 프로젝트의 것만 나옵니다](#searching-searching-a-project-finds-only-its-own-deployments) | 성공 |
| [그 프로젝트에 읽기 권한이 없는 사용자가 프로젝트를 조회하면, 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-a-project) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [같은 프로젝트에 두 사람이 각자 배포를 생성했고 자기 스코프에서 읽기 권한을 받은 사람이 자기 것을 조회하면, 자기가 생성한 것만 나옵니다](#searching-searching-my-own-finds-only-what-i-made) | 성공 |
| [자기 스코프에서 읽기 권한을 받지 않은 사람이 자기 것을 조회하면, 권한 부족으로 거부됩니다. 이 동작도 범위를 좁히기만 하지 않고 권한이 검사합니다](#searching-a-user-granted-nothing-may-not-search-even-their-own) | 거부 |

**search_revisions**

| 시나리오 | 판정 |
|---|---|
| [리비전 셋이 딸린 배포에 읽기 권한을 받은 사용자가 그 배포의 리비전을 조회하면, 셋을 모두 셉니다](#searching_revisions-a-user-granted-read-counts-every-revision-of-a-deployment) | 성공 |
| [두 프로젝트의 배포에 리비전이 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그쪽 배포의 리비전을 조회하면, 그쪽 것만 나옵니다](#searching_revisions-another-deployments-revisions-stay-out-of-a-deployment-search) | 성공 |
| [리비전 셋이 딸린 배포의 리비전을 번호 필터로 조회하면, 그 번호의 것만 남습니다](#searching_revisions-filtering-revisions-by-number-leaves-only-that-one) | 성공 |
| [아무 배포 권한도 받지 않은 사용자가 배포의 리비전을 조회하면, 권한 부족으로 거부됩니다](#searching_revisions-a-user-granted-nothing-may-not-search-a-deployments-revisions) | 거부 |

**get_current_revision**

| 시나리오 | 판정 |
|---|---|
| [리비전이 딸리지 않은 배포의 현재 리비전을 조회하면, 현재 리비전이 없다는 이유로 거부됩니다](#reading-a-deployment-holding-no-revision-answers-nothing-as-its-current-one) | 거부 |

**add_revision**

| 시나리오 | 판정 |
|---|---|
| [프리셋도 필수 슬롯도 없이 자원과 클러스터를 빼고 리비전을 추가하면, 노드 하나에 크기 1이고 자원 슬롯이 빈 리비전이 옵니다](#adding_revisions-a-revision-added-without-resources-runs-on-one-node-with-no-slot) | 성공 |
| [리비전 없는 배포에 생성 권한을 받은 사용자가 모든 설정을 주고 리비전을 추가하면, 번호 1을 단 리비전이 준 설정 그대로 옵니다](#adding_revisions-a-user-granted-create-adds-the-first-revision) | 성공 |
| [리비전 하나가 딸린 배포에 리비전을 추가하면, 번호 2를 단 리비전이 옵니다](#adding_revisions-the-next-revision-is-numbered-one-past-the-last) | 성공 |
| [배포에도 자기 모델 vfolder 에도 권한을 받지 않은 superadmin 이 남의 배포에 리비전을 추가하면, 리비전이 추가됩니다. 역할이 배포 권한과 vfolder 권한을 함께 지나갑니다](#adding_revisions-the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant) | 성공 |
| [배포 생성 권한은 받았지만 모델 vfolder 를 읽을 권한이 없는 사용자가 그 vfolder 로 리비전을 추가하면, vfolder 를 찾을 수 없다는 이유로 거부됩니다](#adding_revisions-a-model-folder-the-caller-may-not-read-is-not-found) | 거부 |
| [남의 모델 vfolder 를 읽기 전용으로 빌린 사용자가 읽고 쓰기로 마운트하는 리비전을 추가하면, vfolder 권한을 넘는다는 이유로 거부됩니다](#adding_revisions-a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused) | 거부 |
| [모든 리비전이 채워야 하는 슬롯이 정해져 있고 그 슬롯을 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다](#adding_revisions-a-revision-missing-a-required-slot-is-refused) | 거부 |
| [프리셋 없이 이미지를 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다](#adding_revisions-a-revision-with-no-image-from-any-layer-is-refused) | 거부 |
| [vfolder 파일을 읽지 않는 인퍼런스 런타임 종류로 프리셋 없이 모델 정의를 빼고 리비전을 추가하면, 이름 없는 모델이 모델 정의 검증에서 거부됩니다](#adding_revisions-a-revision-with-no-model-definition-from-any-layer-is-refused) | 거부 |
| [프리셋 없이 인퍼런스 런타임 종류를 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다](#adding_revisions-a-revision-with-no-runtime-variant-from-any-layer-is-refused) | 거부 |
| [배포 읽기 권한만 받은 사용자가 리비전을 추가하면, 권한 부족으로 거부됩니다](#adding_revisions-a-user-granted-only-read-may-not-add-a-revision) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [이름을 지정하지 않고 배포를 생성하면, 생성한 사용자에게서 이름이 정해집니다](#creating-a-deployment-made-without-a-name-is-named-after-its-maker) | 성공 |
| [프로젝트에서 배포 생성 권한을 받은 사용자가 배포를 생성하면, 그 프로젝트에 속하고 요청한 사용자가 소유하는 배포가 리비전 없이 생성됩니다](#creating-a-user-granted-create-in-a-project-makes-a-deployment-there) | 성공 |
| [엔티티 권한 집행을 비활성화하면 아무 권한도 받지 않은 사용자도 배포를 생성합니다. 이 동작은 역할이 아니라 권한 그래프가 검사합니다](#creating-turning-enforcement-off-lets-a-user-create-a-deployment) | 성공 |
| [생성 권한을 받은 프로젝트가 아닌 다른 프로젝트에 배포를 생성하면, 권한 부족으로 거부됩니다](#creating-a-create-grant-in-another-project-does-not-reach-this-one) | 거부 |
| [아무 배포 권한도 받지 않은 사용자가 배포를 생성하면, 권한 부족으로 거부됩니다](#creating-a-user-granted-nothing-may-not-create-a-deployment) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [soft-delete 권한을 받은 사용자가 배포를 삭제하면, 그 배포의 삭제를 시작했다고 응답합니다](#retiring-a-user-granted-soft-delete-retires-a-deployment) | 성공 |
| [다른 사람이 생성한 배포를 아무 권한도 받지 않은 superadmin 이 삭제하면, 그 배포의 삭제를 시작했다고 응답합니다. 역할이 권한 그래프를 지나갑니다](#retiring-the-superadmin-retires-anothers-deployment-without-a-grant) | 성공 |
| [수정 권한만 받고 soft-delete 권한은 받지 않은 사용자가 배포를 삭제하면, 권한 부족으로 거부됩니다. 삭제는 수정과 다른 동작입니다](#retiring-a-user-granted-only-update-may-not-retire-a-deployment) | 거부 |
| [superadmin 이 아무것도 갖지 않은 id 를 삭제하면, 대상이 없다는 것으로 거부됩니다](#retiring-retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [배포 하나가 있고 읽기 권한을 받은 사용자가 id 로 조회하면, 그 배포가 응답으로 옵니다](#reading-a-user-granted-read-reads-a-deployment-by-id) | 성공 |
| [다른 사람이 생성한 배포를 아무 권한도 받지 않은 superadmin 이 id 로 조회하면, 그 배포가 응답으로 옵니다. 역할이 권한 그래프를 지나갑니다](#reading-the-superadmin-reads-anothers-deployment-without-a-grant) | 성공 |
| [같은 배포가 있고 아무 권한도 받지 않은 사용자가 조회하면, 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-a-deployment) | 거부 |
| [superadmin 이 아무것도 갖지 않은 id 로 조회하면, 대상이 없다는 것으로 거부됩니다. 권한 검사를 지나가는 사람만 이 응답을 봅니다](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |
| [읽기 권한을 받은 사용자가 아무것도 갖지 않은 id 로 조회하면, 대상이 없다는 것이 아니라 권한 부족으로 거부됩니다. 없는 row 에는 걸린 권한도 없기 때문입니다](#reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user) | 거부 |

**partial_bulk_purge_access_tokens**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 배포 토큰 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_access_tokens-a-user-granted-nothing-purges-none-of-several-tokens) | 성공 |
| [배포 영구 삭제 권한을 받은 사용자가 배포 토큰 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_access_tokens-purging-several-tokens-answers-for-the-missing-one) | 성공 |

**partial_bulk_purge_rules**

| 시나리오 | 판정 |
|---|---|
| [배포 수정 권한만 받은 사용자가 오토스케일링 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_auto_scaling_rules-a-deployment-editor-purges-none-of-several-rules) | 성공 |
| [아무 권한도 받지 않은 사용자가 오토스케일링 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_auto_scaling_rules-a-user-granted-nothing-purges-none-of-several-rules) | 성공 |
| [배포 영구 삭제 권한을 받은 사용자가 오토스케일링 규칙 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_auto_scaling_rules-purging-several-rules-answers-for-the-missing-one) | 성공 |

**partial_bulk_update_rules**

| 시나리오 | 판정 |
|---|---|
| [배포 수정 권한을 받은 사용자가 오토스케일링 규칙 여럿의 지표 이름을 한 번에 변경하면, 모두 새 이름으로 오고 실패한 것은 없습니다](#partial_bulk_auto_scaling_rules-a-deployment-editor-edits-several-rules-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 오토스케일링 규칙 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_auto_scaling_rules-a-user-granted-nothing-edits-none-of-several-rules) | 성공 |

**replace_options**

| 시나리오 | 판정 |
|---|---|
| [수정 권한을 받은 사용자가 기본값과 처리기별 설정을 담아 옵션을 교체하면, 준 것이 전부 새 옵션이 되고 응답은 그 옵션만 싣습니다](#options-a-user-granted-update-replaces-the-options-whole) | 성공 |
| [선택 정책을 STRICT 로 담아 옵션을 교체하면, 새 옵션의 선택 정책도 STRICT 입니다](#options-replacing-with-a-strict-policy-keeps-it-strict) | 성공 |
| [상속한 처리기별 설정이 있는 배포에 기본값만 담아 옵션을 교체하면, 상속한 설정이 하나도 남지 않습니다](#options-replacing-with-no-handler-entry-drops-the-inherited-ones) | 성공 |
| [선택 정책이 STRICT 인 배포에서 선택 정책을 빼고 옵션을 교체하면, 선택 정책은 STRICT 로 남습니다](#options-replacing-without-a-policy-keeps-the-stored-one) | 성공 |
| [읽기 권한만 받은 사용자가 옵션을 교체하면, 권한 부족으로 거부됩니다](#options-a-user-granted-only-read-may-not-replace-the-options) | 거부 |
| [같은 처리기 이름을 두 번 담아 옵션을 교체하면, 입력이 틀렸다는 이유로 거부됩니다](#options-naming-a-handler-twice-is-refused) | 거부 |
| [등록되지 않은 처리기 이름을 담아 옵션을 교체하면, 입력이 틀렸다는 이유로 거부됩니다](#options-naming-an-unregistered-handler-is-refused) | 거부 |

**search_revision_resource_slots**

| 시나리오 | 판정 |
|---|---|
| [슬롯 둘을 할당한 리비전이 딸린 배포에 읽기 권한을 받은 사용자가 그 리비전의 슬롯을 조회하면, 둘을 모두 셉니다](#searching_revisions-a-user-granted-read-counts-every-slot-a-revision-allocates) | 성공 |
| [아무 배포 권한도 받지 않은 사용자가 배포의 리비전의 슬롯을 조회하면, 리비전을 찾을 수 없다는 응답으로 거부됩니다](#searching_revisions-a-user-granted-nothing-may-not-search-a-revisions-slots) | 거부 |

**sync_replicas**

| 시나리오 | 판정 |
|---|---|
| [수정 권한을 받은 사용자가 복제 맞추기를 요청하면, 맞추기를 시작했다고 응답합니다](#syncing-a-user-granted-update-starts-syncing-the-replicas) | 성공 |
| [읽기 권한만 받은 사용자가 복제 맞추기를 요청하면, 권한 부족으로 거부됩니다](#syncing-a-user-granted-only-read-may-not-sync-the-replicas) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [공개가 아닌 배포를 수정 권한을 받은 사용자가 공개로 변경하면, 공개로 변경된 상태가 옵니다](#editing-a-user-granted-update-opens-a-deployment-to-the-public) | 성공 |
| [수정 권한을 받은 사용자가 복제 수를 올리면, 두려는 복제 수가 새 값이 됩니다](#editing-a-user-granted-update-raises-the-replica-count) | 성공 |
| [수정 권한을 받은 사용자가 이름을 변경하면, 이름만 새 값이 되고 나머지는 그대로입니다](#editing-a-user-granted-update-renames-a-deployment) | 성공 |
| [태그가 붙은 배포의 태그를 비우면, 태그가 하나도 남지 않습니다](#editing-clearing-the-tags-of-a-deployment-leaves-none) | 성공 |
| [다른 사람이 생성한 배포의 이름을 아무 권한도 받지 않은 superadmin 이 변경하면, 이름만 새 값이 됩니다. 역할이 권한 그래프를 지나갑니다](#editing-the-superadmin-renames-anothers-deployment-without-a-grant) | 성공 |
| [읽기 권한만 받은 사용자가 배포를 수정하면, 권한 부족으로 거부됩니다](#editing-a-user-granted-only-read-may-not-update-a-deployment) | 거부 |
| [superadmin 이 아무것도 갖지 않은 id 를 수정하면, 대상이 없다는 것으로 거부됩니다](#editing-updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

### admin_search

<a id="searching-the-superadmin-counts-every-deployment"></a>

#### [the-superadmin-counts-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

배포 셋이 있고 superadmin 이 필터 없이 전체를 조회하면, 셋을 모두 셉니다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 배포가 모두, 그리고 그것만 셉니다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-read-may-not-search-every-deployment"></a>

#### [a-user-granted-read-may-not-search-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

배포 읽기 권한을 받았지만 superadmin 이 아닌 사용자가 전체를 조회하면, 역할로 거부됩니다. 이 동작은 권한 그래프가 아니라 역할이 검사합니다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_revisions

<a id="searching_revisions-the-superadmin-counts-every-revision"></a>

#### [the-superadmin-counts-every-revision](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

두 프로젝트의 배포에 리비전이 나뉘어 있고 superadmin 이 필터 없이 전체를 조회하면, 둘의 것을 모두 셉니다. 이 동작은 역할이 검사합니다

Given

- 두 프로젝트의 배포에 리비전 2개와 1개가 나뉘어 있고, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 other-1
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 elsewhere-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - superadmin user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 wanted-1: 리비전 하나를 갖는다
  - 배포 wanted-1: 리비전 하나를 갖는다
  - 배포 elsewhere-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.admin_search_revisions: user-1 이 필터 없이 모든 리비전을 조회합니다

Then

- 미리 저장한 리비전이 모두, 그리고 그것만 세어집니다
  - items.id: 센 리비전들와 같다
  - items.revision_number = [1, 1, 2]
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-read-may-not-search-every-revision"></a>

#### [a-user-granted-read-may-not-search-every-revision](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

모든 배포에 읽기 권한을 받았지만 superadmin 이 아닌 사용자가 전체 리비전을 조회하면, 역할로 거부됩니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.admin_search_revisions: user-1 이 필터 없이 모든 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_revisions_by_ids

<a id="reading_revisions-loading-revisions-by-id-answers-each-id-on-its-own"></a>

#### [loading-revisions-by-id-answers-each-id-on-its-own](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

한 프로젝트에서만 배포 읽기 권한을 받은 사용자가 읽을 수 있는 리비전, 다른 프로젝트의 리비전, 아무것도 갖지 않은 id 를 한 번에 조회하면, 지정한 순서대로 리비전, 거부, 빈 항목이 옵니다

Given

- 두 프로젝트의 배포에 리비전 1개와 1개가 나뉘어 있고, 한쪽 프로젝트에서만 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 프로젝트 other-1
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 elsewhere-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 wanted-1: 리비전 하나를 갖는다
  - 배포 elsewhere-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.batch_load_revisions_by_ids: user-1 이 wanted-1의 리비전, 다른 프로젝트 배포의 리비전, 아무것도 갖지 않은 id 를 차례로 지정해 한 번에 조회합니다

Then

- 지정한 순서대로 리비전, 거부, 빈 자리가 옵니다
  - len = 3
  - [0].id: 미리 저장한 리비전와 같다
  - [0].deployment_id: 미리 저장한 배포와 같다
  - [0].revision_number = 1
  - [0].image_id: 미리 저장한 이미지와 같다
  - [0].cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - [0].resource_config.resource_group_name = 'resource-group-1'
  - [0].resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - [0].resource_config.resource_opts = None
  - [0].model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - [0].model_runtime_config.inference_runtime_config = None
  - [0].model_runtime_config.environ = None
  - [0].model_runtime_config.runtime_variant_preset_values = []
  - [0].model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - [0].model_mount_config.mount_destination = '/models'
  - [0].model_mount_config.definition_path = ''
  - [0].model_mount_config.subpath = None
  - [0].model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - [0].created_at: 이 실행이 쓴 시각
  - [0].extra_mounts = []
  - [0].revision_preset_id = None
  - [1] = 'NotEnoughPermission'
  - [2] = None

### get_revision

<a id="reading_revisions-a-user-granted-read-reads-a-revision-by-id"></a>

#### [a-user-granted-read-reads-a-revision-by-id](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

배포 읽기 권한을 받은 사용자가 그 배포의 리비전을 id 로 조회하면, 그 리비전이 옵니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.get_revision: user-1 이 deployment-1의 첫 리비전 id 로 리비전을 조회합니다

Then

- 리비전 전체가 옵니다
  - id: 미리 저장한 리비전와 같다
  - deployment_id: 미리 저장한 배포와 같다
  - revision_number = 1
  - image_id: 미리 저장한 이미지와 같다
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: 이 실행이 쓴 시각
  - extra_mounts = []
  - revision_preset_id = None

<a id="reading_revisions-a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

superadmin 이 아무것도 갖지 않은 id 로 리비전을 조회하면, 대상이 없다는 것으로 거부됩니다. 모든 검사를 지나가는 사람에게는 감출 것이 없습니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - superadmin user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.get_revision: user-1 이 아무것도 갖지 않은 id 로 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: FieldNotFoundError

<a id="reading_revisions-a-revision-id-nothing-answers-to-is-refused-as-unresolvable"></a>

#### [a-revision-id-nothing-answers-to-is-refused-as-unresolvable](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

배포 읽기 권한을 받은 사용자가 아무것도 갖지 않은 id 로 리비전을 조회하면, 볼 수 없는 id 와 같은 이유로 거부됩니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.get_revision: user-1 이 아무것도 갖지 않은 id 로 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="reading_revisions-a-user-granted-nothing-may-not-read-a-revision"></a>

#### [a-user-granted-nothing-may-not-read-a-revision](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

아무 배포 권한도 받지 않은 사용자가 리비전을 id 로 조회하면, 키를 풀 수 없다는 이유로 거부됩니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.get_revision: user-1 이 deployment-1의 첫 리비전 id 로 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### project_search

<a id="searching-searching-a-project-finds-only-its-own-deployments"></a>

#### [searching-a-project-finds-only-its-own-deployments](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

두 프로젝트에 배포가 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그 프로젝트를 조회하면, 그 프로젝트의 것만 나옵니다

Given

- 두 프로젝트에 나뉜 배포들과, 한쪽 프로젝트에서만 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 프로젝트 other-1
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 beside-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 elsewhere-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.project_search: user-1 이 team-1 안을 조회합니다

Then

- 미리 저장한 배포가 모두, 그리고 그것만 셉니다
  - items = ['beside-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-a-project"></a>

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

그 프로젝트에 읽기 권한이 없는 사용자가 프로젝트를 조회하면, 권한 부족으로 거부됩니다

Given

- 같은 프로젝트의 배포 3개와, 그 프로젝트의 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 other-2: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.project_search: user-1 이 team-1 안을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-searching-my-own-finds-only-what-i-made"></a>

#### [searching-my-own-finds-only-what-i-made](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

같은 프로젝트에 두 사람이 각자 배포를 생성했고 자기 스코프에서 읽기 권한을 받은 사람이 자기 것을 조회하면, 자기가 생성한 것만 나옵니다

Given

- 두 사람이 각자 만든 배포와, 자기 스코프에서 배포 읽기 권한을 받은 그중 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 자기 스코프에서 배포를 읽을 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-owner-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-owner-1 보유
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 mine-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.scoped_search: user-1 이 자기 것을 조회합니다

Then

- 미리 저장한 배포가 모두, 그리고 그것만 셉니다
  - items = ['mine-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-even-their-own"></a>

#### [a-user-granted-nothing-may-not-search-even-their-own](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

자기 스코프에서 읽기 권한을 받지 않은 사람이 자기 것을 조회하면, 권한 부족으로 거부됩니다. 이 동작도 범위를 좁히기만 하지 않고 권한이 검사합니다

Given

- 두 사람이 각자 만든 배포와, 아무 배포 권한도 받지 않은 그중 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 mine-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.scoped_search: user-1 이 자기 것을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_revisions

<a id="searching_revisions-a-user-granted-read-counts-every-revision-of-a-deployment"></a>

#### [a-user-granted-read-counts-every-revision-of-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

리비전 셋이 딸린 배포에 읽기 권한을 받은 사용자가 그 배포의 리비전을 조회하면, 셋을 모두 셉니다

Given

- 리비전 3개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다
  - 배포 deployment-1: 리비전 하나를 갖는다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revisions: user-1 이 deployment-1의 리비전을 조회합니다

Then

- 미리 저장한 리비전이 모두, 그리고 그것만 세어집니다
  - items.id: 센 리비전들와 같다
  - items.revision_number = [1, 2, 3]
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-another-deployments-revisions-stay-out-of-a-deployment-search"></a>

#### [another-deployments-revisions-stay-out-of-a-deployment-search](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

두 프로젝트의 배포에 리비전이 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 그쪽 배포의 리비전을 조회하면, 그쪽 것만 나옵니다

Given

- 두 프로젝트의 배포에 리비전 2개와 1개가 나뉘어 있고, 한쪽 프로젝트에서만 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 프로젝트 other-1
  - 배포 wanted-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 elsewhere-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 wanted-1: 리비전 하나를 갖는다
  - 배포 wanted-1: 리비전 하나를 갖는다
  - 배포 elsewhere-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revisions: user-1 이 wanted-1의 리비전을 조회합니다

Then

- 미리 저장한 리비전이 모두, 그리고 그것만 세어집니다
  - items.id: 센 리비전들와 같다
  - items.revision_number = [1, 2]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-filtering-revisions-by-number-leaves-only-that-one"></a>

#### [filtering-revisions-by-number-leaves-only-that-one](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

리비전 셋이 딸린 배포의 리비전을 번호 필터로 조회하면, 그 번호의 것만 남습니다

Given

- 리비전 3개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다
  - 배포 deployment-1: 리비전 하나를 갖는다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revisions: user-1 이 deployment-1의 리비전을 번호 2 필터로 조회합니다

Then

- 미리 저장한 리비전이 모두, 그리고 그것만 세어집니다
  - items.id: 센 리비전들와 같다
  - items.revision_number = [2]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-nothing-may-not-search-a-deployments-revisions"></a>

#### [a-user-granted-nothing-may-not-search-a-deployments-revisions](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

아무 배포 권한도 받지 않은 사용자가 배포의 리비전을 조회하면, 권한 부족으로 거부됩니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revisions: user-1 이 deployment-1의 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_current_revision

<a id="reading-a-deployment-holding-no-revision-answers-nothing-as-its-current-one"></a>

#### [a-deployment-holding-no-revision-answers-nothing-as-its-current-one](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

리비전이 딸리지 않은 배포의 현재 리비전을 조회하면, 현재 리비전이 없다는 이유로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get_current_revision: user-1 이 deployment-1의 현재 리비전을 조회합니다

Then

- 거부됩니다
  - 거부: DeploymentRevisionNotFound

### add_revision

<a id="adding_revisions-a-revision-added-without-resources-runs-on-one-node-with-no-slot"></a>

#### [a-revision-added-without-resources-runs-on-one-node-with-no-slot](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

프리셋도 필수 슬롯도 없이 자원과 클러스터를 빼고 리비전을 추가하면, 노드 하나에 크기 1이고 자원 슬롯이 빈 리비전이 옵니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다 (자원과 클러스터 없이)

Then

- 리비전 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - deployment_id: 미리 저장한 배포와 같다
  - revision_number = 1
  - image_id: 미리 저장한 이미지와 같다
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = []
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: 이 실행이 쓴 시각
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-a-user-granted-create-adds-the-first-revision"></a>

#### [a-user-granted-create-adds-the-first-revision](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

리비전 없는 배포에 생성 권한을 받은 사용자가 모든 설정을 주고 리비전을 추가하면, 번호 1을 단 리비전이 준 설정 그대로 옵니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 리비전 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - deployment_id: 미리 저장한 배포와 같다
  - revision_number = 1
  - image_id: 미리 저장한 이미지와 같다
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: 이 실행이 쓴 시각
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-the-next-revision-is-numbered-one-past-the-last"></a>

#### [the-next-revision-is-numbered-one-past-the-last](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

리비전 하나가 딸린 배포에 리비전을 추가하면, 번호 2를 단 리비전이 옵니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 리비전 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - deployment_id: 미리 저장한 배포와 같다
  - revision_number = 2
  - image_id: 미리 저장한 이미지와 같다
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: 이 실행이 쓴 시각
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

배포에도 자기 모델 vfolder 에도 권한을 받지 않은 superadmin 이 남의 배포에 리비전을 추가하면, 리비전이 추가됩니다. 역할이 배포 권한과 vfolder 권한을 함께 지나갑니다

Given

- 다른 사람이 만든 배포 하나와, 배포에도 자기 모델 vfolder 에도 권한을 받지 않은 superadmin
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 theirs-1에 리비전을 추가합니다

Then

- 리비전 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - deployment_id: 미리 저장한 배포와 같다
  - revision_number = 1
  - image_id: 미리 저장한 이미지와 같다
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: 미리 저장한 인퍼런스 런타임 종류와 같다
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: 미리 저장한 모델 vfolder 와 같다
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: 이 실행이 쓴 시각
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-a-model-folder-the-caller-may-not-read-is-not-found"></a>

#### [a-model-folder-the-caller-may-not-read-is-not-found](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

배포 생성 권한은 받았지만 모델 vfolder 를 읽을 권한이 없는 사용자가 그 vfolder 로 리비전을 추가하면, vfolder 를 찾을 수 없다는 이유로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 권한이 없는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 거부됩니다
  - 거부: VFolderNotFound

<a id="adding_revisions-a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused"></a>

#### [a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

남의 모델 vfolder 를 읽기 전용으로 빌린 사용자가 읽고 쓰기로 마운트하는 리비전을 추가하면, vfolder 권한을 넘는다는 이유로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 남의 모델 폴더를 읽기 전용으로 빌린 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다, 남에게는 ro 로 마운트됩니다
    - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
    - vfolder 공유 제안 share-1: 받는 사람이 받아들임
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 거부됩니다
  - 거부: VFolderPermissionError

<a id="adding_revisions-a-revision-missing-a-required-slot-is-refused"></a>

#### [a-revision-missing-a-required-slot-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

모든 리비전이 채워야 하는 슬롯이 정해져 있고 그 슬롯을 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 모든 리비전이 반드시 채워야 합니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="adding_revisions-a-revision-with-no-image-from-any-layer-is-refused"></a>

#### [a-revision-with-no-image-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

프리셋 없이 이미지를 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다 (이미지 없이)

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="adding_revisions-a-revision-with-no-model-definition-from-any-layer-is-refused"></a>

#### [a-revision-with-no-model-definition-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

vfolder 파일을 읽지 않는 인퍼런스 런타임 종류로 프리셋 없이 모델 정의를 빼고 리비전을 추가하면, 이름 없는 모델이 모델 정의 검증에서 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다 (모델 정의 없이)

Then

- 거부됩니다
  - 거부: BackendAISchemaValidationFailed

<a id="adding_revisions-a-revision-with-no-runtime-variant-from-any-layer-is-refused"></a>

#### [a-revision-with-no-runtime-variant-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

프리셋 없이 인퍼런스 런타임 종류를 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다 (인퍼런스 런타임 종류 없이)

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="adding_revisions-a-user-granted-only-read-may-not-add-a-revision"></a>

#### [a-user-granted-only-read-may-not-add-a-revision](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

배포 읽기 권한만 받은 사용자가 리비전을 추가하면, 권한 부족으로 거부됩니다

Given

- 리비전 0개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다

When

- DeploymentAdapter.add_revision: user-1 이 deployment-1에 리비전을 추가합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create

<a id="creating-a-deployment-made-without-a-name-is-named-after-its-maker"></a>

#### [a-deployment-made-without-a-name-is-named-after-its-maker](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

이름을 지정하지 않고 배포를 생성하면, 생성한 사용자에게서 이름이 정해집니다

Given

- 배포를 놓을 수 있는 프로젝트와, 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create: user-1 이 team-1에 이름 없이 배포를 생성합니다

Then

- 만든 배포 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name: 만든 사람에게서 지어진 이름
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-a-user-granted-create-in-a-project-makes-a-deployment-there"></a>

#### [a-user-granted-create-in-a-project-makes-a-deployment-there](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

프로젝트에서 배포 생성 권한을 받은 사용자가 배포를 생성하면, 그 프로젝트에 속하고 요청한 사용자가 소유하는 배포가 리비전 없이 생성됩니다

Given

- 배포를 놓을 수 있는 프로젝트와, 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create: user-1 이 team-1에 serving 배포를 생성합니다

Then

- 만든 배포 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 2
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-turning-enforcement-off-lets-a-user-create-a-deployment"></a>

#### [turning-enforcement-off-lets-a-user-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

엔티티 권한 집행을 비활성화하면 아무 권한도 받지 않은 사용자도 배포를 생성합니다. 이 동작은 역할이 아니라 권한 그래프가 검사합니다

Given

- 배포를 놓을 수 있는 프로젝트와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentAdapter.create: user-1 이 team-1에 serving 배포를 생성합니다

Then

- 만든 배포 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 만든 사람와 같다
  - options: 리소스 그룹의 기본값와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-a-create-grant-in-another-project-does-not-reach-this-one"></a>

#### [a-create-grant-in-another-project-does-not-reach-this-one](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

생성 권한을 받은 프로젝트가 아닌 다른 프로젝트에 배포를 생성하면, 권한 부족으로 거부됩니다

Given

- 배포를 놓을 프로젝트와, 다른 프로젝트에서 배포에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 프로젝트 other-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유

When

- DeploymentAdapter.create: user-1 이 team-1에 serving 배포를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="creating-a-user-granted-nothing-may-not-create-a-deployment"></a>

#### [a-user-granted-nothing-may-not-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

아무 배포 권한도 받지 않은 사용자가 배포를 생성하면, 권한 부족으로 거부됩니다

Given

- 배포를 놓을 수 있는 프로젝트와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- DeploymentAdapter.create: user-1 이 team-1에 serving 배포를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### delete

<a id="retiring-a-user-granted-soft-delete-retires-a-deployment"></a>

#### [a-user-granted-soft-delete-retires-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

soft-delete 권한을 받은 사용자가 배포를 삭제하면, 그 배포의 삭제를 시작했다고 응답합니다

Given

- 이미 있는 배포 하나와, 배포에 SOFT_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 SOFT_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete: user-1 이 deployment-1를 삭제합니다

Then

- 삭제를 시작한 배포를 담아 응답합니다
  - id: 미리 저장한 배포와 같다

<a id="retiring-the-superadmin-retires-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-retires-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

다른 사람이 생성한 배포를 아무 권한도 받지 않은 superadmin 이 삭제하면, 그 배포의 삭제를 시작했다고 응답합니다. 역할이 권한 그래프를 지나갑니다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete: user-1 이 theirs-1를 삭제합니다

Then

- 삭제를 시작한 배포를 담아 응답합니다
  - id: 미리 저장한 배포와 같다

<a id="retiring-a-user-granted-only-update-may-not-retire-a-deployment"></a>

#### [a-user-granted-only-update-may-not-retire-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

수정 권한만 받고 soft-delete 권한은 받지 않은 사용자가 배포를 삭제하면, 권한 부족으로 거부됩니다. 삭제는 수정과 다른 동작입니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete: user-1 이 deployment-1를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

superadmin 이 아무것도 갖지 않은 id 를 삭제하면, 대상이 없다는 것으로 거부됩니다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.delete: user-1 이 아무것도 갖지 않은 id 를 삭제합니다

Then

- 거부됩니다
  - 거부: EndpointNotFound

### get

<a id="reading-a-user-granted-read-reads-a-deployment-by-id"></a>

#### [a-user-granted-read-reads-a-deployment-by-id](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

배포 하나가 있고 읽기 권한을 받은 사용자가 id 로 조회하면, 그 배포가 응답으로 옵니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get: user-1 이 deployment-1 로 조회합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="reading-the-superadmin-reads-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-reads-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

다른 사람이 생성한 배포를 아무 권한도 받지 않은 superadmin 이 id 로 조회하면, 그 배포가 응답으로 옵니다. 역할이 권한 그래프를 지나갑니다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get: user-1 이 theirs-1 로 조회합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'theirs-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="reading-a-user-granted-nothing-may-not-read-a-deployment"></a>

#### [a-user-granted-nothing-may-not-read-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

같은 배포가 있고 아무 권한도 받지 않은 사용자가 조회하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get: user-1 이 deployment-1 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

superadmin 이 아무것도 갖지 않은 id 로 조회하면, 대상이 없다는 것으로 거부됩니다. 권한 검사를 지나가는 사람만 이 응답을 봅니다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get: user-1 이 아무것도 갖지 않은 id 로 조회합니다

Then

- 거부됩니다
  - 거부: EndpointNotFound

<a id="reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"></a>

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

읽기 권한을 받은 사용자가 아무것도 갖지 않은 id 로 조회하면, 대상이 없다는 것이 아니라 권한 부족으로 거부됩니다. 없는 row 에는 걸린 권한도 없기 때문입니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.get: user-1 이 아무것도 갖지 않은 id 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_purge_access_tokens

<a id="partial_bulk_access_tokens-a-user-granted-nothing-purges-none-of-several-tokens"></a>

#### [a-user-granted-nothing-purges-none-of-several-tokens](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_access_tokens.py): pass

아무 권한도 받지 않은 사용자가 배포 토큰 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 접근 토큰 2개가 걸린 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 배포 토큰 하나를 갖는다
  - 배포 deployment-1: 배포 토큰 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_purge_access_tokens: user-1 이 배포 토큰 2개를 한 번에 purge 합니다

Then

- 처리된 토큰 없이 토큰이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 토큰의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 토큰의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_access_tokens-purging-several-tokens-answers-for-the-missing-one"></a>

#### [purging-several-tokens-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_access_tokens.py): pass

배포 영구 삭제 권한을 받은 사용자가 배포 토큰 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 접근 토큰 2개가 걸린 배포 하나와, 배포에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 배포 토큰 하나를 갖는다
  - 배포 deployment-1: 배포 토큰 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_purge_access_tokens: user-1 이 배포 토큰 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 토큰이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 토큰의 id 와 같다
  - successes[1].id: 미리 저장한 토큰의 id 와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_purge_rules

<a id="partial_bulk_auto_scaling_rules-a-deployment-editor-purges-none-of-several-rules"></a>

#### [a-deployment-editor-purges-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

배포 수정 권한만 받은 사용자가 오토스케일링 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자동 스케일링 규칙 2개가 걸린 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 이 오토스케일링 규칙 2개를 한 번에 purge 합니다

Then

- 처리된 규칙 없이 규칙이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 규칙의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 규칙의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_auto_scaling_rules-a-user-granted-nothing-purges-none-of-several-rules"></a>

#### [a-user-granted-nothing-purges-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

아무 권한도 받지 않은 사용자가 오토스케일링 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자동 스케일링 규칙 2개가 걸린 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 이 오토스케일링 규칙 2개를 한 번에 purge 합니다

Then

- 처리된 규칙 없이 규칙이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 규칙의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 규칙의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_auto_scaling_rules-purging-several-rules-answers-for-the-missing-one"></a>

#### [purging-several-rules-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

배포 영구 삭제 권한을 받은 사용자가 오토스케일링 규칙 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 자동 스케일링 규칙 2개가 걸린 배포 하나와, 배포에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 이 오토스케일링 규칙 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 규칙이 모두 지표 이름 'cpu_util'으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 규칙의 id 와 같다
  - successes[0].metric_name = 'cpu_util'
  - successes[1].id: 미리 저장한 규칙의 id 와 같다
  - successes[1].metric_name = 'cpu_util'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update_rules

<a id="partial_bulk_auto_scaling_rules-a-deployment-editor-edits-several-rules-at-once"></a>

#### [a-deployment-editor-edits-several-rules-at-once](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

배포 수정 권한을 받은 사용자가 오토스케일링 규칙 여럿의 지표 이름을 한 번에 변경하면, 모두 새 이름으로 오고 실패한 것은 없습니다

Given

- 자동 스케일링 규칙 2개가 걸린 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_update_rules: user-1 이 오토스케일링 규칙 2개의 지표 이름을 한 번에 수정합니다

Then

- 규칙이 모두 지표 이름 'memory_util'으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 규칙의 id 와 같다
  - successes[0].metric_name = 'memory_util'
  - successes[1].id: 미리 저장한 규칙의 id 와 같다
  - successes[1].metric_name = 'memory_util'
  - failed = []

<a id="partial_bulk_auto_scaling_rules-a-user-granted-nothing-edits-none-of-several-rules"></a>

#### [a-user-granted-nothing-edits-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

아무 권한도 받지 않은 사용자가 오토스케일링 규칙 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자동 스케일링 규칙 2개가 걸린 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다
  - 배포 deployment-1: 오토스케일링 규칙 하나를 갖는다

When

- DeploymentAdapter.partial_bulk_update_rules: user-1 이 오토스케일링 규칙 2개의 지표 이름을 한 번에 수정합니다

Then

- 처리된 규칙 없이 규칙이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 미리 저장한 규칙의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 미리 저장한 규칙의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

### replace_options

<a id="options-a-user-granted-update-replaces-the-options-whole"></a>

#### [a-user-granted-update-replaces-the-options-whole](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

수정 권한을 받은 사용자가 기본값과 처리기별 설정을 담아 옵션을 교체하면, 준 것이 전부 새 옵션이 되고 응답은 그 옵션만 싣습니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments 을 담아 교체합니다

Then

- 교체한 옵션만 옵니다
  - deployment_id: 미리 저장한 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = [('check-replica-deployments', None, 1)]
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

<a id="options-replacing-with-a-strict-policy-keeps-it-strict"></a>

#### [replacing-with-a-strict-policy-keeps-it-strict](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

선택 정책을 STRICT 로 담아 옵션을 교체하면, 새 옵션의 선택 정책도 STRICT 입니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 선택 정책 strict 와 기본값만 담아 교체합니다

Then

- 교체한 옵션만 옵니다
  - deployment_id: 미리 저장한 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-replacing-with-no-handler-entry-drops-the-inherited-ones"></a>

#### [replacing-with-no-handler-entry-drops-the-inherited-ones](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

상속한 처리기별 설정이 있는 배포에 기본값만 담아 옵션을 교체하면, 상속한 설정이 하나도 남지 않습니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 기본값만 담아 교체합니다

Then

- 교체한 옵션만 옵니다
  - deployment_id: 미리 저장한 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

<a id="options-replacing-without-a-policy-keeps-the-stored-one"></a>

#### [replacing-without-a-policy-keeps-the-stored-one](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

선택 정책이 STRICT 인 배포에서 선택 정책을 빼고 옵션을 교체하면, 선택 정책은 STRICT 로 남습니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다, 선택 정책은 strict 입니다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 기본값만 담아 교체합니다

Then

- 교체한 옵션만 옵니다
  - deployment_id: 미리 저장한 배포와 같다
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-a-user-granted-only-read-may-not-replace-the-options"></a>

#### [a-user-granted-only-read-may-not-replace-the-options](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

읽기 권한만 받은 사용자가 옵션을 교체하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments 을 담아 교체합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="options-naming-a-handler-twice-is-refused"></a>

#### [naming-a-handler-twice-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

같은 처리기 이름을 두 번 담아 옵션을 교체하면, 입력이 틀렸다는 이유로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 처리기별 설정 check-replica-deployments, check-replica-deployments 을 담아 교체합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

<a id="options-naming-an-unregistered-handler-is-refused"></a>

#### [naming-an-unregistered-handler-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

등록되지 않은 처리기 이름을 담아 옵션을 교체하면, 입력이 틀렸다는 이유로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.replace_options: user-1 이 deployment-1의 옵션을 처리기별 설정 no-such-handler 을 담아 교체합니다

Then

- 거부됩니다
  - 거부: InvalidAPIParameters

### search_revision_resource_slots

<a id="searching_revisions-a-user-granted-read-counts-every-slot-a-revision-allocates"></a>

#### [a-user-granted-read-counts-every-slot-a-revision-allocates](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

슬롯 둘을 할당한 리비전이 딸린 배포에 읽기 권한을 받은 사용자가 그 리비전의 슬롯을 조회하면, 둘을 모두 셉니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revision_resource_slots: user-1 이 deployment-1의 첫 리비전의 슬롯을 조회합니다

Then

- 리비전이 잡은 슬롯이 모두 세어집니다
  - items = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-nothing-may-not-search-a-revisions-slots"></a>

#### [a-user-granted-nothing-may-not-search-a-revisions-slots](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

아무 배포 권한도 받지 않은 사용자가 배포의 리비전의 슬롯을 조회하면, 리비전을 찾을 수 없다는 응답으로 거부됩니다

Given

- 리비전 1개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수 있는 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다
  - 리비전이 딛는 이미지, 모델 vfolder, 인퍼런스 런타임 종류, 자원 슬롯 유형 준비
    - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
    - 이미지 image-1: x86_64 이미지
    - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
    - vfolder 읽기 권한 부여
      - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
      - 역할 folder-reader-1: vfolder 전체에 READ 허용
      - 일반 사용자 user-1: 역할 folder-reader-1 보유
    - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
    - 자원 슬롯 유형 cpu: 리비전이 채우지 않아도 됩니다
    - 자원 슬롯 유형 mem: 리비전이 채우지 않아도 됩니다
  - 배포 deployment-1: 리비전 하나를 갖는다

When

- DeploymentAdapter.search_revision_resource_slots: user-1 이 deployment-1의 첫 리비전의 슬롯을 조회합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### sync_replicas

<a id="syncing-a-user-granted-update-starts-syncing-the-replicas"></a>

#### [a-user-granted-update-starts-syncing-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py): pass

수정 권한을 받은 사용자가 복제 맞추기를 요청하면, 맞추기를 시작했다고 응답합니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 2개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.sync_replicas: user-1 이 deployment-1의 복제 맞추기를 요청합니다

Then

- 복제 맞추기를 시작했다고 응답합니다
  - success = True

<a id="syncing-a-user-granted-only-read-may-not-sync-the-replicas"></a>

#### [a-user-granted-only-read-may-not-sync-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py): pass

읽기 권한만 받은 사용자가 복제 맞추기를 요청하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.sync_replicas: user-1 이 deployment-1의 복제 맞추기를 요청합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-opens-a-deployment-to-the-public"></a>

#### [a-user-granted-update-opens-a-deployment-to-the-public](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

공개가 아닌 배포를 수정 권한을 받은 사용자가 공개로 변경하면, 공개로 변경된 상태가 옵니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 deployment-1를 바깥에 열도록 수정합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = True
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-update-raises-the-replica-count"></a>

#### [a-user-granted-update-raises-the-replica-count](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

수정 권한을 받은 사용자가 복제 수를 올리면, 두려는 복제 수가 새 값이 됩니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 deployment-1를 복제 수를 3으로 수정합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 3
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-update-renames-a-deployment"></a>

#### [a-user-granted-update-renames-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

수정 권한을 받은 사용자가 이름을 변경하면, 이름만 새 값이 되고 나머지는 그대로입니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 deployment-1를 이름을 renamed 으로 수정합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-clearing-the-tags-of-a-deployment-leaves-none"></a>

#### [clearing-the-tags-of-a-deployment-leaves-none](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

태그가 붙은 배포의 태그를 비우면, 태그가 하나도 남지 않습니다

Given

- 이미 있는 배포 하나와, 배포에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 UPDATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다, keep 태그가 붙어 있다

When

- DeploymentAdapter.update: user-1 이 deployment-1를 태그를 비우도록 수정합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-the-superadmin-renames-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-renames-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

다른 사람이 생성한 배포의 이름을 아무 권한도 받지 않은 superadmin 이 변경하면, 이름만 새 값이 됩니다. 역할이 권한 그래프를 지나갑니다

Given

- 다른 사람이 만든 배포 하나와, 아무 배포 권한도 받지 않은 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 theirs-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 theirs-1를 이름을 renamed 으로 수정합니다

Then

- 미리 저장한 배포 전체가 옵니다
  - id: 미리 저장한 배포와 같다
  - metadata.project_id: 미리 저장한 프로젝트와 같다
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: 이 실행이 쓴 시각
  - metadata.updated_at: 이 실행이 쓴 시각
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: 미리 저장한 배포를 가진 사람와 같다
  - options: 미리 저장한 배포의 옵션와 같다
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-only-read-may-not-update-a-deployment"></a>

#### [a-user-granted-only-read-may-not-update-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

읽기 권한만 받은 사용자가 배포를 수정하면, 권한 부족으로 거부됩니다

Given

- 이미 있는 배포 하나와, 배포에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 deployment-user-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 deployment-user-1: deployment 전체에 READ 허용
    - 일반 사용자 user-1: 역할 deployment-user-1 보유
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 deployment-1를 이름을 renamed 으로 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

superadmin 이 아무것도 갖지 않은 id 를 수정하면, 대상이 없다는 것으로 거부됩니다

Given

- 이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
  - 프로젝트 team-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 배포 권한을 하나도 받지 않은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 배포 deployment-1: 복제본 1개를 두려 한다, 아직 리비전이 없다

When

- DeploymentAdapter.update: user-1 이 아무것도 갖지 않은 id 를 이름을 renamed 으로 수정합니다

Then

- 거부됩니다
  - 거부: EndpointNotFound

