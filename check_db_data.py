#!/usr/bin/env python3
"""
Supabase 데이터베이스 상태 확인 스크립트
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.loaders.supabase_loader import SupabaseLoader

def main():
    print("=" * 70)
    print("Supabase 데이터베이스 상태 확인")
    print("=" * 70)

    supabase = SupabaseLoader()

    # 1. Documents 확인
    print("\n[1] playbook_documents")
    try:
        result = supabase.client.table('playbook_documents').select('id, title').limit(5).execute()
        print(f"   총 문서 수: {len(result.data) if result.data else 0}")
        if result.data:
            print("   최근 문서:")
            for doc in result.data[:3]:
                print(f"     - {doc['id']}: {doc['title']}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    # 2. Chunks 확인
    print("\n[2] playbook_chunks")
    try:
        result = supabase.client.table('playbook_chunks').select('id, doc_id', count='exact').limit(1).execute()
        print(f"   총 청크 수: {result.count if hasattr(result, 'count') else 'N/A'}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    # 3. Semantic Terms 확인
    print("\n[3] playbook_semantic_terms")
    try:
        result = supabase.client.table('playbook_semantic_terms')\
            .select('id, doc_id, term, category, raw_relations', count='exact')\
            .limit(5)\
            .execute()

        total_count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
        print(f"   총 시맨틱 용어 수: {total_count}")

        if result.data:
            print("   최근 용어:")
            for term in result.data[:3]:
                raw_rels = term.get('raw_relations', [])
                rel_count = len(raw_rels) if isinstance(raw_rels, list) else 0
                print(f"     - {term['term']} ({term['category']}) - {rel_count}개 raw relations")
                print(f"       doc_id: {term['doc_id']}")
                if rel_count > 0:
                    print(f"       raw_relations: {raw_rels[:2]}")  # 처음 2개만 출력
        else:
            print("   ⚠️  데이터 없음")

    except Exception as e:
        print(f"   ❌ 오류: {e}")

    # 4. Ontology Rules 확인
    print("\n[4] playbook_ontology_rules")
    try:
        result = supabase.client.table('playbook_ontology_rules')\
            .select('subject_type, predicate, object_type', count='exact')\
            .limit(3)\
            .execute()

        total_count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
        print(f"   총 규칙 수: {total_count}")

        if result.data:
            print("   예시 규칙:")
            for rule in result.data[:3]:
                print(f"     - {rule['subject_type']} --[{rule['predicate']}]--> {rule['object_type']}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    # 5. Semantic Relations 확인
    print("\n[5] playbook_semantic_relations")
    try:
        result = supabase.client.table('playbook_semantic_relations')\
            .select('source_term_id, predicate, target_term_id', count='exact')\
            .limit(3)\
            .execute()

        total_count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
        print(f"   총 관계 수: {total_count}")

        if result.data:
            print("   예시 관계:")
            for rel in result.data[:3]:
                print(f"     - {rel['source_term_id']} --[{rel['predicate']}]--> {rel['target_term_id']}")
        else:
            print("   ⚠️  데이터 없음 (Phase 2 미실행)")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    print("\n" + "=" * 70)
    print("확인 완료")
    print("=" * 70)

if __name__ == "__main__":
    main()
