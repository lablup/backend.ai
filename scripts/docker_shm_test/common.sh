#!/bin/bash
# 공통 함수 및 변수 정의

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_test() {
    local test_name="$1"
    local memory="$2"
    local shm_size="$3"
    local shm_alloc_mb="$4"
    local ram_alloc_mb="$5"
    local mode="${6:-default}"  # default, ram_first, release_shm

    echo -e "${YELLOW}테스트: ${test_name}${NC}"
    echo "  설정: --memory=${memory} --shm-size=${shm_size}"
    case "$mode" in
        "ram_first"|"true")
            echo "  동작: RAM ${ram_alloc_mb}MB 할당 후 shm ${shm_alloc_mb}MB 할당"
            ;;
        "release_shm")
            echo "  동작: shm ${shm_alloc_mb}MB 할당 → 해제 → RAM ${ram_alloc_mb}MB 할당"
            ;;
        *)
            echo "  동작: shm ${shm_alloc_mb}MB 할당 후 RAM ${ram_alloc_mb}MB 할당"
            ;;
    esac

    local extra_args=""
    case "$mode" in
        "ram_first"|"true")
            extra_args="--ram-first"
            ;;
        "release_shm")
            extra_args="--release-shm-before-ram"
            ;;
    esac

    result=$(docker run --rm \
        -v "${SCRIPT_DIR}/allocate_memory.py:/test/allocate_memory.py:ro" \
        --memory="${memory}" \
        --memory-swap="${memory}" \
        --shm-size="${shm_size}" \
        python:3.11-slim \
        python3 /test/allocate_memory.py \
            --shm-alloc-mb "${shm_alloc_mb}" \
            --ram-alloc-mb "${ram_alloc_mb}" \
            ${extra_args} \
        2>&1)
    exit_code=$?

    if [[ "$result" == *"SUCCESS"* ]]; then
        echo -e "  결과: ${GREEN}✅ 성공 (exit code: 0)${NC}"
        return 0
    elif [[ "$result" == *"SHM_ALLOC_FAILED"* ]] || [[ $exit_code -eq 135 ]]; then
        # Exit code 135 = 128 + 7 (SIGBUS) - occurs when writing exceeds tmpfs limit
        echo -e "  결과: ${RED}❌ shm 할당 실패 - SIGBUS (exit code: 135 = 128+7)${NC}"
        return 1
    elif [[ "$result" == *"RAM_ALLOC_FAILED"* ]] || [[ $exit_code -eq 137 ]]; then
        # Exit code 137 = 128 + 9 (SIGKILL) - OOM killer
        echo -e "  결과: ${RED}❌ RAM 할당 실패 - SIGKILL (exit code: 137 = 128+9)${NC}"
        return 2
    else
        echo -e "  결과: ${RED}❌ 알 수 없는 오류 (exit code: $exit_code)${NC}"
        echo "  상세: $result"
        return 3
    fi
}
