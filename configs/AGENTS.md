# 설정 샘플 — 가드레일

## `sample.toml`은 생성물이다 — 직접 수정 금지

각 컴포넌트의 `sample.toml`(예: `configs/webserver/sample.toml`)은 설정 스키마에서 생성된 뷰이며
손으로 관리하는 파일이 아니다. 블록/필드 주석·기본값·예시값은 모두 해당 컴포넌트
`config/unified.py`의 각 필드 `BackendAIConfigMeta` 어노테이션에서 나온다.

`sample.toml`을 직접 수정하지 않는다 — 재생성 시 덮어써지고 스키마(진실 원천)와 어긋난다.

수정하려면:
1. 컴포넌트 `config/unified.py`에서 필드의 `description=`(및 기본값/예시)을 수정한다.
2. 컴포넌트의 `generate-sample` CLI로 재생성한다(`src/ai/backend/{component}/cli/config.py`).
   예: web server는 `./backend.ai web generate-sample --overwrite`.

참고: 구형 `.conf` 샘플(예: `configs/webserver/sample.conf`)은 실제 로컬 예시값으로 손으로
관리하며, 생성되는 `.toml`과 별개다.
