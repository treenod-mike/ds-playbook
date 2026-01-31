#!/usr/bin/env python3
"""
고아 용어 분석 스크립트
- 관계가 전혀 없는 용어들을 찾아서 분석
- 더미 데이터 vs 실제 중요 용어 구분
"""

from src.infrastructure.supabase_client import SupabaseClient
from collections import defaultdict
import json

def analyze_orphan_terms():
    """고아 용어 분석"""
    supabase = SupabaseClient()

    print("=" * 70)
    print("고아 용어(Orphan Terms) 분석")
    print("=" * 70)
    print()

    # 1. 전체 용어 로드 (페이지네이션)
    print("📊 용어 데이터 로딩 중...")
    all_terms = []
    page = 0
    page_size = 1000

    while True:
        response = supabase.client.table('playbook_semantic_terms').select(
            'id,doc_id,term,category,definition,frequency,confidence,raw_relations'
        ).range(page * page_size, (page + 1) * page_size - 1).execute()

        if not response.data:
            break

        all_terms.extend(response.data)
        page += 1

        if len(response.data) < page_size:
            break

    print(f"✓ 로드 완료: {len(all_terms)}개 용어\n")

    # 2. 관계 데이터 로드
    print("🔗 관계 데이터 로딩 중...")
    relations = supabase.client.table('playbook_graph_relations').select(
        'source_term_id,target_term_id'
    ).execute()

    print(f"✓ 로드 완료: {len(relations.data)}개 관계\n")

    # 3. 관계가 있는 용어 ID 집합
    connected_term_ids = set()
    for rel in relations.data:
        connected_term_ids.add(rel['source_term_id'])
        connected_term_ids.add(rel['target_term_id'])

    # 4. 고아 용어 필터링
    orphan_terms = []
    terms_with_raw_relations = []

    for term in all_terms:
        if term['id'] not in connected_term_ids:
            orphan_terms.append(term)

            # raw_relations가 있는지 확인
            if term.get('raw_relations'):
                terms_with_raw_relations.append(term)

    # 5. 통계 출력
    print("=" * 70)
    print("📈 전체 통계")
    print("=" * 70)
    print(f"총 용어 수: {len(all_terms):,}개")
    print(f"연결된 용어: {len(connected_term_ids):,}개 ({len(connected_term_ids)/len(all_terms)*100:.1f}%)")
    print(f"고아 용어: {len(orphan_terms):,}개 ({len(orphan_terms)/len(all_terms)*100:.1f}%)")
    print(f"  - raw_relations 있음: {len(terms_with_raw_relations):,}개 ({len(terms_with_raw_relations)/len(orphan_terms)*100:.1f}%)")
    print(f"  - raw_relations 없음: {len(orphan_terms) - len(terms_with_raw_relations):,}개")
    print()

    # 6. 카테고리별 고아 용어 분석
    orphan_by_category = defaultdict(int)
    orphan_with_raw_by_category = defaultdict(int)

    for term in orphan_terms:
        orphan_by_category[term['category']] += 1
        if term.get('raw_relations'):
            orphan_with_raw_by_category[term['category']] += 1

    print("=" * 70)
    print("📊 카테고리별 고아 용어 분포")
    print("=" * 70)
    print(f"{'카테고리':<15} {'고아 수':>10} {'raw_relations':>15} {'변환 실패율':>15}")
    print("-" * 70)

    for category in sorted(orphan_by_category.keys(), key=lambda x: orphan_by_category[x], reverse=True):
        total = orphan_by_category[category]
        with_raw = orphan_with_raw_by_category[category]
        failure_rate = (with_raw / total * 100) if total > 0 else 0
        print(f"{category:<15} {total:>10} {with_raw:>15} {failure_rate:>14.1f}%")

    print()

    # 7. 고아 용어 샘플 (raw_relations 있는 것 우선)
    print("=" * 70)
    print("🔍 고아 용어 샘플 (raw_relations 있음)")
    print("=" * 70)
    print("이 용어들은 LLM이 관계를 추출했지만 온톨로지 규칙이 없어서 연결 실패")
    print()

    for i, term in enumerate(terms_with_raw_relations[:20], 1):
        print(f"{i}. [{term['category']}] {term['term']}")
        print(f"   정의: {term.get('definition', 'N/A')[:80]}...")
        print(f"   빈도: {term.get('frequency', 0)}, 신뢰도: {term.get('confidence', 0):.2f}")
        print(f"   raw_relations: {len(term.get('raw_relations', []))}개")

        # raw_relations 샘플 출력
        if term.get('raw_relations'):
            for j, raw_rel in enumerate(term['raw_relations'][:3], 1):
                print(f"      {j}) {raw_rel.get('relation_type', 'N/A')} -> {raw_rel.get('target', 'N/A')}")
        print()

    # 8. 진짜 고아 용어 (raw_relations도 없음)
    real_orphans = [t for t in orphan_terms if not t.get('raw_relations')]

    print("=" * 70)
    print("🚫 진짜 고아 용어 (raw_relations 없음)")
    print("=" * 70)
    print(f"총 {len(real_orphans):,}개 - 이들은 LLM이 관계를 추출하지 못한 용어")
    print()

    # 빈도별 정렬 (높은 빈도 = 중요할 가능성)
    real_orphans_sorted = sorted(real_orphans, key=lambda x: x.get('frequency', 0), reverse=True)

    print("빈도가 높은 진짜 고아 용어 TOP 20:")
    print("-" * 70)

    for i, term in enumerate(real_orphans_sorted[:20], 1):
        print(f"{i}. [{term['category']}] {term['term']}")
        print(f"   빈도: {term.get('frequency', 0)}, 신뢰도: {term.get('confidence', 0):.2f}")
        print(f"   정의: {term.get('definition', 'N/A')[:80]}...")
        print()

    # 9. 권장 사항
    print("=" * 70)
    print("💡 권장 사항")
    print("=" * 70)
    print()
    print(f"1. raw_relations 있는 고아 용어 ({len(terms_with_raw_relations):,}개):")
    print("   → 온톨로지 규칙 추가 필요 (add_missing_ontology_rules.sql 실행)")
    print()
    print(f"2. 진짜 고아 용어 ({len(real_orphans):,}개):")
    print("   a) 빈도 높음 (frequency >= 3): Phase 1 프롬프트 개선 필요")
    print(f"      → {len([t for t in real_orphans if t.get('frequency', 0) >= 3]):,}개")
    print()
    print("   b) 빈도 낮음 (frequency < 3): 노이즈 데이터 가능성")
    print(f"      → {len([t for t in real_orphans if t.get('frequency', 0) < 3]):,}개")
    print("      → 삭제 고려 또는 신뢰도 임계값 상향")
    print()

    # 10. 품질 메트릭
    total_raw_relations = sum(len(t.get('raw_relations', [])) for t in all_terms)
    connected_raw = total_raw_relations - sum(len(t.get('raw_relations', [])) for t in terms_with_raw_relations)

    print("=" * 70)
    print("📊 품질 메트릭")
    print("=" * 70)
    print(f"전체 raw_relations: {total_raw_relations:,}개")
    print(f"성공적으로 변환: {len(relations.data):,}개")
    print(f"변환 실패: {total_raw_relations - len(relations.data):,}개")
    print(f"변환율: {len(relations.data)/total_raw_relations*100:.1f}%")
    print()
    print(f"목표 변환율: 30-50%")
    print(f"현재 갭: {30 - len(relations.data)/total_raw_relations*100:.1f}%p")
    print()

if __name__ == '__main__':
    analyze_orphan_terms()
