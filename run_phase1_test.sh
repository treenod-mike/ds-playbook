#!/bin/bash
# Phase 1 Test Run (100 documents)
# 개선된 프롬프트 검증용

echo "================================================"
echo "Phase 1 개선 버전 테스트 실행"
echo "================================================"
echo ""
echo "📊 실행 계획:"
echo "  - 처리 문서: 100개 (테스트)"
echo "  - 예상 시간: 5-10분"
echo "  - 예상 비용: \$1-2"
echo ""
echo "🎯 검증 목표:"
echo "  - raw_relations 평균: 2.0+ (현재 0.0)"
echo "  - 관계 수: 200+ (현재 202 for 2,246 docs)"
echo "  - 연결률: 30%+ (현재 1.8%)"
echo ""
echo "------------------------------------------------"
echo ""

# 사용자 확인
read -p "테스트를 시작하시겠습니까? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "🚀 Phase 1 실행 중..."
echo ""

# Phase 1 실행
python3 run_full_pipeline.py --phase 1 --max-pages 100

echo ""
echo "================================================"
echo "Phase 1 테스트 완료!"
echo "================================================"
echo ""
echo "📊 결과 확인 방법:"
echo ""
echo "1. 진단 실행:"
echo "   python3 scripts/diagnose_relations.py"
echo ""
echo "2. 특정 용어 확인:"
echo "   python3 scripts/check_term_relations.py BM"
echo "   python3 scripts/check_term_relations.py 턴릴레이"
echo ""
echo "3. 웹 플랫폼 테스트:"
echo "   python3 -m uvicorn src.api.main:app --reload --port 8000"
echo "   (다른 터미널) cd playbook-web && npm run dev"
echo "   브라우저: http://localhost:3000"
echo ""
echo "------------------------------------------------"
echo ""
echo "✅ 테스트 성공 시:"
echo "   bash run_phase1_full.sh  # 전체 2,246개 문서 실행"
echo ""
echo "❌ 개선 필요 시:"
echo "   PHASE1_IMPROVEMENTS.md 참고하여 파라미터 조정"
echo ""
