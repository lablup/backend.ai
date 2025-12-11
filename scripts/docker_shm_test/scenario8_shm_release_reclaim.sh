#!/bin/bash
# 시나리오 8: shm 해제 후 메모리 반환 확인
# 가설: shm을 해제하면 메모리가 반환되어 RAM으로 사용 가능해짐

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "=============================================="
echo "시나리오 8: shm 해제 후 메모리 반환 확인"
echo "=============================================="
echo ""
echo "가설: shm 해제 시 메모리가 반환되어 RAM으로 재사용 가능"
echo ""
echo "설정: memory=1g, shm-size=1g"
echo ""

echo "테스트 8-1 (기준): shm 700MB 유지 + RAM 500MB (총 1.2GB, limit 초과)"
echo "                   → OOM 발생 예상"
run_test "S8_baseline_shm700_ram500" "1g" "1g" 700 500
result1=$?
echo ""

echo "테스트 8-2: shm 700MB 할당 → 해제 → RAM 500MB 할당"
echo "           → 가설이 맞으면: shm 해제 후 RAM 할당 성공"
run_test "S8_release_shm700_ram500" "1g" "1g" 700 500 release_shm
result2=$?
echo ""

echo "테스트 8-3: shm 700MB 할당 → 해제 → RAM 900MB 할당"
echo "           → 가설이 맞으면: 성공 (shm 해제 후 거의 전체 memory 사용 가능)"
run_test "S8_release_shm700_ram900" "1g" "1g" 700 900 release_shm
result3=$?
echo ""

echo "테스트 8-4: shm 700MB 할당 → 해제 → RAM 1200MB 할당"
echo "           → Memory limit 초과로 OOM 예상"
run_test "S8_release_shm700_ram1200" "1g" "1g" 700 1200 release_shm
result4=$?
echo ""

echo "=========================================="
echo "결과 요약:"
echo "  shm 700MB 유지 + RAM 500MB: $([[ $result1 -ne 0 ]] && echo "✅ OOM (예상대로)" || echo "❌ 예상외 성공")"
echo "  shm 700MB 해제 → RAM 500MB: $([[ $result2 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 700MB 해제 → RAM 900MB: $([[ $result3 -eq 0 ]] && echo "✅ 성공" || echo "❌ 실패")"
echo "  shm 700MB 해제 → RAM 1200MB: $([[ $result4 -ne 0 ]] && echo "✅ OOM (예상대로)" || echo "❌ 예상외 성공")"
echo ""

if [[ $result1 -ne 0 ]] && [[ $result2 -eq 0 ]] && [[ $result3 -eq 0 ]] && [[ $result4 -ne 0 ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}결론: 가설 검증됨${NC}"
    echo -e "${GREEN}      - shm 해제 시 메모리가 정상적으로 반환됨${NC}"
    echo -e "${GREEN}      - 반환된 메모리는 RAM으로 재사용 가능${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}결론: 예상치 못한 결과${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 1
fi
