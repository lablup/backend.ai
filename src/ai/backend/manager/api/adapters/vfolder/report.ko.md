## vfolder

[배경](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

시나리오: 미완성 5 / 30

- ops 구성 (4)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - project_search: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (26)
  - batch_load_mount_permissions: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - batch_load_permissions: 성공 있음 1 · 거부 있음 1 (partial_bulk)
  - bulk_delete: 성공 없음 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - bulk_purge: 성공 없음 · 거부 없음 (single_entity): SCENARIO-GAP
  - clone: 성공 있음 1 · 거부 있음 2 (single_entity)
  - create: 성공 있음 1 · 거부 있음 1 (scope)
  - create_download_session: 성공 있음 1 · 거부 있음 1 (single_entity)
  - create_in_project: 성공 있음 1 · 거부 있음 1 (scope)
  - create_upload_session: 성공 있음 1 · 거부 있음 1 (single_entity)
  - delete: 성공 있음 1 · 거부 있음 1 (single_entity)
  - delete_files: 성공 있음 1 · 거부 있음 1 (single_entity)
  - deploy: 성공 있음 1 · 거부 있음 2 (scope, single_entity)
  - get: 성공 있음 2 · 거부 있음 2 (single_entity)
  - get_folder_usage: 성공 있음 2 · 거부 있음 1 (single_entity)
  - list_files: 성공 있음 1 · 거부 있음 1 (single_entity)
  - list_mount_policies: 성공 있음 1 · 거부 있음 1 (single_entity)
  - mkdir: 성공 있음 1 · 거부 있음 1 (single_entity)
  - move_file: 성공 있음 1 · 거부 있음 1 (single_entity)
  - partial_bulk_delete: 성공 있음 2 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - partial_bulk_restore: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: 성공 있음 2 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - purge: 성공 있음 1 · 거부 있음 2 (single_entity)
  - restore: 성공 있음 1 · 거부 있음 1 (single_entity)
  - set_mount_policy: 성공 있음 1 · 거부 있음 2 (single_entity)
  - unset_mount_policy: 성공 있음 1 · 거부 있음 1 (single_entity)
  - update: 성공 있음 1 · 거부 있음 2 (single_entity)

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [아무 역할도 받지 않은 superadmin 이 모든 vfolder 를 조회하면, 심은 vfolder 가 응답으로 옵니다](#searching-a-superadmin-searches-every-folder) | 성공 |
| [일반 사용자가 모든 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#searching-a-regular-user-may-not-search-every-folder) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 옵니다](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | 성공 |
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다](#batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id) | 성공 |
| [다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다](#batch_loading-an-accepted-share-loads-someone-elses-folder-by-id) | 성공 |
| [superadmin 이 다른 사용자의 vfolder 와 없는 id 를 함께 요청하면, 그 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다](#batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |
| [자기 vfolder 만 읽을 수 있는 사용자가 자기 vfolder, 공유받지 않은 다른 사용자의 vfolder, 없는 id 를 한 번에 요청하면, 입력 순서대로 그 vfolder, 거부, 거부가 옵니다](#batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order) | 거부 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder) | 거부 |
| [다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder) | 거부 |

**project_search**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 를 조회하면, 그 프로젝트의 vfolder 가 응답으로 옵니다](#reaching-a-user-granted-folder-read-in-a-project-lists-its-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-a-user-granted-nothing-may-not-list-a-projects-folders) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 이름 조각으로 걸러 이름 오름차순으로 한 페이지를 조회하면, 걸러진 자기 vfolder 둘만 이름 순서로 실린 한 페이지가 응답으로 옵니다](#searching-a-search-narrows-to-the-matching-folder-in-order-and-page) | 성공 |
| [vfolder 를 하나도 생성하지 않은 사용자가 자기 vfolder 를 조회하면, 응답은 비어 있습니다](#vfolder-a-user-who-has-made-no-folder-lists-none) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 범위의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-their-own-scope) | 거부 |

**batch_load_mount_permissions**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 vfolder 를 읽을 수 있는 사용자가 자기 마운트 레벨을 일괄 조회하면, 읽기/쓰기 레벨 하나가 실린 답이 옵니다](#batch_permissions-the-owner-of-a-personal-folder-loads-the-read-write-mount-level) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 마운트 레벨을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level) | 거부 |

**batch_load_permissions**

| 시나리오 | 판정 |
|---|---|
| [vfolder 읽기 권한을 받은 사용자가 자기 권한을 일괄 조회하면, 읽기 권한 하나가 실린 답이 옵니다](#batch_permissions-a-user-granted-folder-read-loads-their-permissions) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 권한을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다](#batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-permissions) | 거부 |

**clone**

| 시나리오 | 판정 |
|---|---|
| [복제할 수 있는 자기 vfolder 에 대해 복제 권한을 받은 사용자가 새 이름으로 복제하면, 복제된 vfolder 가 응답으로 옵니다](#cloning-a-user-granted-clone-copies-a-cloneable-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 복제하려 하면 권한 부족으로 거부됩니다](#cloning-a-user-granted-nothing-may-not-clone-their-folder) | 거부 |
| [복제할 수 있다고 표시되지 않은 vfolder 를 복제하려 하면 거부됩니다](#cloning-cloning-a-folder-not-marked-cloneable-is-refused) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 vfolder 생성 권한을 받은 사용자가 vfolder 를 생성하면, 그 vfolder 의 소유는 그 사용자에게 있습니다](#vfolder-a-user-granted-folder-create-makes-one-of-their-own) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다](#vfolder-a-user-granted-nothing-may-not-make-a-folder) | 거부 |

**create_download_session**

| 시나리오 | 판정 |
|---|---|
| [vfolder 읽기 권한을 받은 사용자가 폴더에서 내려받을 세션을 열면, 내려받기에 쓸 token 과 주소가 응답으로 옵니다](#files-a-user-granted-folder-read-opens-a-download-session) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더에서 내려받을 세션을 열려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-open-a-download-session) | 거부 |

**create_in_project**

| 시나리오 | 판정 |
|---|---|
| [프로젝트에서 vfolder 생성 권한을 받은 사용자가 그 프로젝트 소유로 vfolder 를 생성하면, 그 폴더는 그 프로젝트에 속합니다](#creating-a-user-granted-folder-create-in-a-project-makes-a-project-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 프로젝트 소유 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다](#creating-a-user-granted-nothing-may-not-make-a-project-folder) | 거부 |

**create_upload_session**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 폴더에 올릴 세션을 열면, 올리기에 쓸 token 과 주소가 응답으로 옵니다](#files-a-user-granted-folder-update-opens-an-upload-session) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더에 올릴 세션을 열려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-open-an-upload-session) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 를 soft delete 하면, 그 vfolder 가 삭제 대기 상태로 응답으로 옵니다](#deleting-a-user-granted-soft-delete-soft-deletes-their-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 soft delete 하려 하면 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-soft-delete-their-folder) | 거부 |

**delete_files**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 폴더 안의 파일을 지우면, 삭제를 맡은 background task 의 id 가 응답으로 옵니다](#files-a-user-granted-folder-update-deletes-files) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더 안의 파일을 지우려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-delete-files) | 거부 |

**deploy**

| 시나리오 | 판정 |
|---|---|
| [그 프로젝트에서 배포 생성 권한을 받은 사용자가 읽을 수 있는 모델 vfolder 로 배포를 만들면, 만들어진 배포의 id 와 이름이 응답으로 옵니다](#deploying-a-user-granted-deployment-create-deploys-a-model-folder) | 성공 |
| [폴더 읽기만 받고 배포 생성은 받지 않은 사용자가 모델 vfolder 로 배포를 만들려 하면 권한 부족으로 거부됩니다](#deploying-a-user-without-deployment-create-may-not-deploy-a-model-folder) | 거부 |
| [모델 용도가 아닌 vfolder 로 배포를 만들려 하면 모델 폴더가 아니라는 이유로 거부됩니다](#deploying-deploying-a-folder-not-used-as-a-model-is-refused) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다](#reaching-a-user-granted-folder-read-reads-their-own-folder) | 성공 |
| [다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다](#reaching-an-accepted-share-reads-someone-elses-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-a-user-granted-nothing-may-not-read-their-own-folder) | 거부 |
| [다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다](#reaching-an-unanswered-offer-may-not-read-someone-elses-folder) | 거부 |

**get_folder_usage**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 관리하지 않는 경로를 가리키는 vfolder 의 사용량을 조회하면, 사용량 없이 응답이 끝납니다](#usage-a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder) | 성공 |
| [자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 의 사용량을 조회하면, 저장소가 답한 사용량이 응답으로 옵니다](#usage-a-user-granted-folder-read-reads-the-folder-usage) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 의 사용량을 조회하려 하면 권한 부족으로 거부됩니다](#usage-a-user-granted-nothing-may-not-read-the-folder-usage) | 거부 |

**list_files**

| 시나리오 | 판정 |
|---|---|
| [vfolder 읽기 권한을 받은 사용자가 폴더의 파일 목록을 조회하면, 저장소가 답한 목록이 응답으로 옵니다](#files-a-user-granted-folder-read-lists-the-files) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더의 파일 목록을 조회하려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-list-the-files) | 거부 |

**list_mount_policies**

| 시나리오 | 판정 |
|---|---|
| [vfolder 읽기 권한을 받은 사용자가 폴더에 걸린 마운트 레벨을 조회하면, 걸린 레벨이 실린 목록이 응답으로 옵니다](#mount_policies-a-user-granted-folder-read-lists-the-mount-levels) | 성공 |
| [vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 받지 않은 다른 사용자가 걸린 레벨을 조회하려 하면 권한 부족으로 거부됩니다](#mount_policies-a-user-granted-nothing-may-not-list-the-mount-levels) | 거부 |

**mkdir**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 폴더 안에 디렉터리를 만들면, 만든 경로가 응답으로 옵니다](#files-a-user-granted-folder-update-makes-directories) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더 안에 디렉터리를 만들려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-make-directories) | 거부 |

**move_file**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 폴더 안에서 파일을 옮기면, 출발지와 도착지가 응답으로 옵니다](#files-a-user-granted-folder-update-moves-a-file) | 성공 |
| [아무 권한도 받지 않은 사용자가 폴더 안에서 파일을 옮기려 하면 권한 부족으로 거부됩니다](#files-a-user-granted-nothing-may-not-move-a-file) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 하면, 자기 vfolder 둘은 삭제 대기로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다](#partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [vfolder soft delete 권한을 받은 사용자가 soft delete 한 자기 vfolder 둘을 한 번에 restore 하면, 둘 다 사용할 수 있는 상태로 옵니다](#partial_bulk-restoring-several-folders-brings-them-back) | 성공 |
| [vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 폴더와 다른 사용자의 폴더를 한 번에 restore 하면, 자기 폴더만 되살아나고 다른 사용자의 폴더는 권한 부족 으로 실패 목록에 옵니다](#partial_bulk-restoring-several-folders-leaves-anothers-out) | 성공 |
| [vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 폴더와 삭제가 진행 중인 폴더를 한 번에 restore 하면, 휴지통에 있던 폴더만 되살아나고 삭제 중인 폴더는 실패 목록에 옵니다](#partial_bulk-restoring-several-folders-leaves-the-purging-one-out) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 수정하면, 자기 vfolder 둘은 수정되어 응답으로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다](#partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several) | 성공 |
| [아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk-a-user-granted-nothing-updates-none-of-several-folders) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 영구 삭제 권한을 받은 사용자가 휴지통에 있는 자기 vfolder 를 영구히 지우면, 그 vfolder 가 삭제 중 상태로 응답으로 옵니다](#purging-a-user-granted-hard-delete-purges-a-trashed-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 영구히 지우려 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-their-folder) | 거부 |
| [휴지통에 있지 않은 vfolder 를 영구히 지우려 하면 상태가 맞지 않는다는 이유로 거부됩니다](#purging-purging-a-folder-outside-the-trash-is-refused) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 vfolder 를 되살리면, 그 vfolder 의 id 가 응답으로 옵니다](#restoring-a-user-granted-soft-delete-restores-their-trashed-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 되살리려 하면 권한 부족으로 거부됩니다](#restoring-a-user-granted-nothing-may-not-restore-their-folder) | 거부 |

**set_mount_policy**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 읽기 전용으로 정하면, 정한 레벨이 응답으로 옵니다](#mount_policies-a-user-granted-folder-update-sets-another-users-mount-level) | 성공 |
| [아무 권한도 받지 않은 사용자가 마운트 레벨을 정하려 하면 권한 부족으로 거부됩니다](#mount_policies-a-user-granted-nothing-may-not-set-a-mount-level) | 거부 |
| [폴더 소유자의 마운트 레벨을 정하려 하면 그 자체로 거부됩니다](#mount_policies-setting-the-owners-own-mount-level-is-refused) | 거부 |

**unset_mount_policy**

| 시나리오 | 판정 |
|---|---|
| [vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 되돌리면, 그 자리와 지워졌다는 사실이 응답으로 옵니다](#mount_policies-a-user-granted-folder-update-takes-another-users-level-back) | 성공 |
| [vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 받지 않은 다른 사용자가 그것을 되돌리려 하면 권한 부족으로 거부됩니다](#mount_policies-a-user-granted-nothing-may-not-take-a-mount-level-back) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 의 이름과 옵션을 변경하면, 바뀐 vfolder 가 응답으로 옵니다](#editing-a-user-granted-folder-update-renames-their-folder) | 성공 |
| [아무 권한도 받지 않은 사용자가 자기 vfolder 를 변경하려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-update-their-folder) | 거부 |
| [자기 다른 vfolder 가 이미 사용하는 이름으로 변경하려 하면, 잘못된 값으로 거부됩니다](#editing-renaming-to-a-name-the-owner-already-uses-is-refused) | 거부 |

### admin_search

<a id="searching-a-superadmin-searches-every-folder"></a>

#### [a-superadmin-searches-every-folder](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

아무 역할도 받지 않은 superadmin 이 모든 vfolder 를 조회하면, 심은 vfolder 가 응답으로 옵니다

Given

- 남의 개인 vfolder 하나와, 아무 역할도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.admin_search: user-2이 필터 없이 모든 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 하나만 실린 페이지가 응답으로 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 vfolder 와 같다
  - items[0].entity_id: 응답의 id 와 같다
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'user'
  - items[0].ownership.user_id: vfolder 소유자와 같다
  - items[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - items[0].ownership.creator_id: 생성한 사용자와 같다
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - items[0].access_control.permission = 'none'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
  - items[0].metadata.created_at: 이 실행이 쓴 시각

<a id="searching-a-regular-user-may-not-search-every-folder"></a>

#### [a-regular-user-may-not-search-every-folder](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

일반 사용자가 모든 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.admin_search: user-1이 필터 없이 모든 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 옵니다

Given

- vfolder 를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFolderAdapter.batch_load_by_ids: user-1이 빈 목록으로 일괄 조회합니다

Then

- 빈 목록이 옵니다
  - loaded = []

<a id="batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id"></a>

#### [a-user-granted-folder-read-loads-their-own-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 미리 저장한 vfolder 하나가 전체가 응답으로 옵니다
  - length = 1
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].entity_id: 응답의 id 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-an-accepted-share-loads-someone-elses-folder-by-id"></a>

#### [an-accepted-share-loads-someone-elses-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 id 로 일괄 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 미리 저장한 vfolder 하나가 전체가 응답으로 옵니다
  - length = 1
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].entity_id: 응답의 id 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
  - [0].metadata.created_at: 이 실행이 쓴 시각

<a id="batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

superadmin 이 다른 사용자의 vfolder 와 없는 id 를 함께 요청하면, 그 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다

Given

- 남의 개인 vfolder 하나와, 아무 역할도 받지 않은 superadmin 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - superadmin user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 와 없는 id 를 일괄 조회합니다

Then

- 있는 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다
  - length = 2
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].entity_id: 응답의 id 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - [1] = None

<a id="batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

자기 vfolder 만 읽을 수 있는 사용자가 자기 vfolder, 공유받지 않은 다른 사용자의 vfolder, 없는 id 를 한 번에 요청하면, 입력 순서대로 그 vfolder, 거부, 거부가 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-2: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1, folder-2, 없는 id 순으로 일괄 조회합니다

Then

- 입력 순서대로 각 항목에 vfolder 또는 거부가 옵니다
  - length = 3
  - [0].id: 미리 저장한 vfolder 와 같다
  - [0].entity_id: 응답의 id 와 같다
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: vfolder 소유자와 같다
  - [0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - [0].ownership.creator_id: 생성한 사용자와 같다
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
  - [0].metadata.created_at: 이 실행이 쓴 시각
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_by_ids: user-1이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

<a id="batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder"></a>

#### [an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 아직 응답하지 않은, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_by_ids: user-2이 folder-1 vfolder 를 id 로 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### project_search

<a id="reaching-a-user-granted-folder-read-in-a-project-lists-its-folder"></a>

#### [a-user-granted-folder-read-in-a-project-lists-its-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 를 조회하면, 그 프로젝트의 vfolder 가 응답으로 옵니다

Given

- vfolder 하나를 가진 프로젝트와, 그 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.project_search: user-1이 folder-1 vfolder 가 놓인 프로젝트의 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: 미리 저장한 vfolder 와 같다
  - items[0].entity_id: 응답의 id 와 같다
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'group'
  - items[0].ownership.user_id: vfolder 소유자와 같다
  - items[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - items[0].ownership.creator_id: 생성한 사용자와 같다
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - items[0].access_control.permission = 'rw'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
  - items[0].metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-list-a-projects-folders"></a>

#### [a-user-granted-nothing-may-not-list-a-projects-folders](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 프로젝트의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- vfolder 하나를 가진 프로젝트와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.project_search: user-1이 folder-1 vfolder 가 놓인 프로젝트의 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### scoped_search

<a id="searching-a-search-narrows-to-the-matching-folder-in-order-and-page"></a>

#### [a-search-narrows-to-the-matching-folder-in-order-and-page](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 이름 조각으로 걸러 이름 오름차순으로 한 페이지를 조회하면, 걸러진 자기 vfolder 둘만 이름 순서로 실린 한 페이지가 응답으로 옵니다

Given

- 이름에 match 가 든 자기 개인 vfolder 둘과 들지 않는 자기 개인 vfolder 하나, 그리고 이름에 match 가 들지만 남의 것인 개인 vfolder 하나를 가진, 자기 스코프에서 vfolder READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder match-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder match-2: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder other-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder match-3: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 자기 스코프에서 vfolder READ 권한을 받은 사용자 준비
    - 역할 folder-holder-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-holder-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-holder-1 보유

When

- VFolderAdapter.scoped_search: user-1이 자기 범위에서 이름에 match 가 든 vfolder 를 이름 오름차순으로 2개까지 조회합니다

Then

- 걸러진 자기 vfolder 둘만 이름 순서로 실린 한 페이지가 응답으로 옵니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: 미리 저장한 vfolder 와 같다
  - items[0].entity_id: 응답의 id 와 같다
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'match-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'user'
  - items[0].ownership.user_id: vfolder 소유자와 같다
  - items[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - items[0].ownership.creator_id: 생성한 사용자와 같다
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - items[0].access_control.permission = 'none'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
  - items[0].metadata.created_at: 이 실행이 쓴 시각
  - items[1].id: 미리 저장한 vfolder 와 같다
  - items[1].entity_id: 응답의 id 와 같다
  - items[1].host = 'local:volume1'
  - items[1].status = 'ready'
  - items[1].metadata.name = 'match-2'
  - items[1].metadata.cloneable = False
  - items[1].metadata.last_used = None
  - items[1].access_control.ownership_type = 'user'
  - items[1].ownership.user_id: vfolder 소유자와 같다
  - items[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - items[1].ownership.creator_id: 생성한 사용자와 같다
  - items[1].ownership.creator_email = 'user-1@scenario.local'
  - items[1].unmanaged_path = None
  - items[1].metadata.usage_mode = 'general'
  - items[1].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - items[1].access_control.permission = 'none'
  - items[1].quota.max_size = None
  - items[1].quota.max_files = 1000
  - items[1].metadata.created_at: 이 실행이 쓴 시각
  - items ids: 걸러진 자기 vfolder 둘

<a id="vfolder-a-user-who-has-made-no-folder-lists-none"></a>

#### [a-user-who-has-made-no-folder-lists-none](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

vfolder 를 하나도 생성하지 않은 사용자가 자기 vfolder 를 조회하면, 응답은 비어 있습니다

Given

- vfolder 를 놓을 수 있는 도메인과, 거기서 vfolder 를 생성할 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - vfolder 를 생성할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 folder-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.scoped_search: user-1이 자기 vfolder 를 조회합니다

Then

- 응답이 비어 있습니다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-their-own-scope"></a>

#### [a-user-granted-nothing-may-not-search-their-own-scope](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

아무 권한도 받지 않은 사용자가 자기 범위의 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.scoped_search: user-1이 자기 범위의 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### batch_load_mount_permissions

<a id="batch_permissions-the-owner-of-a-personal-folder-loads-the-read-write-mount-level"></a>

#### [the-owner-of-a-personal-folder-loads-the-read-write-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

자기 개인 vfolder 를 읽을 수 있는 사용자가 자기 마운트 레벨을 일괄 조회하면, 읽기/쓰기 레벨 하나가 실린 답이 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_mount_permissions: user-1이 folder-1 vfolder 에서 자기 마운트 레벨을 일괄 조회합니다

Then

- 읽기/쓰기 마운트 레벨 하나가 실린 답이 옵니다
  - length = 1
  - [0] = <VFolderPermissionField.READ_WRITE: 'rw'>

<a id="batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

아무 권한도 받지 않은 사용자가 자기 마운트 레벨을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_mount_permissions: user-1이 folder-1 vfolder 에서 자기 마운트 레벨을 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### batch_load_permissions

<a id="batch_permissions-a-user-granted-folder-read-loads-their-permissions"></a>

#### [a-user-granted-folder-read-loads-their-permissions](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

vfolder 읽기 권한을 받은 사용자가 자기 권한을 일괄 조회하면, 읽기 권한 하나가 실린 답이 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.batch_load_permissions: user-1이 folder-1 vfolder 에서 자기 권한을 일괄 조회합니다

Then

- 읽기 권한 하나만 실린 답이 옵니다
  - length = 1
  - [0] = [<PermissionBitDTO.READ: 'read'>]

<a id="batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-permissions"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-permissions](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

아무 권한도 받지 않은 사용자가 자기 권한을 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.batch_load_permissions: user-1이 folder-1 vfolder 에서 자기 권한을 일괄 조회합니다

Then

- 그 항목은 권한 부족으로 거부됩니다
  - length = 1
  - 거부: NotEnoughPermission

### clone

<a id="cloning-a-user-granted-clone-copies-a-cloneable-folder"></a>

#### [a-user-granted-clone-copies-a-cloneable-folder](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

복제할 수 있는 자기 vfolder 에 대해 복제 권한을 받은 사용자가 새 이름으로 복제하면, 복제된 vfolder 가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 CREATE, READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, ready 상태입니다, 복제할 수 있습니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 CREATE 허용
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.clone: user-1이 folder-1 vfolder 를 copy 라는 이름으로 복제합니다

Then

- 복제된 vfolder 전체가 응답으로 옵니다
  - bgtask_id = '00000000-0000-0000-0000-000000000001'
  - vfolder.id: 응답의 entity_id 와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'copy'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: 복제한 사람와 같다
  - vfolder.ownership.project_id: 원본 vfolder 가 놓인 복제한 사람의 개인 프로젝트와 같다
  - vfolder.ownership.creator_id: 복제한 사람와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: 복제한 사람의 quota scope 와 같다
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="cloning-a-user-granted-nothing-may-not-clone-their-folder"></a>

#### [a-user-granted-nothing-may-not-clone-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 복제하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, ready 상태입니다, 복제할 수 있습니다

When

- VFolderAdapter.clone: user-1이 folder-1 vfolder 를 copy 라는 이름으로 복제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="cloning-cloning-a-folder-not-marked-cloneable-is-refused"></a>

#### [cloning-a-folder-not-marked-cloneable-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

복제할 수 있다고 표시되지 않은 vfolder 를 복제하려 하면 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 CREATE, READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 CREATE 허용
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.clone: user-1이 folder-1 vfolder 를 copy 라는 이름으로 복제합니다

Then

- 거부됩니다
  - 거부: Forbidden

### create

<a id="vfolder-a-user-granted-folder-create-makes-one-of-their-own"></a>

#### [a-user-granted-folder-create-makes-one-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

자기 스코프에서 vfolder 생성 권한을 받은 사용자가 vfolder 를 생성하면, 그 vfolder 의 소유는 그 사용자에게 있습니다

Given

- vfolder 를 놓을 수 있는 도메인과, 거기서 vfolder 를 생성할 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - vfolder 를 생성할 수 있는 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 folder-owner-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
    - 역할 folder-owner-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- VFolderAdapter.create: user-1이 work 이라는 이름으로 vfolder 를 생성합니다

Then

- 만든 vfolder 전체가 응답으로 오고, 그 소유는 만든 사람에게 있습니다
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: 만든 사람와 같다
  - ownership.project_id: 건너뜀: 개인 vfolder 는 그 사용자의 개인 프로젝트에 붙습니다. 그 id 는 사용자를 생성할 때 생깁니다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - status: 건너뜀: vfolder 가 생성되는 동안 오가는 값입니다
  - metadata.usage_mode: 건너뜀: 타입이 이미 값을 고정합니다
  - metadata.quota_scope_id: 건너뜀: 저장소가 정합니다
  - access_control.permission: 건너뜀: 만든 사람에게는 확인할 것이 없습니다
  - quota: 건너뜀: 저장소가 응답하는 값이라 여기서 말할 수 없습니다
  - metadata.created_at: 이 실행이 쓴 시각

<a id="vfolder-a-user-granted-nothing-may-not-make-a-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

아무 권한도 받지 않은 사용자가 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다

Given

- vfolder 를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFolderAdapter.create: user-1이 denied 이라는 이름으로 vfolder 를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create_download_session

<a id="files-a-user-granted-folder-read-opens-a-download-session"></a>

#### [a-user-granted-folder-read-opens-a-download-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 읽기 권한을 받은 사용자가 폴더에서 내려받을 세션을 열면, 내려받기에 쓸 token 과 주소가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.create_download_session: user-1이 folder-1 vfolder 에서 내려받을 세션을 엽니다

Then

- 내려받기에 쓸 token 과 주소가 응답으로 옵니다
  - token = 'download-token'
  - url = 'http://127.0.0.1:6021/download'

<a id="files-a-user-granted-nothing-may-not-open-a-download-session"></a>

#### [a-user-granted-nothing-may-not-open-a-download-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더에서 내려받을 세션을 열려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.create_download_session: user-1이 folder-1 vfolder 에서 내려받을 세션을 엽니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create_in_project

<a id="creating-a-user-granted-folder-create-in-a-project-makes-a-project-folder"></a>

#### [a-user-granted-folder-create-in-a-project-makes-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py): pass

프로젝트에서 vfolder 생성 권한을 받은 사용자가 그 프로젝트 소유로 vfolder 를 생성하면, 그 폴더는 그 프로젝트에 속합니다

Given

- vfolder 를 받아줄 프로젝트와, 그 프로젝트에서 vfolder 생성 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1: 이 프로젝트의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 역할 folder-maker-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 folder-maker-1: vfolder 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 folder-maker-1 보유

When

- VFolderAdapter.create_in_project: user-1이 project-1 프로젝트 소유로 shared vfolder 를 생성합니다

Then

- 방금 만든 vfolder 전체가 응답으로 옵니다
  - id: 응답의 entity_id 와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'shared'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'group'
  - ownership.user_id: 폴더 소유자와 같다
  - ownership.project_id: 폴더가 놓인 프로젝트와 같다
  - ownership.creator_id: 만든 사람와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: 폴더 소유자의 quota scope 와 같다
  - access_control.permission = 'rw'
  - quota.max_size = None
  - quota.max_files = 1000
  - metadata.created_at: 이 실행이 쓴 시각

<a id="creating-a-user-granted-nothing-may-not-make-a-project-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py): pass

아무 권한도 받지 않은 사용자가 프로젝트 소유 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다

Given

- vfolder 를 받아줄 프로젝트와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1: 이 프로젝트의 vfolder 는 local:volume1에 놓을 수 있습니다

When

- VFolderAdapter.create_in_project: user-1이 project-1 프로젝트 소유로 shared vfolder 를 생성합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create_upload_session

<a id="files-a-user-granted-folder-update-opens-an-upload-session"></a>

#### [a-user-granted-folder-update-opens-an-upload-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 수정 권한을 받은 사용자가 폴더에 올릴 세션을 열면, 올리기에 쓸 token 과 주소가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.create_upload_session: user-1이 folder-1 vfolder 에 올릴 세션을 엽니다

Then

- 올리기에 쓸 token 과 주소가 응답으로 옵니다
  - token = 'upload-token'
  - url = 'http://127.0.0.1:6021/upload'

<a id="files-a-user-granted-nothing-may-not-open-an-upload-session"></a>

#### [a-user-granted-nothing-may-not-open-an-upload-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더에 올릴 세션을 열려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.create_upload_session: user-1이 folder-1 vfolder 에 올릴 세션을 엽니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### delete

<a id="deleting-a-user-granted-soft-delete-soft-deletes-their-folder"></a>

#### [a-user-granted-soft-delete-soft-deletes-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deleting.py): pass

자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 를 soft delete 하면, 그 vfolder 가 삭제 대기 상태로 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.delete: user-1이 folder-1 vfolder 를 soft delete 합니다

Then

- 삭제 대기 상태의 vfolder 전체가 응답으로 옵니다
  - id: 부른 vfolder 의 id 와 같다
  - vfolder.id: 미리 저장한 vfolder 와 같다
  - vfolder.entity_id: 응답의 id 와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'delete-pending'
  - vfolder.metadata.name = 'folder-1'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: vfolder 소유자와 같다
  - vfolder.ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - vfolder.ownership.creator_id: 생성한 사용자와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-their-folder"></a>

#### [a-user-granted-nothing-may-not-soft-delete-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 soft delete 하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.delete: user-1이 folder-1 vfolder 를 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### delete_files

<a id="files-a-user-granted-folder-update-deletes-files"></a>

#### [a-user-granted-folder-update-deletes-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 수정 권한을 받은 사용자가 폴더 안의 파일을 지우면, 삭제를 맡은 background task 의 id 가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.delete_files: user-1이 folder-1 vfolder 안의 파일 하나를 지웁니다

Then

- 삭제를 맡은 background task 의 id 가 응답으로 옵니다
  - bgtask_id = '00000000-0000-0000-0000-000000000002'

<a id="files-a-user-granted-nothing-may-not-delete-files"></a>

#### [a-user-granted-nothing-may-not-delete-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더 안의 파일을 지우려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.delete_files: user-1이 folder-1 vfolder 안의 파일 하나를 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### deploy

<a id="deploying-a-user-granted-deployment-create-deploys-a-model-folder"></a>

#### [a-user-granted-deployment-create-deploys-a-model-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

그 프로젝트에서 배포 생성 권한을 받은 사용자가 읽을 수 있는 모델 vfolder 로 배포를 만들면, 만들어진 배포의 id 와 이름이 응답으로 옵니다

Given

- 배포를 놓을 프로젝트와 자원 그룹, model 용도 vfolder 하나, 런타임 종류와 리비전 프리셋, 그리고 폴더 읽기와 배포 생성을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓입니다, ready 상태입니다, model 용도입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유
  - 역할 deployer-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 deployer-1: deployment 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 deployer-1 보유
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트, 모델 정의가 채워져 있다

When

- VFolderAdapter.deploy: user-1이 folder-1 vfolder 로 project-1 에 배포를 만듭니다

Then

- 만들어진 배포의 id 와 폴더 이름에서 온 배포 이름이 응답으로 옵니다
  - deployment_id: 건너뜀: 데이터베이스가 생성합니다
  - deployment_name: 'folder-1'로 시작하는 이름

<a id="deploying-a-user-without-deployment-create-may-not-deploy-a-model-folder"></a>

#### [a-user-without-deployment-create-may-not-deploy-a-model-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

폴더 읽기만 받고 배포 생성은 받지 않은 사용자가 모델 vfolder 로 배포를 만들려 하면 권한 부족으로 거부됩니다

Given

- 배포를 놓을 프로젝트와 자원 그룹, model 용도 vfolder 하나, 런타임 종류와 리비전 프리셋, 그리고 폴더 읽기만 받고 배포 생성은 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓입니다, ready 상태입니다, model 용도입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트, 모델 정의가 채워져 있다

When

- VFolderAdapter.deploy: user-1이 folder-1 vfolder 로 project-1 에 배포를 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deploying-deploying-a-folder-not-used-as-a-model-is-refused"></a>

#### [deploying-a-folder-not-used-as-a-model-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

모델 용도가 아닌 vfolder 로 배포를 만들려 하면 모델 폴더가 아니라는 이유로 거부됩니다

Given

- 배포를 놓을 프로젝트와 자원 그룹, general 용도 vfolder 하나, 런타임 종류와 리비전 프리셋, 그리고 폴더 읽기와 배포 생성을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 프로젝트 project-1
  - 자원 그룹 resource-group-1: fifo 스케줄러를 사용합니다
  - 프로젝트 vfolder folder-1: 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유
  - 역할 deployer-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 deployer-1: deployment 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 deployer-1 보유
  - 인퍼런스 런타임 종류 runtime-1: 기본 모델 정의가 비어 있고, 모델 vfolder 의 설정 파일을 읽지 않습니다
  - 컨테이너 레지스트리 host-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 배포 리비전 프리셋 preset-1: 단일 노드, 복제본 하나, 롤링 업데이트, 모델 정의가 채워져 있다

When

- VFolderAdapter.deploy: user-1이 folder-1 vfolder 로 project-1 에 배포를 만듭니다

Then

- 거부됩니다
  - 거부: NotAModelVFolder

### get

<a id="reaching-a-user-granted-folder-read-reads-their-own-folder"></a>

#### [a-user-granted-folder-read-reads-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-1이 folder-1 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - id: 미리 저장한 vfolder 와 같다
  - entity_id: 응답의 id 와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: vfolder 소유자와 같다
  - ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - ownership.creator_id: 생성한 사용자와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - access_control.permission = 'none'
  - quota.max_size = None
  - quota.max_files = 1000
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-an-accepted-share-reads-someone-elses-folder"></a>

#### [an-accepted-share-reads-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 조회하면, 그 vfolder 가 응답으로 옵니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 받아들인, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 공유 제안 share-1: 받는 사람이 받아들임
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 vfolder 를 조회합니다

Then

- 미리 저장한 vfolder 전체가 응답으로 옵니다
  - id: 미리 저장한 vfolder 와 같다
  - entity_id: 응답의 id 와 같다
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: vfolder 소유자와 같다
  - ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - ownership.creator_id: 생성한 사용자와 같다
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - access_control.permission = 'none'
  - quota.max_size = None
  - quota.max_files = 1000
  - metadata.created_at: 이 실행이 쓴 시각

<a id="reaching-a-user-granted-nothing-may-not-read-their-own-folder"></a>

#### [a-user-granted-nothing-may-not-read-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.get: user-1이 folder-1 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reaching-an-unanswered-offer-may-not-read-someone-elses-folder"></a>

#### [an-unanswered-offer-may-not-read-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다

Given

- 남의 개인 vfolder 를 읽기로 공유 제안받아 아직 응답하지 않은, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 공유 제안 share-1: READ 권한으로 제안되었고, 아직 응답하지 않았습니다
  - vfolder 읽기 권한 부여
    - 역할 folder-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-2: 역할 folder-reader-1 보유

When

- VFolderAdapter.get: user-2이 folder-1 vfolder 를 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_folder_usage

<a id="usage-a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder"></a>

#### [a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 관리하지 않는 경로를 가리키는 vfolder 의 사용량을 조회하면, 사용량 없이 응답이 끝납니다

Given

- 관리하지 않는 경로를 가리키는 개인 vfolder 하나를 가진, 자기 개인 폴더에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder unmanaged-1: 그 사람의 개인 프로젝트에 놓이고, 관리하지 않는 경로를 가리킵니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.get_folder_usage: user-1이 unmanaged-1 vfolder 의 사용량을 조회합니다

Then

- 관리하지 않는 폴더라 사용량 없이 응답이 끝납니다
  - 응답 없이 끝납니다

<a id="usage-a-user-granted-folder-read-reads-the-folder-usage"></a>

#### [a-user-granted-folder-read-reads-the-folder-usage](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 의 사용량을 조회하면, 저장소가 답한 사용량이 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.get_folder_usage: user-1이 folder-1 vfolder 의 사용량을 조회합니다

Then

- 저장소가 답한 사용량 전체가 응답으로 옵니다
  - num_files = 0
  - used_bytes.expr = '0'
  - used_bytes.display = '0'

<a id="usage-a-user-granted-nothing-may-not-read-the-folder-usage"></a>

#### [a-user-granted-nothing-may-not-read-the-folder-usage](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

아무 권한도 받지 않은 사용자가 vfolder 의 사용량을 조회하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.get_folder_usage: user-1이 folder-1 vfolder 의 사용량을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### list_files

<a id="files-a-user-granted-folder-read-lists-the-files"></a>

#### [a-user-granted-folder-read-lists-the-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 읽기 권한을 받은 사용자가 폴더의 파일 목록을 조회하면, 저장소가 답한 목록이 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 READ 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.list_files: user-1이 folder-1 vfolder 의 파일 목록을 조회합니다

Then

- 저장소가 답한 파일 목록 전체가 응답으로 옵니다
  - items.length = 2
  - items[0].name = 'hello.txt'
  - items[0].type = 'FILE'
  - items[0].size = 5
  - items[0].mode = 33188
  - items[0].created_at = '2026-01-01 00:00:00'
  - items[0].updated_at = '2026-01-02 00:00:00'
  - items[1].name = 'data'
  - items[1].type = 'DIRECTORY'
  - items[1].size = 0
  - items[1].mode = 16877
  - items[1].created_at = '2026-01-01 00:00:00'
  - items[1].updated_at = '2026-01-01 00:00:00'

<a id="files-a-user-granted-nothing-may-not-list-the-files"></a>

#### [a-user-granted-nothing-may-not-list-the-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더의 파일 목록을 조회하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.list_files: user-1이 folder-1 vfolder 의 파일 목록을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### list_mount_policies

<a id="mount_policies-a-user-granted-folder-read-lists-the-mount-levels"></a>

#### [a-user-granted-folder-read-lists-the-mount-levels](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

vfolder 읽기 권한을 받은 사용자가 폴더에 걸린 마운트 레벨을 조회하면, 걸린 레벨이 실린 목록이 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 READ, UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 READ 허용
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.list_mount_policies: user-1이 folder-1 vfolder 에 걸린 마운트 레벨을 조회합니다

Then

- 마운트 레벨 하나가 실린 목록이 응답으로 옵니다
  - items.length = 1
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 응답의 id 와 같다
  - items[0].vfolder_id: 부른 vfolder 와 같다
  - items[0].user_id: 레벨을 받은 사용자와 같다
  - items[0].permission = 'ro'
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각

<a id="mount_policies-a-user-granted-nothing-may-not-list-the-mount-levels"></a>

#### [a-user-granted-nothing-may-not-list-the-mount-levels](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 받지 않은 다른 사용자가 걸린 레벨을 조회하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.list_mount_policies: user-1이 folder-1 vfolder 에 다른 사용자의 마운트 레벨을 정한 뒤, 권한이 없는 user-2이 걸린 레벨을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### mkdir

<a id="files-a-user-granted-folder-update-makes-directories"></a>

#### [a-user-granted-folder-update-makes-directories](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 수정 권한을 받은 사용자가 폴더 안에 디렉터리를 만들면, 만든 경로가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.mkdir: user-1이 folder-1 vfolder 안에 디렉터리 둘을 만듭니다

Then

- 만든 디렉터리 경로가 응답으로 옵니다
  - results = ['new', 'other']

<a id="files-a-user-granted-nothing-may-not-make-directories"></a>

#### [a-user-granted-nothing-may-not-make-directories](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더 안에 디렉터리를 만들려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.mkdir: user-1이 folder-1 vfolder 안에 디렉터리 둘을 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### move_file

<a id="files-a-user-granted-folder-update-moves-a-file"></a>

#### [a-user-granted-folder-update-moves-a-file](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

vfolder 수정 권한을 받은 사용자가 폴더 안에서 파일을 옮기면, 출발지와 도착지가 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.move_file: user-1이 folder-1 vfolder 안에서 파일 하나를 옮깁니다

Then

- 옮긴 파일의 출발지와 도착지가 응답으로 옵니다
  - src = 'hello.txt'
  - dst = 'data/hello.txt'

<a id="files-a-user-granted-nothing-may-not-move-a-file"></a>

#### [a-user-granted-nothing-may-not-move-a-file](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

아무 권한도 받지 않은 사용자가 폴더 안에서 파일을 옮기려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.move_file: user-1이 folder-1 vfolder 안에서 파일 하나를 옮깁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several"></a>

#### [a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 하면, 자기 vfolder 둘은 삭제 대기로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 합니다

Then

- 자기 vfolder 둘이 delete-pending 상태로 오고, 다른 사용자의 vfolder 는 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].entity_id: 응답의 id 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'delete-pending'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].entity_id: 응답의 id 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'delete-pending'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.partial_bulk_delete: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 soft delete 합니다

Then

- 처리된 vfolder 없이, 셋 모두 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 vfolder 의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 vfolder 의 id 와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### partial_bulk_restore

<a id="partial_bulk-restoring-several-folders-brings-them-back"></a>

#### [restoring-several-folders-brings-them-back](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

vfolder soft delete 권한을 받은 사용자가 soft delete 한 자기 vfolder 둘을 한 번에 restore 하면, 둘 다 사용할 수 있는 상태로 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_restore: user-1이 자기 vfolder 둘을 한 번에 soft delete 했다가 한 번에 restore 합니다. restore 의 응답을 반환합니다

Then

- 자기 vfolder 둘이 ready 상태로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].entity_id: 응답의 id 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].entity_id: 응답의 id 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed = []

<a id="partial_bulk-restoring-several-folders-leaves-anothers-out"></a>

#### [restoring-several-folders-leaves-anothers-out](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 폴더와 다른 사용자의 폴더를 한 번에 restore 하면, 자기 폴더만 되살아나고 다른 사용자의 폴더는 권한 부족 으로 실패 목록에 옵니다

Given

- delete-pending 의 자기 개인 vfolder 하나와 delete-pending 의 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_restore: user-1이 휴지통에 있는 자기 vfolder 하나와 다른 사용자의 vfolder 하나를 한 번에 restore 합니다

Then

- 휴지통에 있던 자기 폴더만 사용할 수 있는 상태로 오고, 다른 사용자의 폴더는 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].entity_id: 응답의 id 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-restoring-several-folders-leaves-the-purging-one-out"></a>

#### [restoring-several-folders-leaves-the-purging-one-out](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 폴더와 삭제가 진행 중인 폴더를 한 번에 restore 하면, 휴지통에 있던 폴더만 되살아나고 삭제 중인 폴더는 실패 목록에 옵니다

Given

- delete-pending 의 자기 개인 vfolder 하나와 delete-ongoing 의 자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓입니다, delete-ongoing 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_restore: user-1이 휴지통에 있는 자기 vfolder 와 삭제가 진행 중인 자기 vfolder 를 한 번에 restore 합니다

Then

- 휴지통에 있던 폴더만 사용할 수 있는 상태로 오고, 삭제가 진행 중인 폴더는 실패 목록에 옵니다
  - successes count = 1
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].entity_id: 응답의 id 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 삭제가 진행 중인 vfolder 와 같다
  - failed[0].message: 'being purged'를 담은 이유

### partial_bulk_update

<a id="partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several"></a>

#### [a-user-granted-folder-update-updates-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 수정하면, 자기 vfolder 둘은 수정되어 응답으로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 복제 가능으로 변경합니다

Then

- 자기 vfolder 둘이 복제 가능으로 오고, 다른 사용자의 vfolder 는 권한이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 vfolder 와 같다
  - successes[0].entity_id: 응답의 id 와 같다
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = True
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: vfolder 소유자와 같다
  - successes[0].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[0].ownership.creator_id: 생성한 사용자와 같다
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: 이 실행이 쓴 시각
  - successes[1].id: 미리 저장한 vfolder 와 같다
  - successes[1].entity_id: 응답의 id 와 같다
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = True
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: vfolder 소유자와 같다
  - successes[1].ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - successes[1].ownership.creator_id: 생성한 사용자와 같다
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
  - successes[1].metadata.created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk-a-user-granted-nothing-updates-none-of-several-folders"></a>

#### [a-user-granted-nothing-updates-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.partial_bulk_update: user-1이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 복제 가능으로 변경합니다

Then

- 처리된 vfolder 없이, 셋 모두 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 3
  - failed[0].id: 대상 vfolder 의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 vfolder 의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유
  - failed[2].id: 대상 vfolder 의 id 와 같다
  - failed[2].message: 'Insufficient permission'를 담은 이유

### purge

<a id="purging-a-user-granted-hard-delete-purges-a-trashed-folder"></a>

#### [a-user-granted-hard-delete-purges-a-trashed-folder](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

자기 개인 프로젝트에서 vfolder 영구 삭제 권한을 받은 사용자가 휴지통에 있는 자기 vfolder 를 영구히 지우면, 그 vfolder 가 삭제 중 상태로 응답으로 옵니다

Given

- delete-pending 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.purge: user-1이 folder-1 vfolder 를 영구히 지웁니다

Then

- 삭제 중 상태의 vfolder 전체가 응답으로 옵니다
  - id: 부른 vfolder 의 id 와 같다
  - vfolder.id: 미리 저장한 vfolder 와 같다
  - vfolder.entity_id: 응답의 id 와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'delete-ongoing'
  - vfolder.metadata.name = 'folder-1'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: vfolder 소유자와 같다
  - vfolder.ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - vfolder.ownership.creator_id: 생성한 사용자와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="purging-a-user-granted-nothing-may-not-purge-their-folder"></a>

#### [a-user-granted-nothing-may-not-purge-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 영구히 지우려 하면 권한 부족으로 거부됩니다

Given

- delete-pending 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다

When

- VFolderAdapter.purge: user-1이 folder-1 vfolder 를 영구히 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-purging-a-folder-outside-the-trash-is-refused"></a>

#### [purging-a-folder-outside-the-trash-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

휴지통에 있지 않은 vfolder 를 영구히 지우려 하면 상태가 맞지 않는다는 이유로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 HARD_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.purge: user-1이 folder-1 vfolder 를 영구히 지웁니다

Then

- 거부됩니다
  - 거부: VFolderFilterStatusFailed

### restore

<a id="restoring-a-user-granted-soft-delete-restores-their-trashed-folder"></a>

#### [a-user-granted-soft-delete-restores-their-trashed-folder](/tests/scenario/bai_scenario/manager/vfolder/test_restoring.py): pass

자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 vfolder 를 되살리면, 그 vfolder 의 id 가 응답으로 옵니다

Given

- delete-pending 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 SOFT_DELETE 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 SOFT_DELETE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.restore: user-1이 folder-1 vfolder 를 휴지통에서 되살립니다

Then

- 되살린 vfolder 의 id 가 응답으로 옵니다
  - id: 되살린 vfolder 의 id 와 같다

<a id="restoring-a-user-granted-nothing-may-not-restore-their-folder"></a>

#### [a-user-granted-nothing-may-not-restore-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_restoring.py): pass

아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 되살리려 하면 권한 부족으로 거부됩니다

Given

- delete-pending 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓입니다, delete-pending 상태입니다

When

- VFolderAdapter.restore: user-1이 folder-1 vfolder 를 휴지통에서 되살립니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### set_mount_policy

<a id="mount_policies-a-user-granted-folder-update-sets-another-users-mount-level"></a>

#### [a-user-granted-folder-update-sets-another-users-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 읽기 전용으로 정하면, 정한 레벨이 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.set_mount_policy: user-1이 folder-1 vfolder 에서 다른 사용자의 마운트 레벨을 읽기 전용으로 정합니다

Then

- 정한 마운트 레벨 전체가 응답으로 옵니다
  - policy.id: 건너뜀: 데이터베이스가 생성합니다
  - policy.field_id: 응답의 id 와 같다
  - policy.vfolder_id: 부른 vfolder 와 같다
  - policy.user_id: 레벨을 받은 사용자와 같다
  - policy.permission = 'ro'
  - policy.created_at: 이 실행이 쓴 시각
  - policy.updated_at: 이 실행이 쓴 시각

<a id="mount_policies-a-user-granted-nothing-may-not-set-a-mount-level"></a>

#### [a-user-granted-nothing-may-not-set-a-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

아무 권한도 받지 않은 사용자가 마운트 레벨을 정하려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 아무 권한도 받지 않은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.set_mount_policy: user-1이 folder-1 vfolder 에서 다른 사용자의 마운트 레벨을 읽기 전용으로 정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="mount_policies-setting-the-owners-own-mount-level-is-refused"></a>

#### [setting-the-owners-own-mount-level-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

폴더 소유자의 마운트 레벨을 정하려 하면 그 자체로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.set_mount_policy: user-1이 folder-1 vfolder 에서 소유자 자신의 마운트 레벨을 읽기 전용으로 정합니다

Then

- 거부됩니다
  - 거부: VFolderMountPolicyNotApplicable

### unset_mount_policy

<a id="mount_policies-a-user-granted-folder-update-takes-another-users-level-back"></a>

#### [a-user-granted-folder-update-takes-another-users-level-back](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 되돌리면, 그 자리와 지워졌다는 사실이 응답으로 옵니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.unset_mount_policy: user-1이 folder-1 vfolder 에서 다른 사용자의 마운트 레벨을 정했다가 되돌립니다

Then

- 되돌린 마운트 레벨의 자리가 응답으로 오고, 그 행은 지워졌습니다
  - vfolder_id: 부른 vfolder 와 같다
  - user_id: 레벨을 잃은 사용자와 같다
  - removed = True

<a id="mount_policies-a-user-granted-nothing-may-not-take-a-mount-level-back"></a>

#### [a-user-granted-nothing-may-not-take-a-mount-level-back](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 받지 않은 다른 사용자가 그것을 되돌리려 하면 권한 부족으로 거부됩니다

Given

- 사용할 수 있는 상태의 개인 vfolder 하나를 가진, 자기 개인 폴더에 UPDATE 권한을 받은 사용자 한 명, 그리고 그 폴더를 쓰지 않는 다른 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.unset_mount_policy: user-1이 folder-1 vfolder 에서 다른 사용자의 마운트 레벨을 정한 뒤, 권한이 없는 user-2이 그것을 되돌립니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-a-user-granted-folder-update-renames-their-folder"></a>

#### [a-user-granted-folder-update-renames-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 의 이름과 옵션을 변경하면, 바뀐 vfolder 가 응답으로 옵니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 renamed 으로 변경하고 복제 가능으로 변경합니다

Then

- 첫 vfolder 가 renamed 이라는 이름과 복제 가능으로 응답으로 옵니다
  - vfolder.id: 미리 저장한 vfolder 와 같다
  - vfolder.entity_id: 응답의 id 와 같다
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'renamed'
  - vfolder.metadata.cloneable = True
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: vfolder 소유자와 같다
  - vfolder.ownership.project_id: vfolder 가 놓인 프로젝트와 같다
  - vfolder.ownership.creator_id: 생성한 사용자와 같다
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: 미리 저장한 vfolder 의 quota scope 와 같다
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-may-not-update-their-folder"></a>

#### [a-user-granted-nothing-may-not-update-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

아무 권한도 받지 않은 사용자가 자기 vfolder 를 변경하려 하면 권한 부족으로 거부됩니다

Given

- 자기 개인 vfolder 둘을 가진, 아무 권한도 받지 않은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 renamed 으로 변경하고 복제 가능으로 변경합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-renaming-to-a-name-the-owner-already-uses-is-refused"></a>

#### [renaming-to-a-name-the-owner-already-uses-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

자기 다른 vfolder 가 이미 사용하는 이름으로 변경하려 하면, 잘못된 값으로 거부됩니다

Given

- 자기 개인 vfolder 둘을 가진, 자기 개인 프로젝트에서 폴더에 UPDATE 권한을 받은 사용자 한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 개인 vfolder first-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder second-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - 개인 vfolder folder-1: 그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다
  - vfolder 권한 부여
    - 역할 folder-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 folder-writer-1: vfolder 전체에 UPDATE 허용
    - 일반 사용자 user-1: 역할 folder-writer-1 보유

When

- VFolderAdapter.update: user-1이 자기 첫 vfolder 를 둘째 vfolder 의 이름으로 변경하고 복제 가능으로 변경합니다

Then

- 거부됩니다
  - 거부: VFolderInvalidParameter

