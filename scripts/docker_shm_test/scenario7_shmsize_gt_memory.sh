#!/bin/bash
# 시나리오 7: ShmSize > Memory 설정 시 동작
# 가설: ShmSize가 Memory보다 커도 실제 사용량은 Memory cgroup limit에 제한됨

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 7: ShmSize > Memory 설정 시 동작"
echo "=============================================="
echo ""
echo "가설: ShmSize가 Memory보다 커도 실제 사용은 Memory cgroup limit에 제한됨"
echo ""
echo "설정: memory=1g, shm-size=2g (shm > memory)"
echo ""

echo "테스트 7-1: shm 800MB 할당 (ShmSize 이하, Memory 이하)"
run_test "S7_shm800" "1g" "2g" 800 0
result1=$?
echo ""

echo "테스트 7-2: shm 1200MB 할당 (ShmSize 이하, Memory 초과)"
echo "           → 가설이 맞으면: Memory cgroup에 의해 OOM"
run_test "S7_shm1200" "1g" "2g" 1200 0
result2=$?
echo ""

echo "테스트 7-3: shm 500MB + RAM 400MB (총 900MB, Memory 이하)"
run_test "S7_shm500_ram400" "1g" "2g" 500 400
result3=$?
echo ""

echo "테스트 7-4: shm 500MB + RAM 700MB (총 1.2GB, Memory 초과)"
echo "           → 가설이 맞으면: Memory cgroup에 의해 OOM"
run_test "S7_shm500_ram700" "1g" "2g" 500 700
result4=$?
echo ""

echo "=========================================="
echo "결과 요약:"
echo "  shm 800MB (Memory 이하): $([[ $result1 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 1200MB (Memory 초과): $([[ $result2 -ne 0 ]] && echo "✅ 실패 (예상대로)" || echo "❌ 예상외 성공")"
echo "  shm 500MB + RAM 400MB (0.9GB): $([[ $result3 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 500MB + RAM 700MB (1.2GB): $([[ $result4 -ne 0 ]] && echo "✅ 실패 (예상대로)" || echo "❌ 예상외 성공")"
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -ne 0 ]] && [[ $result3 -eq 0 ]] && [[ $result4 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨${NC}"
    echo -e "${GREEN}      - ShmSize > Memory여도 Memory cgroup이 우선 적용됨${NC}"
    echo -e "${GREEN}      - 실제 사용 가능한 shm은 Memory limit에 제한됨${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 1
fi
