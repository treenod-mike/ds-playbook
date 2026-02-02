#!/usr/bin/env python3
"""
Phase 2 데이터 초기화 스크립트

playbook_semantic_relations 테이블의 모든 관계를 삭제하고
Phase 2를 재실행할 수 있도록 준비합니다.
"""
import sys
import os

# .env 파일 직접 읽기
env_path = '/Users/mike/Desktop/playbook_nexus/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

from supabase import create_client

# Supabase 연결
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')

if not url or not key:
    print("ERROR: SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
    sys.exit(1)

supabase = create_client(url, key)

print("=" * 70)
print("🔄 Phase 2 데이터 초기화")
print("=" * 70)
print()

# 현재 상태 확인
print("📊 현재 상태:")
print("-" * 70)

terms_count = supabase.table('playbook_semantic_terms').select('id', count='exact').execute()
relations_count = supabase.table('playbook_semantic_relations').select('id', count='exact').execute()
rules_count = supabase.table('playbook_ontology_rules').select('id', count='exact').execute()

print(f"  - playbook_semantic_terms: {terms_count.count:,}개 (유지)")
print(f"  - playbook_semantic_relations: {relations_count.count:,}개 (삭제 예정)")
print(f"  - playbook_ontology_rules: {rules_count.count}개 (유지)")
print()

# 확인
print("⚠️  경고: 모든 관계 데이터가 삭제됩니다!")
print(f"   삭제 대상: {relations_count.count:,}개 관계")
print()

response = input("계속하시겠습니까? (yes/no): ")

if response.lower() not in ['yes', 'y']:
    print("❌ 취소되었습니다.")
    sys.exit(0)

print()
print("-" * 70)
print("🗑️  관계 데이터 삭제 중...")
print("-" * 70)

try:
    # 모든 관계 삭제
    # Supabase는 DELETE FROM 구문을 직접 지원하지 않으므로
    # 페이지네이션으로 삭제
    deleted_count = 0
    batch_size = 1000

    while True:
        # 최대 1000개씩 조회
        response = supabase.table('playbook_semantic_relations')\
            .select('id')\
            .limit(batch_size)\
            .execute()

        if not response.data:
            break

        # ID 목록 추출
        ids = [r['id'] for r in response.data]

        # 삭제
        supabase.table('playbook_semantic_relations')\
            .delete()\
            .in_('id', ids)\
            .execute()

        deleted_count += len(ids)
        print(f"  삭제됨: {deleted_count:,}개...")

        if len(response.data) < batch_size:
            break

    print()
    print(f"✅ {deleted_count:,}개 관계 삭제 완료!")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)

# 결과 확인
print()
print("-" * 70)
print("📊 최종 상태:")
print("-" * 70)

terms_count = supabase.table('playbook_semantic_terms').select('id', count='exact').execute()
relations_count = supabase.table('playbook_semantic_relations').select('id', count='exact').execute()

print(f"  - playbook_semantic_terms: {terms_count.count:,}개")
print(f"  - playbook_semantic_relations: {relations_count.count:,}개")
print()

print("=" * 70)
print("✅ Phase 2 초기화 완료!")
print("=" * 70)
print()
print("다음 단계:")
print("  1. Phase 2 재실행: python3 src/core/processors/ontology_builder.py")
print("  2. 또는 특정 문서만: python3 src/core/processors/ontology_builder.py --max-docs 10")
print()
