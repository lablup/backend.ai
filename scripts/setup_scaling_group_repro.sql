-- BA-5608 Scaling Group 에러 재현 셋업
--
-- 이 스크립트는 scaling group access가 keypair-level로 제한된 시나리오를 만듭니다.
-- - admin@lablup.com의 keypair → 'restricted-sg' 접근 가능
-- - user@lablup.com의 keypair → 'restricted-sg' 접근 불가
-- - default 도메인/프로젝트 → 'restricted-sg' 접근 불가
--
-- 이 셋업 후, admin이 owner_access_key=user의 AK로 'restricted-sg'에 세션 생성을
-- 시도하면 "Scaling group 'restricted-sg' is not accessible" 에러 발생.
--
-- 수정 후에도 이 에러는 발생합니다 (의도된 동작 - 실제로 owner가 권한 없음).
-- 프로덕션 케이스에서 "실제 권한이 있어도" 라고 한 것은 admin이 다른 방법
-- (도메인/프로젝트 레벨)으로 권한 부여한 줄 알았는데 실제로는 keypair-level로만
-- 부여되었거나, 부여 자체가 어딘가 누락된 케이스일 가능성이 있습니다.

-- 1. 'restricted-sg' scaling group 생성
INSERT INTO scaling_groups (name, description, is_active, is_public, created_at, scheduler, scheduler_opts, wsproxy_addr, driver, driver_opts, use_host_network)
VALUES (
    'restricted-sg',
    'Test scaling group for BA-5608 reproduction',
    true,
    true,
    NOW(),
    'fifo',
    '{}',
    'http://127.0.0.1:5050',
    'static',
    '{}',
    false
)
ON CONFLICT (name) DO NOTHING;

-- 2. admin@lablup.com의 keypair에만 접근 권한 부여
INSERT INTO sgroups_for_keypairs (scaling_group, access_key)
VALUES ('restricted-sg', 'AKIAIOSFODNN7EXAMPLE')
ON CONFLICT DO NOTHING;

-- 3. 결과 확인
\echo '=== Scaling group access associations ==='
SELECT 'domain' AS type, scaling_group, domain AS target FROM sgroups_for_domains WHERE scaling_group = 'restricted-sg'
UNION ALL
SELECT 'group' AS type, scaling_group, "group"::text AS target FROM sgroups_for_groups WHERE scaling_group = 'restricted-sg'
UNION ALL
SELECT 'keypair' AS type, scaling_group, access_key AS target FROM sgroups_for_keypairs WHERE scaling_group = 'restricted-sg';
