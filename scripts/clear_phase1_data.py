#!/usr/bin/env python3
"""
Phase 1 데이터 초기화 스크립트
playbook_documents, playbook_chunks, playbook_terms, playbook_relations 테이블 데이터 삭제
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from supabase import create_client

def clear_phase1_data():
    """Clear Phase 1 data (documents, chunks, terms, relations)"""
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    print("\n" + "="*70)
    print("Phase 1 데이터 초기화")
    print("="*70 + "\n")

    tables = [
        'playbook_semantic_relations',
        'playbook_semantic_terms',
        'playbook_chunks',
        'playbook_documents'
    ]

    print("삭제할 테이블:")
    for table in tables:
        result = client.table(table).select('*', count='exact').execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"  - {table}: {count}개 레코드")

    print("\n⚠️ 주의: ontology_rules 테이블은 유지됩니다.")

    # Auto-confirm if running in non-interactive mode
    if not sys.stdin.isatty():
        response = 'y'
        print("\n자동 실행 모드 - 데이터 삭제 진행")
    else:
        print("\n진행하시겠습니까? (y/N): ", end="")
        response = input().strip().lower()

    if response != 'y':
        print("취소되었습니다.")
        return

    print("\n데이터 삭제 중...\n")

    for table in tables:
        try:
            # Get all records first
            result = client.table(table).select('*').execute()
            if result.data:
                # Delete all records (use gte with a very old timestamp or similar universal condition)
                if table == 'playbook_documents':
                    client.table(table).delete().gte('doc_id', 0).execute()
                elif table == 'playbook_chunks':
                    client.table(table).delete().gte('doc_id', 0).execute()
                elif table in ['playbook_semantic_terms', 'playbook_semantic_relations']:
                    # For UUID-based tables, delete by selecting all IDs
                    ids = [row['id'] for row in result.data]
                    for i in range(0, len(ids), 100):
                        batch = ids[i:i+100]
                        client.table(table).delete().in_('id', batch).execute()
            print(f"✅ {table} 삭제 완료 ({len(result.data) if result.data else 0}개)")
        except Exception as e:
            print(f"❌ {table} 삭제 실패: {e}")

    print("\n" + "="*70)
    print("Phase 1 데이터 초기화 완료!")
    print("="*70)
    print("\n다음 단계:")
    print("  python3 run_full_pipeline.py --phase1-only --max-pages 100")


if __name__ == "__main__":
    clear_phase1_data()
