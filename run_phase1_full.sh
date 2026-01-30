#!/bin/bash
# Phase 1 Full Run (all 2,246 documents)
# 개선된 프롬프트로 전체 문서 처리

echo "================================================"
echo "Phase 1 개선 버전 전체 실행"
echo "================================================"
echo ""
echo "📊 실행 계획:"
echo "  - 처리 문서: 2,246개 (전체)"
echo "  - 예상 시간: 30-60분"
echo "  - 예상 비용: \$20-40"
echo ""
echo "🎯 목표:"
echo "  - 용어: 5,000-8,000개"
echo "  - 관계: 2,000-5,000개"
echo "  - 연결률: 30-50%"
echo "  - raw_relations 평균: 2-3개/용어"
echo ""
echo "⚠️ 주의사항:"
echo "  - 반드시 테스트 실행(run_phase1_test.sh) 후 진행"
echo "  - 실행 중 중단하지 마십시오"
echo "  - OpenAI API 키 잔액 확인"
echo ""
echo "------------------------------------------------"
echo ""

# 사용자 확인
read -p "전체 실행을 시작하시겠습니까? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "🚀 Phase 1 전체 실행 중..."
echo "진행률은 로그에서 확인하세요: tail -f logs/playbook.log"
echo ""

# 시작 시간 기록
START_TIME=$(date +%s)

# Phase 1 실행
python3 run_full_pipeline.py --phase 1 --max-pages 2246

# 종료 시간 기록
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "================================================"
echo "Phase 1 전체 실행 완료!"
echo "================================================"
echo ""
echo "⏱️ 소요 시간: ${MINUTES}분 ${SECONDS}초"
echo ""
echo "📊 결과 확인:"
echo ""

# 자동 진단 실행
echo "1. 전체 통계 확인..."
python3 scripts/diagnose_relations.py

echo ""
echo "2. 샘플 용어 확인..."
echo ""
echo "BM 용어 관계:"
python3 scripts/check_term_relations.py BM
echo ""
echo "턴릴레이 용어 관계:"
python3 scripts/check_term_relations.py 턴릴레이
echo ""
echo "빈칸 용어 관계:"
python3 scripts/check_term_relations.py 빈칸

echo ""
echo "------------------------------------------------"
echo ""
echo "🎯 다음 단계:"
echo ""
echo "1. 웹 플랫폼 테스트:"
echo "   python3 -m uvicorn src.api.main:app --reload --port 8000"
echo "   (다른 터미널) cd playbook-web && npm run dev"
echo "   브라우저: http://localhost:3000"
echo ""
echo "2. Phase 2 실행 (관계 구성):"
echo "   python3 run_phase2_only.py"
echo ""
echo "3. 상세 가이드:"
echo "   cat PHASE1_IMPROVEMENTS.md"
echo "   cat TEST_GUIDE.md"
echo ""
