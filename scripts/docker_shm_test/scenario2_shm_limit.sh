#!/bin/bash
# 시나리오 2: shmem 제한(ShmSize)이 실제로 적용되는지 여부
# 가설: ShmSize 제한을 초과하여 /dev/shm에 쓸 수 없다

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 2: ShmSize 제한이 적용되는지"
echo "=============================================="
echo ""
echo "가설: ShmSize 제한을 초과하여 /dev/shm에 쓸 수 없다"
echo ""
echo "설정: memory=4g, shm-size=512m"
echo ""

echo "테스트 2-1: shm 400MB 할당 (제한 이하)"
run_test "S2_shm_limit_under" "4g" "512m" 400 100
result1=$?
echo ""

echo "테스트 2-2: shm 600MB 할당 (제한 초과)"
run_test "S2_shm_limit_over" "4g" "512m" 600 100
result2=$?
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -eq 1 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨 - ShmSize 제한이 적용됨${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
elif [[ $result2 -eq 0 ]]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}결론: 가설 기각 - ShmSize 제한이 적용되지 않음${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 2
fi
