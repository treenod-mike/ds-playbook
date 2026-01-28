#!/usr/bin/env python3
"""
누락된 온톨로지 룰 자동 추가 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def add_missing_rules():
    """Add missing ontology rules based on common patterns"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print("\n" + "="*70)
    print("온톨로지 룰 자동 추가")
    print("="*70 + "\n")

    # Define comprehensive rules (모든 가능한 조합 허용)
    # 카테고리: GameObject, Resource, Mechanic, Content, Condition, System
    # 서술어: triggers, consumes, clears, counters, rewards, requires, contains, unlocks, synergizes_with

    new_rules = [
        # GameObject 관계
        ('gameobject', 'requires', 'content', '게임 오브젝트가 특정 콘텐츠에서 필요함'),
        ('gameobject', 'requires', 'mechanic', '게임 오브젝트가 특정 메카닉을 요구함'),
        ('gameobject', 'triggers', 'mechanic', '게임 오브젝트가 메카닉을 유발함'),
        ('gameobject', 'clears', 'gameobject', '게임 오브젝트가 다른 오브젝트를 제거함'),
        ('gameobject', 'clears', 'condition', '게임 오브젝트가 조건을 해소함'),
        ('gameobject', 'counters', 'gameobject', '게임 오브젝트가 다른 오브젝트에 효과적임'),
        ('gameobject', 'synergizes_with', 'gameobject', '게임 오브젝트 간 시너지'),

        # Resource 관계
        ('resource', 'unlocks', 'content', '리소스로 콘텐츠 해금'),
        ('resource', 'unlocks', 'gameobject', '리소스로 게임 오브젝트 해금'),

        # Mechanic 관계
        ('mechanic', 'triggers', 'content', '메카닉이 콘텐츠를 유발함'),
        ('mechanic', 'triggers', 'gameobject', '메카닉이 게임 오브젝트를 생성함'),
        ('mechanic', 'triggers', 'mechanic', '메카닉이 다른 메카닉을 유발함'),
        ('mechanic', 'requires', 'condition', '메카닉이 조건을 요구함'),
        ('mechanic', 'clears', 'gameobject', '메카닉이 게임 오브젝트를 제거함'),

        # Content 관계
        ('content', 'requires', 'mechanic', '콘텐츠가 메카닉을 요구함'),
        ('content', 'requires', 'resource', '콘텐츠가 리소스를 요구함'),
        ('content', 'requires', 'condition', '콘텐츠가 조건을 요구함'),
        ('content', 'contains', 'gameobject', '콘텐츠가 게임 오브젝트를 포함함'),
        ('content', 'contains', 'mechanic', '콘텐츠가 메카닉을 포함함'),
        ('content', 'contains', 'condition', '콘텐츠가 조건을 포함함'),
        ('content', 'rewards', 'resource', '콘텐츠가 리소스를 보상함'),
        ('content', 'rewards', 'gameobject', '콘텐츠가 게임 오브젝트를 보상함'),
        ('content', 'unlocks', 'content', '콘텐츠가 다른 콘텐츠를 해금함'),
        ('content', 'consumes', 'resource', '콘텐츠가 리소스를 소비함'),

        # Condition 관계
        ('condition', 'requires', 'mechanic', '조건이 메카닉을 요구함'),
        ('condition', 'requires', 'gameobject', '조건이 게임 오브젝트를 요구함'),

        # System 관계
        ('system', 'contains', 'content', '시스템이 콘텐츠를 포함함'),
        ('system', 'contains', 'mechanic', '시스템이 메카닉을 포함함'),
        ('system', 'contains', 'resource', '시스템이 리소스를 포함함'),
        ('system', 'manages', 'resource', '시스템이 리소스를 관리함'),
        ('system', 'tracks', 'condition', '시스템이 조건을 추적함'),
    ]

    print(f"추가할 룰: {len(new_rules)}개\n")

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
        print("✅ 모든 룰이 이미 존재합니다.")
        return

    print(f"신규 추가할 룰: {len(rules_to_add)}개\n")

    # Show rules to add
    print("추가될 룰 목록:")
    for rule in rules_to_add[:10]:  # Show first 10
        print(f"  - {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}")
    if len(rules_to_add) > 10:
        print(f"  ... 외 {len(rules_to_add) - 10}개")

    # Auto-confirm if running in non-interactive mode
    import sys
    if not sys.stdin.isatty():
        response = 'y'
        print("\n자동 실행 모드 - 룰 추가 진행")
    else:
        print("\n진행하시겠습니까? (y/N): ", end="")
        response = input().strip().lower()

    if response != 'y':
        print("취소되었습니다.")
        return

    # Insert rules
    print("\n룰 추가 중...")
    try:
        result = client.table('playbook_ontology_rules').insert(rules_to_add).execute()
        print(f"✅ {len(rules_to_add)}개 룰이 추가되었습니다!")

        print("\n다음 단계:")
        print("  1. Phase 2 재실행: python3 run_phase2_only.py")
        print("  2. 관계 확인: python3 scripts/diagnose_relations.py")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n수동으로 추가하려면 다음 SQL을 실행하세요:")
        print("\nINSERT INTO playbook_ontology_rules (subject_type, predicate, object_type, description) VALUES")
        for i, rule in enumerate(rules_to_add):
            comma = "," if i < len(rules_to_add) - 1 else ";"
            print(f"  ('{rule['subject_type']}', '{rule['predicate']}', '{rule['object_type']}', '{rule['description']}'){comma}")


if __name__ == "__main__":
    add_missing_rules()
