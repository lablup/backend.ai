#!/bin/bash
# 모든 시나리오 테스트 실행

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "Docker ShmSize vs Memory Limit 전체 검증 테스트"
echo "=============================================="
echo ""

# 결과 저장
S1_RESULT=""
S2_RESULT=""
S3_RESULT=""
S4_RESULT=""
S5_RESULT=""
S6_RESULT=""
S7_RESULT=""
S8_RESULT=""

run_scenario() {
    local scenario_num="$1"
    local script_name="$2"

    echo ""
    bash "${SCRIPT_DIR}/${script_name}"
    local exit_code=$?
    echo ""
    echo "----------------------------------------------"

    case $scenario_num in
        1) S1_RESULT=$exit_code ;;
        2) S2_RESULT=$exit_code ;;
        3) S3_RESULT=$exit_code ;;
        4) S4_RESULT=$exit_code ;;
        5) S5_RESULT=$exit_code ;;
        6) S6_RESULT=$exit_code ;;
        7) S7_RESULT=$exit_code ;;
        8) S8_RESULT=$exit_code ;;
    esac
}

# 각 시나리오 실행
run_scenario 1 "scenario1_shm_in_memory.sh"
run_scenario 2 "scenario2_shm_limit.sh"
run_scenario 3 "scenario3_app_invade_shm.sh"
run_scenario 4 "scenario4_shm_used_app_max.sh"
run_scenario 5 "scenario5_shm_unused_app_max.sh"
run_scenario 6 "scenario6_ram_first_then_shm.sh"
run_scenario 7 "scenario7_shmsize_gt_memory.sh"
run_scenario 8 "scenario8_shm_release_reclaim.sh"

# 결과 문자열 생성 함수
get_result_str() {
    local code=$1
    if [[ "$code" == "0" ]]; then
        echo "✅ 가설 검증됨"
    elif [[ "$code" == "1" ]]; then
        echo "❌ 가설 기각"
    else
        echo "⚠️ 확인 필요"
    fi
}

# 최종 결과 요약
echo ""
echo "=============================================="
echo "최종 결과 요약"
echo "=============================================="
echo ""
echo "| 시나리오 | 결과 |"
echo "|----------|------|"
echo "| 시나리오 1 (shm이 Memory에 포함되는지) | $(get_result_str $S1_RESULT) |"
echo "| 시나리오 2 (ShmSize 제한 적용 여부) | $(get_result_str $S2_RESULT) |"
echo "| 시나리오 3 (app이 shm 영역 침범 가능 여부) | $(get_result_str $S3_RESULT) |"
echo "| 시나리오 4 (shm 사용 시 app memory 최대량) | $(get_result_str $S4_RESULT) |"
echo "| 시나리오 5 (shm 미사용 시 app memory 최대량) | $(get_result_str $S5_RESULT) |"
echo "| 시나리오 6 (RAM 먼저 할당 후 shm 할당) | $(get_result_str $S6_RESULT) |"
echo "| 시나리오 7 (ShmSize > Memory 설정 시) | $(get_result_str $S7_RESULT) |"
echo "| 시나리오 8 (shm 해제 후 메모리 반환) | $(get_result_str $S8_RESULT) |"
echo ""

# Backend.AI 로직 판정
echo "=============================================="
echo "Backend.AI 로직 판정"
echo "=============================================="
echo ""
echo "현재 로직: Memory -= shmem, MemorySwap -= shmem, ShmSize = shmem"
echo ""

if [[ "$S1_RESULT" == "0" ]]; then
    echo -e "${GREEN}✅ 현재 로직이 올바릅니다.${NC}"
    echo ""
    echo "검증 결과:"
    echo "  - shm은 Memory limit과 별개로 할당됨"
    echo "  - 사용자가 4GB + 1GB shmem 요청 시:"
    echo "    Memory=3GB, ShmSize=1GB → 실제 3GB RAM + 1GB shm = 4GB 제공"
    echo "  - 의도대로 동작함"
else
    echo -e "${RED}❌ 현재 로직이 틀렸습니다.${NC}"
    echo ""
    echo "검증 결과:"
    echo "  - shm이 Memory limit에 포함됨"
    echo "  - Memory에서 shmem을 빼면 중복 차감됨"
    echo "  - 사용자가 4GB + 1GB shmem 요청 시:"
    echo "    Memory=3GB, ShmSize=1GB → 실제 (3GB - 1GB shm사용) = 2GB만 사용 가능"
    echo ""
    echo "수정 필요: Memory와 MemorySwap에서 shmem을 빼지 말아야 함"
fi
echo ""
echo "=============================================="
