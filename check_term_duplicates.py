#!/usr/bin/env python3
"""
시맨틱 용어 중복 분석 스크립트
"""
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.loaders.supabase_loader import SupabaseLoader

def main():
    print("=" * 70)
    print("시맨틱 용어 중복 분석")
    print("=" * 70)

    supabase = SupabaseLoader()

    # 모든 시맨틱 용어 가져오기
    result = supabase.client.table('playbook_semantic_terms')\
        .select('id, doc_id, term, category')\
        .execute()

    terms = result.data if result.data else []
    print(f"\n총 {len(terms)}개의 시맨틱 용어")

    # 중복 분석 1: 같은 문서 내 중복 (UNIQUE 제약 위반)
    doc_term_map = defaultdict(list)
    for term in terms:
        key = f"{term['doc_id']}:{term['term']}"
        doc_term_map[key].append(term)

    same_doc_duplicates = {k: v for k, v in doc_term_map.items() if len(v) > 1}

    print(f"\n[1] 같은 문서 내 중복 (UNIQUE 제약 위반): {len(same_doc_duplicates)}개")
    if same_doc_duplicates:
        print("   ⚠️  문제 발견! UNIQUE(doc_id, term) 제약이 작동하지 않음")
        for key, dups in list(same_doc_duplicates.items())[:3]:
            print(f"   - {key}: {len(dups)}개")
    else:
        print("   ✓ 문제 없음")

    # 중복 분석 2: 다른 문서 간 같은 용어 (정상)
    term_only_map = defaultdict(list)
    for term in terms:
        term_only_map[term['term']].append(term)

    cross_doc_duplicates = {k: v for k, v in term_only_map.items() if len(v) > 1}

    print(f"\n[2] 다른 문서 간 같은 용어 (정상적인 중복): {len(cross_doc_duplicates)}개")
    print("   상위 10개:")
    sorted_dups = sorted(cross_doc_duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for term_name, instances in sorted_dups[:10]:
        doc_count = len(set(t['doc_id'] for t in instances))
        print(f"   - '{term_name}': {len(instances)}개 (문서 {doc_count}개)")

    # 중복 분석 3: 같은 용어 + 다른 카테고리 (문제 가능성)
    term_category_map = defaultdict(lambda: defaultdict(list))
    for term in terms:
        term_category_map[term['term']][term['category']].append(term)

    category_conflicts = {}
    for term_name, categories in term_category_map.items():
        if len(categories) > 1:
            category_conflicts[term_name] = categories

    print(f"\n[3] 같은 용어, 다른 카테고리 (문제 가능성): {len(category_conflicts)}개")
    if category_conflicts:
        print("   상위 5개:")
        for term_name, categories in list(category_conflicts.items())[:5]:
            cat_summary = ", ".join([f"{cat}({len(terms)})" for cat, terms in categories.items()])
            print(f"   - '{term_name}': {cat_summary}")
    else:
        print("   ✓ 문제 없음")

    # 중복 분석 4: 총 용어 수 vs 유니크 용어 수
    unique_terms = set(t['term'] for t in terms)
    print(f"\n[4] 전체 통계")
    print(f"   - 총 용어 수: {len(terms)}")
    print(f"   - 유니크 용어 수: {len(unique_terms)}")
    print(f"   - 평균 중복도: {len(terms) / len(unique_terms):.2f}x")

    print("\n" + "=" * 70)
    print("분석 완료")
    print("=" * 70)

    # 질문에 대한 답변
    print("\n📌 질문: term 덩어리가 중복되는게 정상인가?")
    print("\n답변:")
    print("✅ 정상적인 중복:")
    print("   - 같은 용어가 여러 문서에 등장 (예: '스테이지' 100개 문서에 등장)")
    print("   - 각 문서마다 별도의 term 레코드 생성")
    print("   - 이유: 문서별 context, raw_relations, frequency가 다름")
    print("\n⚠️  비정상적인 중복:")
    print("   - 같은 문서 내에서 같은 용어가 2번 이상 등장")
    print("   - UNIQUE(doc_id, term) 제약 위반")
    print("\n💡 개선 방안:")
    print("   1. 용어 정규화 강화 (현재: normalize_term())")
    print("   2. 글로벌 용어 사전 구축 (term_id 재사용)")
    print("   3. 온톨로지 기반 용어 통합")

if __name__ == "__main__":
    main()
