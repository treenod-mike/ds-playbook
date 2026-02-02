#!/usr/bin/env python3
"""
Phase 2 재실행 전 상태 확인
"""
import sys
import os

env_path = '/Users/mike/Desktop/playbook_nexus/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase = create_client(url, key)

print("=" * 70)
print("📊 Phase 2 재실행 전 상태 확인")
print("=" * 70)
print()

# 현재 통계
terms = supabase.table('playbook_semantic_terms').select('id', count='exact').execute()
relations = supabase.table('playbook_semantic_relations').select('id', count='exact').execute()
rules = supabase.table('playbook_ontology_rules').select('id', count='exact').execute()
docs = supabase.table('playbook_documents').select('id', count='exact').execute()

print("현재 데이터:")
print(f"  📄 문서: {docs.count:,}개")
print(f"  🏷️  용어: {terms.count:,}개")
print(f"  🔗 관계: {relations.count:,}개 ← 삭제 대상")
print(f"  📚 온톨로지 규칙: {rules.count}개")
print()

# 예상 소요시간
print("-" * 70)
print("⏱️  예상 소요시간:")
print(f"  - 관계 삭제: ~10초")
print(f"  - Phase 2 재실행: ~10-15분 ({docs.count:,}개 문서)")
print()

print("=" * 70)
print("✅ 준비 완료!")
print("=" * 70)
print()
print("실행:")
print("  python3 scripts/reset_phase2.py")
print()
