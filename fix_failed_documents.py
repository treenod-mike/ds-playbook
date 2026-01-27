#!/usr/bin/env python3
"""
실패한 문서 복구 스크립트

긴 문서(2000자+)인데 시맨틱 용어가 없는 문서들의
orphaned chunks를 삭제하고 재처리 준비

Usage:
    python3 fix_failed_documents.py --dry-run  # 미리보기만
    python3 fix_failed_documents.py            # 실제 삭제
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from src.shared.config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='실패한 문서의 orphaned chunks 삭제'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 삭제하지 않고 미리보기만'
    )
    parser.add_argument(
        '--min-length',
        type=int,
        default=2000,
        help='최소 콘텐츠 길이 (기본: 2000자)'
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("실패한 문서 복구 스크립트")
    logger.info("=" * 70)

    # Supabase 연결
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    # 1. 용어 없는 긴 문서 찾기
    logger.info("용어 없는 긴 문서 검색 중...")

    docs_response = client.table('playbook_documents').select('id, title, content_length').execute()
    terms_response = client.table('playbook_semantic_terms').select('doc_id').execute()

    all_doc_ids = set([row['id'] for row in docs_response.data])
    docs_with_terms = set([row['doc_id'] for row in terms_response.data])
    docs_without_terms = all_doc_ids - docs_with_terms

    # 긴 문서 필터링
    failed_docs = [
        row for row in docs_response.data
        if row['id'] in docs_without_terms and row['content_length'] >= args.min_length
    ]

    logger.info(f"발견: {len(failed_docs)}개 문서 (≥{args.min_length}자, 용어 없음)")

    if not failed_docs:
        logger.info("복구할 문서 없음. 종료.")
        return

    # 2. 샘플 표시
    logger.info("\n샘플 10개:")
    for doc in failed_docs[:10]:
        logger.info(f"  - {doc['id']}: {doc['title']} ({doc['content_length']}자)")

    if args.dry_run:
        logger.info("\n[DRY RUN] 실제 삭제는 하지 않습니다.")
        logger.info(f"실제 삭제하려면: python3 fix_failed_documents.py")
        return

    # 3. 사용자 확인
    print("\n" + "=" * 70)
    response = input(f"{len(failed_docs)}개 문서의 청크를 삭제하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("취소됨.")
        return

    # 4. 청크 삭제
    logger.info("\n청크 삭제 중...")
    deleted_total = 0
    success_count = 0

    for idx, doc in enumerate(failed_docs, 1):
        doc_id = doc['id']
        try:
            result = client.table('playbook_chunks').delete().eq('doc_id', doc_id).execute()
            deleted_chunks = len(result.data) if result.data else 0

            if deleted_chunks > 0:
                logger.info(f"[{idx}/{len(failed_docs)}] {doc_id}: {deleted_chunks}개 청크 삭제")
                deleted_total += deleted_chunks
                success_count += 1
            else:
                logger.debug(f"[{idx}/{len(failed_docs)}] {doc_id}: 청크 없음")

        except Exception as e:
            logger.error(f"[{idx}/{len(failed_docs)}] {doc_id}: 에러 - {e}")

    # 5. 결과 요약
    logger.info("\n" + "=" * 70)
    logger.info("✅ 청크 삭제 완료!")
    logger.info("=" * 70)
    logger.info(f"처리된 문서: {success_count}/{len(failed_docs)}개")
    logger.info(f"삭제된 청크: {deleted_total}개")
    logger.info("=" * 70)
    logger.info("\n다음 단계:")
    logger.info("  python3 run_full_pipeline.py --full --max-pages 1000")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
