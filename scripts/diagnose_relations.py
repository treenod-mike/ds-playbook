#!/usr/bin/env python3
"""
관계 생성 문제 진단 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def diagnose():
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print("\n" + "="*70)
    print("관계 생성 진단 리포트")
    print("="*70 + "\n")

    # 1. 전체 통계
    terms_count = client.table(Config.TABLE_SEMANTIC).select("id", count="exact").execute()
    relations_count = client.table(Config.TABLE_RELATIONS).select("id", count="exact").execute()
    docs_count = client.table("playbook_documents").select("id", count="exact").execute()

    print("📊 전체 통계:")
    print(f"  - 문서: {docs_count.count}개")
    print(f"  - 용어: {terms_count.count}개")
    print(f"  - 관계: {relations_count.count}개")
    print(f"  - 연결률: {(relations_count.count / terms_count.count * 100):.2f}%")
    print()

    # 2. raw_relations 필드 확인 (LLM이 생성한 원본 관계)
    print("🔍 LLM 생성 관계 확인 (raw_relations 필드):")

    # Sample 10 terms with raw_relations
    terms_with_raw = client.table(Config.TABLE_SEMANTIC)\
        .select("term, raw_relations")\
        .not_.is_("raw_relations", "null")\
        .limit(10)\
        .execute()

    if terms_with_raw.data:
        print(f"  ✓ raw_relations 필드가 있는 용어: {len(terms_with_raw.data)}개 (샘플)")

        total_raw_relations = 0
        for term in terms_with_raw.data:
            if term.get('raw_relations'):
                import json
                try:
                    raw_rels = json.loads(term['raw_relations']) if isinstance(term['raw_relations'], str) else term['raw_relations']
                    total_raw_relations += len(raw_rels)
                except:
                    pass

        print(f"  - 샘플 10개 용어의 raw_relations 평균: {total_raw_relations / len(terms_with_raw.data):.1f}개")

        # Show example
        example = terms_with_raw.data[0]
        print(f"\n  예시: '{example['term']}'")
        try:
            raw_rels = json.loads(example['raw_relations']) if isinstance(example['raw_relations'], str) else example['raw_relations']
            for rel in raw_rels[:3]:
                print(f"    - {rel.get('predicate')} → {rel.get('target')}")
        except Exception as e:
            print(f"    (파싱 오류: {e})")
    else:
        print(f"  ❌ raw_relations 필드가 있는 용어가 없습니다!")
    print()

    # 3. 관계 분포 확인
    print("📈 생성된 관계 분포:")

    # By relation_type
    core_count = client.table(Config.TABLE_RELATIONS)\
        .select("id", count="exact")\
        .eq("relation_type", "CORE")\
        .execute()
    flow_count = client.table(Config.TABLE_RELATIONS)\
        .select("id", count="exact")\
        .eq("relation_type", "FLOW")\
        .execute()
    print(f"  관계 타입별:")
    print(f"    - CORE: {core_count.count}개")
    print(f"    - FLOW: {flow_count.count}개")

    # By weight
    for weight in [1, 2, 3, 4, 5]:
        w_count = client.table(Config.TABLE_RELATIONS)\
            .select("id", count="exact")\
            .eq("weight", weight)\
            .execute()
        if w_count.count > 0:
            print(f"  Weight {weight}: {w_count.count}개")
    print()

    # 4. 관계가 있는 용어 vs 없는 용어
    print("🔗 용어 연결 상태:")

    # Terms with outgoing relations
    terms_with_out = client.table(Config.TABLE_RELATIONS)\
        .select("source_term_id")\
        .execute()

    unique_sources = set([r['source_term_id'] for r in terms_with_out.data])

    # Terms with incoming relations
    terms_with_in = client.table(Config.TABLE_RELATIONS)\
        .select("target_term_id")\
        .execute()

    unique_targets = set([r['target_term_id'] for r in terms_with_in.data])

    connected_terms = unique_sources | unique_targets

    print(f"  - 관계가 있는 용어: {len(connected_terms)}개 ({len(connected_terms)/terms_count.count*100:.1f}%)")
    print(f"  - 관계가 없는 용어: {terms_count.count - len(connected_terms)}개 ({(terms_count.count - len(connected_terms))/terms_count.count*100:.1f}%)")
    print()

    # 5. Phase 2 실행 이력 확인
    print("⏱️ Phase 2 실행 이력:")

    # Check most recent relations
    recent_rels = client.table(Config.TABLE_RELATIONS)\
        .select("created_at")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if recent_rels.data:
        print(f"  - 최근 관계 생성 시각: {recent_rels.data[0]['created_at']}")
    else:
        print(f"  ❌ 관계가 없습니다")
    print()

    # 6. 진단 결과
    print("="*70)
    print("🔍 진단 결과")
    print("="*70)

    issues = []

    if relations_count.count < terms_count.count * 0.05:
        issues.append("⚠️  관계가 너무 적습니다 (용어 대비 5% 미만)")

    if len(connected_terms) < terms_count.count * 0.1:
        issues.append("⚠️  연결된 용어가 너무 적습니다 (전체의 10% 미만)")

    if not terms_with_raw.data:
        issues.append("❌ raw_relations 필드가 비어있습니다 (LLM이 관계를 생성하지 않음)")

    if issues:
        print("\n문제점:")
        for issue in issues:
            print(f"  {issue}")

        print("\n권장 해결 방법:")
        print("  1. Phase 2를 재실행하여 관계 재생성:")
        print("     python3 run_phase2_only.py")
        print()
        print("  2. Phase 2 로그 확인하여 필터링 원인 파악:")
        print("     tail -f logs/playbook.log | grep -E '\\[HUB FILTER|\\[VALIDATION FAIL'")
        print()
        print("  3. 온톨로지 룰 확인:")
        print("     - 너무 엄격한 룰로 인해 대부분 필터링되는지 확인")
        print("     - src/core/rules/ontology_rules.py 검토")
        print()
        print("  4. 허브 노드 필터링 완화 고려:")
        print("     - RelationClassifier.should_filter_abstract_relation()의 threshold 조정")
        print("     - 현재: specificity < 0.3 필터링")
    else:
        print("\n✅ 관계 생성이 정상적으로 보입니다.")

    print()


if __name__ == "__main__":
    diagnose()
