# Backend.AI Service Layer Test Scenarios Documentation Task

## 작업 목표
Backend.AI의 manager 컴포넌트 서비스 레이어에 대한 테스트 시나리오를 문서화

## 작업 계획

### 1. 서비스 목록 식별 (완료)
확인된 서비스 모듈:
- agent
- auth  
- container_registry
- domain
- group
- image
- keypair_resource_policy
- metric
- model_serving
- project_resource_policy
- resource_preset
- session
- user
- user_resource_policy
- vfolder

### 2. 각 서비스별 테스트 시나리오 작성 순서
1. [x] agent - 에이전트 관리 서비스
2. [x] auth - 인증/인가 서비스
3. [x] container_registry - 컨테이너 레지스트리 관리
4. [x] domain - 도메인 관리
5. [x] group - 그룹 관리
6. [x] image - 이미지 관리
7. [x] keypair_resource_policy - 키페어 리소스 정책
8. [x] metric - 메트릭 수집 및 관리
9. [x] model_serving - 모델 서빙
10. [x] project_resource_policy - 프로젝트 리소스 정책
11. [x] resource_preset - 리소스 프리셋
12. [x] session - 세션 관리
13. [x] user - 사용자 관리
14. [x] user_resource_policy - 사용자 리소스 정책
15. [x] vfolder - 가상 폴더 관리

### 3. 작업 진행 상태
- [x] 서비스 목록 식별
- [x] test_scenarios 디렉토리 생성
- [x] 각 서비스별 테스트 시나리오 문서 작성
- [ ] 전체 검토 및 누락 사항 확인

### 4. 테스트 시나리오 문서 구조
각 서비스별 문서는 다음 구조를 따름:
- 서비스 개요
- 주요 기능 목록
- 각 기능별 테스트 시나리오
  - 기능 설명
  - 입력값
  - 기대 출력값
  - 동작 근거

## 진행 사항 기록

### 완료된 작업 (2025-07-16)

#### 초기 작업 완료
1. **서비스 목록 식별 완료**
   - src/ai/backend/manager/services 하위의 15개 서비스 모듈 확인
   - 각 서비스의 action 파일과 service.py 구조 분석

2. **테스트 시나리오 문서 작성 완료**
   - 모든 15개 서비스에 대한 테스트 시나리오 문서 생성
   - 각 문서는 다음 내용 포함:
     - 서비스 개요 및 주요 기능 목록
     - 각 기능별 상세 테스트 케이스 (정상/비정상 시나리오)
     - 복합 시나리오 및 공통 에러 케이스
     - 성능 및 보안 요구사항

3. **작성된 테스트 시나리오 파일 목록**
   - agent.md - 에이전트 관리 (6개 기능, 30개 테스트 케이스)
   - auth.md - 인증/인가 (10개 기능, 45개 테스트 케이스)
   - container_registry.md - 컨테이너 레지스트리 (5개 기능, 25개 테스트 케이스)
   - domain.md - 도메인 관리 (6개 기능, 32개 테스트 케이스)
   - group.md - 그룹 관리 (6개 기능, 35개 테스트 케이스)
   - image.md - 이미지 관리 (12개 기능, 48개 테스트 케이스)
   - keypair_resource_policy.md - 키페어 리소스 정책 (3개 기능, 15개 테스트 케이스)
   - metric.md - 메트릭 수집 (2개 기능, 13개 테스트 케이스)
   - model_serving.md - 모델 서빙 (16개 기능, 52개 테스트 케이스)
   - project_resource_policy.md - 프로젝트 리소스 정책 (3개 기능, 15개 테스트 케이스)
   - resource_preset.md - 리소스 프리셋 (5개 기능, 35개 테스트 케이스)
   - session.md - 세션 관리 (27개 기능, 65개 테스트 케이스)
   - user.md - 사용자 관리 (6개 기능, 32개 테스트 케이스)
   - user_resource_policy.md - 사용자 리소스 정책 (3개 기능, 15개 테스트 케이스)
   - vfolder.md - 가상 폴더 관리 (22개 기능, 48개 테스트 케이스)

### 주요 성과
- 총 126개의 서비스 기능에 대한 테스트 시나리오 작성
- 약 505개의 개별 테스트 케이스 정의
- 각 서비스의 정상 동작, 에러 처리, 보안, 성능 측면 모두 고려
- 서비스 간 상호작용 및 복합 시나리오 포함

### 향후 활용 방안
1. 각 테스트 시나리오를 기반으로 실제 테스트 코드 작성
2. 서비스 레이어 분리 시 테스트 기준으로 활용
3. Mock 객체 설계 시 참고 자료로 활용
4. API 문서화 및 사용자 가이드 작성 시 참조

#### 수정 작업 완료 (2025-07-16)
1. **Action/ActionResult 타입 명시**
   - 모든 서비스의 기능 목록에 Action과 ActionResult 클래스명 추가
   - 각 기능별로 사용되는 정확한 타입 정보 포함

2. **구현되지 않은 기능 제거**
   - image 서비스: PreloadImage, UnloadImage (NotImplementedError) 제거
   - 각 서비스의 TODO나 미구현 기능 관련 테스트 시나리오 제거
   - 시스템 정책 삭제 등 가정적인 시나리오 제거

3. **불필요한 섹션 제거**
   - 성능 요구사항 섹션 제거
   - 보안 요구사항 섹션 제거
   - 복합 시나리오 중 미래 개선사항 관련 내용 제거
   - 정책 적용 시나리오 등 추측성 내용 제거

4. **현재 구현 상태 반영**
   - 실제 코드베이스의 Action 클래스와 매칭
   - 현재 동작하는 기능만 테스트 시나리오에 포함
   - 각 서비스의 실제 구현 범위에 맞춰 조정