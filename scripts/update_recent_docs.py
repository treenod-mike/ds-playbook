#!/usr/bin/env python3
"""
최근 N개월 문서만 Phase 2 재실행

기존 관계는 유지하고 최신 문서의 관계만 업데이트합니다.
"""
import sys
import os
from datetime import datetime, timedelta, timezone

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
supabase = create_client(url, key)

# 설정
MONTHS = 12  # 최근 N개월

print("=" * 70)
print(f"🔄 최근 {MONTHS}개월 문서 Phase 2 업데이트")
print("=" * 70)
print()

# 날짜 계산
now = datetime.now(timezone.utc)
cutoff_date = now - timedelta(days=MONTHS * 30)
cutoff_str = cutoff_date.isoformat()

print(f"📅 업데이트 대상: {cutoff_date.strftime('%Y-%m-%d')} 이후 문서")
print()

# 최근 문서 조회
print("📄 최근 문서 조회 중...")
all_docs = []
page = 0
page_size = 1000

while True:
    response = supabase.table('playbook_documents')\
        .select('id,title,last_updated')\
        .gte('last_updated', cutoff_str)\
        .range(page * page_size, (page + 1) * page_size - 1)\
        .execute()

    if not response.data:
        break

    all_docs.extend(response.data)
    page += 1

    if len(response.data) < page_size:
        break

print(f"✅ {len(all_docs):,}개 최근 문서 발견")
print()

if len(all_docs) == 0:
    print("업데이트할 문서가 없습니다.")
    sys.exit(0)

# 최근 문서 미리보기
print("📋 최근 10개 문서:")
print("-" * 70)
for i, doc in enumerate(all_docs[:10], 1):
    date_str = doc['last_updated'][:10]
    print(f"{i:2}. [{date_str}] {doc['title'][:50]}")

if len(all_docs) > 10:
    print(f"... 외 {len(all_docs) - 10}개")
print()

# 해당 문서의 기존 관계 삭제
print("-" * 70)
print(f"🗑️  {len(all_docs):,}개 문서의 기존 관계 삭제 중...")
print("-" * 70)

doc_ids = [d['id'] for d in all_docs]
deleted_count = 0

try:
    # 문서 ID 목록으로 용어 조회
    all_terms = []
    page = 0

    while True:
        response = supabase.table('playbook_semantic_terms')\
            .select('id')\
            .in_('doc_id', doc_ids)\
            .range(page * page_size, (page + 1) * page_size - 1)\
            .execute()

        if not response.data:
            break

        all_terms.extend([t['id'] for t in response.data])
        page += 1

        if len(response.data) < page_size:
            break

    print(f"  해당 문서의 용어: {len(all_terms):,}개")

    # 해당 용어의 관계 삭제
    if all_terms:
        # source_term_id로 삭제
        batch_size = 100
        for i in range(0, len(all_terms), batch_size):
            batch = all_terms[i:i+batch_size]

            # 삭제 전 개수 확인
            count_response = supabase.table('playbook_semantic_relations')\
                .select('id', count='exact')\
                .in_('source_term_id', batch)\
                .execute()

            if count_response.count > 0:
                supabase.table('playbook_semantic_relations')\
                    .delete()\
                    .in_('source_term_id', batch)\
                    .execute()

                deleted_count += count_response.count
                print(f"  삭제됨: {deleted_count:,}개...")

    print(f"\n✅ {deleted_count:,}개 관계 삭제 완료")

except Exception as e:
    print(f"❌ 오류: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✅ 기존 관계 삭제 완료!")
print("=" * 70)
print()
print("다음 단계:")
print(f"  Phase 2 재실행 (최근 {MONTHS}개월 문서만):")
print(f"  python3 src/core/processors/ontology_builder.py --doc-ids {' '.join(doc_ids[:5])} ...")
print()
print("  또는 전체 재실행:")
print("  python3 src/core/processors/ontology_builder.py")
print()
