#!/usr/bin/env python3
"""
UX & Advanced Business 온톨로지 룰 추가 스크립트
balances, relieves, maintains, optimizes, diversifies, impacts 관계 타입 추가
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def add_ux_advanced_rules():
    """Add UX & Advanced Business ontology rules"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print("\n" + "="*70)
    print("UX & Advanced Business 온톨로지 룰 추가")
    print("="*70 + "\n")

    # Define new rules
    new_rules = [
        # ==========================================
        # UX & Psychology (Flow Theory)
        # ==========================================

        # balances 관계 (시스템 ↔ 요소 균형)
        ('mechanic', 'balances', 'condition', '메카닉이 조건/상태의 균형을 맞춤 (예: 동적 난이도 -> 유저 실력)'),
        ('system', 'balances', 'condition', '시스템이 조건/상태의 균형을 맞춤 (예: 매칭 시스템 -> 팀 밸런스)'),
        ('mechanic', 'balances', 'mechanic', '메카닉이 다른 메카닉과 균형을 맞춤 (예: 난이도 조절 -> 보상)'),
        ('content', 'balances', 'condition', '컨텐츠가 조건의 균형을 맞춤 (예: 튜토리얼 -> 난이도)'),

        # induces 관계 (조건 → 심리/행동) - 기존 1개에 추가
        ('condition', 'induces', 'ux_factor', '조건이 UX 요소/감정을 유발함 (예: 고난이도 -> 좌절감)'),
        ('mechanic', 'induces', 'ux_factor', '메카닉이 UX 요소/감정을 유발함 (예: 연속 성공 -> 성취감)'),
        ('content', 'induces', 'ux_factor', '컨텐츠가 UX 요소/감정을 유발함 (예: 보스전 -> 긴장감)'),
        ('gameobject', 'induces', 'ux_factor', '게임 오브젝트가 감정을 유발함 (예: 캐릭터 -> 애착)'),

        # relieves 관계 (아이템/시스템 → 부정적 경험 완화)
        ('gameobject', 'relieves', 'ux_factor', '아이템이 부정적 경험을 완화함 (예: 힌트 아이템 -> 막힘)'),
        ('mechanic', 'relieves', 'ux_factor', '메카닉이 부정적 경험을 완화함 (예: 셔플 -> 막힘)'),
        ('content', 'relieves', 'ux_factor', '컨텐츠가 부정적 경험을 완화함 (예: 보상 지급 -> 박탈감)'),
        ('system', 'relieves', 'ux_factor', '시스템이 부정적 경험을 완화함 (예: 난이도 하향 -> 좌절감)'),

        # maintains 관계 (시스템 → 긍정적 상태 유지)
        ('mechanic', 'maintains', 'ux_factor', '메카닉이 긍정적 상태를 유지함 (예: 적절한 난이도 -> 몰입)'),
        ('content', 'maintains', 'ux_factor', '컨텐츠가 긍정적 상태를 유지함 (예: 보상 구조 -> 동기부여)'),
        ('system', 'maintains', 'ux_factor', '시스템이 긍정적 상태를 유지함 (예: 피드백 -> 성취감)'),
        ('gameobject', 'maintains', 'ux_factor', '게임 오브젝트가 긍정적 상태를 유지함 (예: 캐릭터 -> 애착)'),

        # ==========================================
        # Advanced Business Logic
        # ==========================================

        # optimizes 관계 (시스템 → 지표/경험 최적화)
        ('system', 'optimizes', 'metric', '시스템이 지표를 최적화함 (예: 개인화 알고리즘 -> 매출)'),
        ('mechanic', 'optimizes', 'metric', '메카닉이 지표를 최적화함 (예: 튜토리얼 -> 리텐션)'),
        ('content', 'optimizes', 'metric', '컨텐츠가 지표를 최적화함 (예: 추천 시스템 -> 전환율)'),
        ('system', 'optimizes', 'ux_factor', '시스템이 경험을 최적화함 (예: 동적 가격 -> 만족도)'),
        ('mechanic', 'optimizes', 'condition', '메카닉이 조건을 최적화함 (예: 개인화 -> 난이도 밸런스)'),

        # diversifies 관계 (시스템 → 경험/패턴 다양화)
        ('system', 'diversifies', 'ux_factor', '시스템이 경험을 다양화함 (예: AB테스트 -> 유저 경험)'),
        ('mechanic', 'diversifies', 'ux_factor', '메카닉이 경험을 다양화함 (예: 랜덤 보상 -> 경험)'),
        ('content', 'diversifies', 'content', '컨텐츠가 다른 컨텐츠를 다양화함 (예: 개인화 이벤트 -> 콘텐츠)'),
        ('system', 'diversifies', 'content', '시스템이 컨텐츠를 다양화함 (예: AB테스트 -> 상점 UI)'),
        ('mechanic', 'diversifies', 'condition', '메카닉이 조건을 다양화함 (예: 동적 난이도 -> 스테이지 체감)'),

        # impacts 관계 (변경 → 행동/지표, 중립적 인과관계)
        ('system', 'impacts', 'ux_factor', '시스템이 경험에 영향을 미침 (예: UI 변경 -> 조작감)'),
        ('content', 'impacts', 'metric', '컨텐츠가 지표에 영향을 미침 (예: 신규 콘텐츠 -> 유저 행동)'),
        ('mechanic', 'impacts', 'metric', '메카닉이 지표에 영향을 미침 (예: 밸런스 패치 -> 메타 게임)'),
        ('system', 'impacts', 'metric', '시스템이 지표에 영향을 미침 (예: 소셜 기능 -> 상호작용)'),
        ('content', 'impacts', 'ux_factor', '컨텐츠가 경험에 영향을 미침 (예: 이벤트 -> 플레이 패턴)'),

        # ==========================================
        # UX_Factor 역관계 (결과로서의 심리 상태)
        # ==========================================

        # UX_Factor가 다른 요소에 미치는 영향
        ('ux_factor', 'boosts', 'metric', 'UX 요소가 지표를 증폭시킨다 (예: 몰입 -> 리텐션)'),
        ('ux_factor', 'causes', 'metric', 'UX 요소가 지표에 부정적 영향을 준다 (예: 좌절감 -> 이탈률)'),
        ('ux_factor', 'promotes', 'content', 'UX 요소가 구매를 촉진한다 (예: 막힘 -> 힌트 아이템 구매)'),
    ]

    print(f"추가할 UX & Advanced Business 룰: {len(new_rules)}개\n")

    # Check existing rules
    existing_rules = client.table('playbook_ontology_rules')\
        .select('subject_type, predicate, object_type')\
        .execute()

    existing_set = set()
    if existing_rules.data:
        for rule in existing_rules.data:
            key = (rule['subject_type'], rule['predicate'], rule['object_type'])
            existing_set.add(key)

    print(f"기존 룰: {len(existing_set)}개\n")

    # Filter out existing rules
    rules_to_add = []
    for rule in new_rules:
        key = (rule[0], rule[1], rule[2])
        if key not in existing_set:
            rules_to_add.append({
                'subject_type': rule[0],
                'predicate': rule[1],
                'object_type': rule[2],
                'description': rule[3]
            })

    if not rules_to_add:
        print("✅ 모든 UX & Advanced Business 룰이 이미 존재합니다.")
        return

    print(f"신규 추가할 룰: {len(rules_to_add)}개\n")

    # Group by predicate for display
    from collections import defaultdict
    by_pred = defaultdict(list)
    for rule in rules_to_add:
        by_pred[rule['predicate']].append(f"{rule['subject_type']} -> {rule['object_type']}")

    print("추가될 Predicate별 룰:")
    for pred, rules in sorted(by_pred.items()):
        print(f"\n  {pred} ({len(rules)}개):")
        for r in rules[:3]:  # Show first 3
            print(f"    - {r}")
        if len(rules) > 3:
            print(f"    ... 외 {len(rules)-3}개")

    # Auto-confirm if running in non-interactive mode
    if not sys.stdin.isatty():
        response = 'y'
        print("\n자동 실행 모드 - UX & Advanced Business 룰 추가 진행")
    else:
        print(f"\n총 {len(rules_to_add)}개 룰을 추가하시겠습니까? (y/N): ", end="")
        response = input().strip().lower()

    if response != 'y':
        print("취소되었습니다.")
        return

    # Insert rules
    print("\nUX & Advanced Business 룰 추가 중...")
    try:
        result = client.table('playbook_ontology_rules').insert(rules_to_add).execute()
        print(f"✅ {len(rules_to_add)}개 룰이 추가되었습니다!")

        print("\n추가된 관계 타입:")
        print("  🧠 UX & Psychology:")
        print("    - balances: 시스템 ↔ 조건/실력 균형")
        print("    - induces: 조건 → 감정 유발")
        print("    - relieves: 아이템 → 부정 경험 완화")
        print("    - maintains: 시스템 → 긍정 상태 유지")
        print("\n  📊 Advanced Business:")
        print("    - optimizes: 시스템 → 지표/경험 최적화")
        print("    - diversifies: 시스템 → 경험 다양화")
        print("    - impacts: 변경 → 행동/지표 영향")

        # Get final count
        final_result = client.table('playbook_ontology_rules').select('*', count='exact').execute()
        final_count = final_result.count if hasattr(final_result, 'count') else len(final_result.data)

        print(f"\n총 온톨로지 룰: {len(existing_set)}개 → {final_count}개")

        print("\n다음 단계:")
        print("  1. Phase 1 재실행: bash run_phase1_test.sh")
        print("  2. Phase 2 실행: python3 run_phase2_only.py")
        print("  3. 관계 확인: python3 scripts/diagnose_relations.py")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    add_ux_advanced_rules()
