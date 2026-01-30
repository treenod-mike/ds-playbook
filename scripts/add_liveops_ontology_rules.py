#!/usr/bin/env python3
"""
LiveOps 온톨로지 룰 추가 스크립트
boosts, drains, promotes, targets 관계 타입 추가
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def add_liveops_rules():
    """Add LiveOps ontology rules (boosts, drains, promotes, targets)"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print("\n" + "="*70)
    print("LiveOps 온톨로지 룰 추가")
    print("="*70 + "\n")

    # Define LiveOps rules
    # boosts: 지표/행동 강화
    # drains: 재화 싱크
    # promotes: 구매 촉진
    # targets: 유저 세그먼트

    new_rules = [
        # boosts 관계 (이벤트/시스템 → 지표/행동)
        ('content', 'boosts', 'system', '이벤트가 시스템 지표를 강화함'),
        ('content', 'boosts', 'mechanic', '컨텐츠가 게임 메카닉 사용을 증가시킴'),
        ('mechanic', 'boosts', 'mechanic', '메카닉이 다른 메카닉 사용을 촉진함'),
        ('system', 'boosts', 'mechanic', '시스템이 특정 행동을 강화함'),

        # drains 관계 (컨텐츠 → 재화 싱크)
        ('content', 'drains', 'resource', '컨텐츠가 재화를 대량 소모함'),
        ('mechanic', 'drains', 'resource', '메카닉이 재화를 소모함'),
        ('gameobject', 'drains', 'resource', '게임 오브젝트가 재화를 소모함'),

        # promotes 관계 (상황 → 구매 촉진)
        ('content', 'promotes', 'content', '컨텐츠가 다른 컨텐츠 구매를 촉진함'),
        ('mechanic', 'promotes', 'content', '메카닉이 컨텐츠 구매를 촉진함'),
        ('condition', 'promotes', 'content', '조건이 컨텐츠 구매를 촉진함'),
        ('condition', 'promotes', 'mechanic', '조건이 메카닉 사용을 촉진함'),
        ('gameobject', 'promotes', 'content', '게임 오브젝트가 컨텐츠 구매를 촉진함'),

        # targets 관계 (상품/이벤트 → 유저 세그먼트)
        ('content', 'targets', 'system', '컨텐츠가 특정 유저 세그먼트를 대상으로 함'),
        ('mechanic', 'targets', 'system', '메카닉이 특정 유저 세그먼트를 대상으로 함'),
        ('content', 'targets', 'segment', '컨텐츠가 특정 유저 세그먼트를 대상으로 함'),
        ('mechanic', 'targets', 'segment', '메카닉이 특정 유저 세그먼트를 대상으로 함'),

        # Segment 역관계 (세그먼트가 컨텐츠를 요구)
        ('segment', 'requires', 'content', '유저 세그먼트가 특정 컨텐츠 대상임'),
    ]

    print(f"추가할 LiveOps 룰: {len(new_rules)}개\n")

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
        print("✅ 모든 LiveOps 룰이 이미 존재합니다.")
        return

    print(f"신규 추가할 LiveOps 룰: {len(rules_to_add)}개\n")

    # Show rules to add
    print("추가될 LiveOps 룰 목록:")
    for rule in rules_to_add:
        print(f"  - {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}")
        print(f"    → {rule['description']}")

    # Auto-confirm if running in non-interactive mode
    if not sys.stdin.isatty():
        response = 'y'
        print("\n자동 실행 모드 - LiveOps 룰 추가 진행")
    else:
        print("\n진행하시겠습니까? (y/N): ", end="")
        response = input().strip().lower()

    if response != 'y':
        print("취소되었습니다.")
        return

    # Insert rules
    print("\nLiveOps 룰 추가 중...")
    try:
        result = client.table('playbook_ontology_rules').insert(rules_to_add).execute()
        print(f"✅ {len(rules_to_add)}개 LiveOps 룰이 추가되었습니다!")

        print("\n추가된 관계 타입:")
        print("  - boosts: 이벤트/시스템 → 지표/행동 강화")
        print("  - drains: 컨텐츠 → 재화 싱크")
        print("  - promotes: 상황 → 구매 촉진")
        print("  - targets: 상품/이벤트 → 유저 세그먼트")

        print("\n다음 단계:")
        print("  1. Phase 1 실행: bash run_phase1_test.sh")
        print("  2. Phase 2 실행: python3 run_phase2_only.py")
        print("  3. 관계 확인: python3 scripts/diagnose_relations.py")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    add_liveops_rules()
