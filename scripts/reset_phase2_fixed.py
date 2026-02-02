#!/usr/bin/env python3
"""
Phase 2 데이터 초기화 스크립트 (개선된 버전)

Supabase RPC 함수를 사용하여 빠르게 삭제합니다.
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
print("🔄 Phase 2 데이터 초기화 (개선 버전)")
print("=" * 70)
print()

# 현재 상태 확인
print("📊 현재 상태:")
print("-" * 70)

try:
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

    # 방법 1: Supabase SQL 에디터 사용 안내
    print()
    print("⚠️  Python에서 대량 삭제가 제한되어 있습니다.")
    print()
    print("다음 방법 중 하나를 선택하세요:")
    print()
    print("=" * 70)
    print("방법 1: Supabase SQL Editor 사용 (가장 빠름)")
    print("=" * 70)
    print()
    print("1. Supabase Dashboard 접속")
    print("2. SQL Editor 메뉴 선택")
    print("3. 다음 SQL 실행:")
    print()
    print("   DELETE FROM playbook_semantic_relations;")
    print()
    print("4. 완료 후 Phase 2 재실행:")
    print("   python3 src/core/processors/ontology_builder.py")
    print()

    print("=" * 70)
    print("방법 2: psql 사용 (로컬에서)")
    print("=" * 70)
    print()
    print("Supabase Database URL이 있다면:")
    print()
    print("   psql 'postgresql://...' -c 'DELETE FROM playbook_semantic_relations;'")
    print()

    print("=" * 70)
    print("방법 3: 작은 배치로 삭제 (느림, 10-20분)")
    print("=" * 70)
    print()

    choice = input("방법 3 (배치 삭제)을 실행하시겠습니까? (yes/no): ")

    if choice.lower() in ['yes', 'y']:
        print()
        print("배치 삭제 시작...")

        deleted_count = 0
        batch_size = 100  # 작은 배치로 변경

        while True:
            try:
                # ID 조회
                response = supabase.table('playbook_semantic_relations')\
                    .select('id')\
                    .limit(batch_size)\
                    .execute()

                if not response.data or len(response.data) == 0:
                    break

                ids = [r['id'] for r in response.data]

                # 하나씩 삭제
                for id_val in ids:
                    try:
                        supabase.table('playbook_semantic_relations')\
                            .delete()\
                            .eq('id', id_val)\
                            .execute()
                        deleted_count += 1

                        if deleted_count % 100 == 0:
                            print(f"  삭제됨: {deleted_count:,}개...")
                    except Exception as e:
                        print(f"  오류 (ID {id_val}): {e}")
                        continue

            except Exception as e:
                print(f"  배치 오류: {e}")
                break

        print()
        print(f"✅ {deleted_count:,}개 관계 삭제 완료!")
    else:
        print()
        print("Supabase Dashboard에서 SQL로 삭제하는 것을 추천합니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)

# 결과 확인
print()
print("-" * 70)
print("📊 현재 상태 확인:")
print("-" * 70)

try:
    relations_count = supabase.table('playbook_semantic_relations').select('id', count='exact').execute()
    print(f"  - playbook_semantic_relations: {relations_count.count:,}개")

    if relations_count.count == 0:
        print()
        print("=" * 70)
        print("✅ Phase 2 초기화 완료!")
        print("=" * 70)
        print()
        print("다음 단계:")
        print("  python3 src/core/processors/ontology_builder.py")
        print()
except Exception as e:
    print(f"확인 중 오류: {e}")

print()
