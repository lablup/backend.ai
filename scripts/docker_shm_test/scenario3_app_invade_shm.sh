#!/bin/bash
# 시나리오 3: app memory가 shmem 영역을 침범할 수 있는지 여부
# 가설: shm을 안 써도 app memory는 Memory limit까지만 사용 가능하다

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 3: app memory가 shm 영역 침범 가능한지"
echo "=============================================="
echo ""
echo "가설: shm을 안 써도 app memory는 Memory limit까지만 사용 가능"
echo ""
echo "설정: memory=2g, shm-size=1g"
echo "검증: shm 미사용 시 RAM 2.5GB 할당 가능한지"
echo "      → 가설이 맞으면(침범 불가): OOM 발생"
echo "      → 가설이 틀리면(침범 가능): 성공"
echo ""

echo "테스트 3-1: shm 0MB, RAM 1.8GB 할당 (Memory limit 이하)"
run_test "S3_no_shm_ram_1800" "2g" "1g" 0 1800
result1=$?
echo ""

echo "테스트 3-2: shm 0MB, RAM 2.5GB 할당 (Memory limit 초과)"
run_test "S3_no_shm_ram_2500" "2g" "1g" 0 2500
result2=$?
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨 - app은 Memory limit까지만 사용 가능${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
elif [[ $result2 -eq 0 ]]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}결론: 가설 기각 - app이 shm 영역을 침범할 수 있음${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 2
fi
