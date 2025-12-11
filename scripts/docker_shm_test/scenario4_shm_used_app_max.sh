#!/bin/bash
# 시나리오 4: shmem 사용 시 app memory 최대 사용량
# 가설: shm이 Memory와 별개라면, shm 사용 중에도 Memory limit까지 RAM 사용 가능

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 4: shm 사용 시 app memory 최대량"
echo "=============================================="
echo ""
echo "가설: shm이 Memory와 별개라면, shm 사용 중에도 Memory limit까지 RAM 사용 가능"
echo ""
echo "설정: memory=2g, shm-size=1g, shm 800MB 사용"
echo ""

echo "테스트 4-1: shm 800MB + RAM 1800MB 할당 (Memory limit 이하)"
run_test "S4_shm800_ram1800" "2g" "1g" 800 1800
result1=$?
echo ""

echo "테스트 4-2: shm 800MB + RAM 2500MB 할당 (Memory limit 초과)"
echo "           → Memory limit이 적용되면: OOM 발생"
run_test "S4_shm800_ram2500" "2g" "1g" 800 2500
result2=$?
echo ""

echo "=========================================="
echo "결과 요약:"
echo "  shm 800MB + RAM 1800MB (limit 이하): $([[ $result1 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 800MB + RAM 2500MB (limit 초과): $([[ $result2 -ne 0 ]] && echo "✅ OOM 발생" || echo "❌ 예상외 성공")"
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨${NC}"
    echo -e "${GREEN}      - shm 사용 시에도 Memory limit(2GB)까지 RAM 사용 가능${NC}"
    echo -e "${GREEN}      - Memory limit 초과 시 OOM 발생${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
elif [[ $result1 -ne 0 ]]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}결론: 가설 기각 - shm 사용량이 Memory limit에서 차감됨${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과 - Memory limit이 적용 안 됨${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 2
fi
