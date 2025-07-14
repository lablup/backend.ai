## Background

* 현재 agent, manager, storage-proxy, webserver 서비스에 대해 config 를 모두 pydantic 기반으로 변경함.
* 각 서비스의 sample config 파일을 CLI 명령어로 생성할 수 있도록 진행했음.
    * ./backend.ai mgr config generate-sample --overwrite
    * ./backend.ai ag config generate-sample --overwrite
    * ./backend.ai storage config generate-sample --overwrite
    * ./backend.ai web config generate-sample --overwrite

## Goal

* configs 디렉토리에 각 서비스의 sample config 파일을 관리하고 있는데, 이 파일들을 config CLI 에서 검증할 수 있도록 기능을 추가하려 함
* 각 서비스의 config 파일을 검증하는 명령어를 추가함. (path 를 지정하지 않으면 기본 경로인 ./configs/{service_name}/halfstack.yaml 파일을 사용함)
    * ./backend.ai mgr config validate
    * ./backend.ai ag config validate
    * ./backend.ai storage config validate
    * ./backend.ai web config validate
* 검증은 단순히 pydantic으로 생성한 config의 model_dump() 를 수행해 검증.
