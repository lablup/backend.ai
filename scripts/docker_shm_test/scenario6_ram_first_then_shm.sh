#!/bin/bash
# 시나리오 6: RAM 먼저 할당 후 shm 할당
# 가설: 할당 순서와 관계없이 shm + RAM은 Memory cgroup limit 내에서 공유됨

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 6: RAM 먼저 할당 후 shm 할당"
echo "=============================================="
echo ""
echo "가설: 할당 순서와 관계없이 shm + RAM 합계가 Memory limit에 제한됨"
echo ""
echo "설정: memory=2g, shm-size=1g"
echo ""

echo "테스트 6-1: RAM 1100MB 먼저 → shm 800MB (총 1.9GB, limit 이하)"
run_test "S6_ram1100_shm800" "2g" "1g" 800 1100 true
result1=$?
echo ""

echo "테스트 6-2: RAM 1300MB 먼저 → shm 800MB (총 2.1GB, limit 초과)"
echo "           → 가설이 맞으면: shm 할당 시 OOM 또는 실패"
run_test "S6_ram1300_shm800" "2g" "1g" 800 1300 true
result2=$?
echo ""

echo "테스트 6-3: RAM 1800MB 먼저 → shm 400MB (총 2.2GB, limit 초과)"
echo "           → 가설이 맞으면: shm 할당 시 OOM 또는 실패"
run_test "S6_ram1800_shm400" "2g" "1g" 400 1800 true
result3=$?
echo ""

echo "=========================================="
echo "결과 요약:"
echo "  RAM 1100MB → shm 800MB (1.9GB): $([[ $result1 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  RAM 1300MB → shm 800MB (2.1GB): $([[ $result2 -ne 0 ]] && echo "✅ 실패 (예상대로)" || echo "❌ 예상외 성공")"
echo "  RAM 1800MB → shm 400MB (2.2GB): $([[ $result3 -ne 0 ]] && echo "✅ 실패 (예상대로)" || echo "❌ 예상외 성공")"
echo ""

# 시나리오 4와 비교 (shm 먼저 할당)
echo "=========================================="
echo "시나리오 4와 비교 (shm 먼저 할당 시):"
echo ""
echo "테스트 6-4: shm 800MB 먼저 → RAM 1100MB (총 1.9GB, limit 이하)"
run_test "S6_compare_shm800_ram1100" "2g" "1g" 800 1100 false
result4=$?
echo ""

echo "테스트 6-5: shm 800MB 먼저 → RAM 1300MB (총 2.1GB, limit 초과)"
run_test "S6_compare_shm800_ram1300" "2g" "1g" 800 1300 false
result5=$?
echo ""

echo "=========================================="
echo "순서 비교 결과:"
echo "  RAM→shm (1.9GB): $([[ $result1 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm→RAM (1.9GB): $([[ $result4 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  RAM→shm (2.1GB): $([[ $result2 -ne 0 ]] && echo "✅ 실패" || echo "❌ 성공")"
echo "  shm→RAM (2.1GB): $([[ $result5 -ne 0 ]] && echo "✅ 실패" || echo "❌ 성공")"
echo ""

if [[ $result1 -eq 0 ]] && [[ $result2 -ne 0 ]] && [[ $result4 -eq 0 ]] && [[ $result5 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨${NC}"
    echo -e "${GREEN}      - 할당 순서와 관계없이 동일한 결과${NC}"
    echo -e "${GREEN}      - shm + RAM은 Memory cgroup limit 내에서 공유됨${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과 - 순서에 따라 다른 동작?${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 1
fi
