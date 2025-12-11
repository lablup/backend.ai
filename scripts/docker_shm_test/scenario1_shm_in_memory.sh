#!/bin/bash
# 시나리오 1: shmem이 전체 메모리(Memory limit)에 포함되는지 여부
# 가설: shm은 Memory limit과 별개로 동작한다

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 1: shmem이 Memory limit에 포함되는지"
echo "=============================================="
echo ""
echo "가설: shm은 Memory limit과 별개로 동작한다"
echo ""
echo "설정: memory=1g, shm-size=1g"
echo ""

echo "테스트 1-1: shm 900MB + RAM 900MB = 1.8GB 할당"
echo "           → 가설이 맞으면(별개): RAM 900MB < 1GB limit → 성공"
echo "           → 가설이 틀리면(포함): 1.8GB > 1GB limit → OOM"
run_test "S1_shm_separate" "1g" "1g" 900 900
result1=$?
echo ""

echo "테스트 1-2: shm 0MB + RAM 1200MB 할당 (Memory limit 초과)"
echo "           → Memory limit이 적용되면: OOM 발생"
run_test "S1_ram_over_limit" "1g" "1g" 0 1200
result2=$?
echo ""

echo "=========================================="
echo "결과 요약:"
echo "  shm 900MB + RAM 900MB (1.8GB 총합): $([[ $result1 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 0MB + RAM 1200MB (limit 초과):  $([[ $result2 -ne 0 ]] && echo "✅ OOM 발생" || echo "❌ 예상외 성공")"
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨 - shm은 Memory limit과 별개${NC}"
    echo -e "${GREEN}      (shm+RAM 1.8GB 성공, RAM만 1.2GB는 OOM)${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
elif [[ $result1 -ne 0 ]]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}결론: 가설 기각 - shm이 Memory limit에 포함됨${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과 - Memory limit이 적용 안 됨${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 2
fi
