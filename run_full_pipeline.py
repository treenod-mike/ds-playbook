#!/usr/bin/env python3
"""
전체 파이프라인 실행 스크립트 (Phase 1 + Phase 2 자동 연결)

Phase 1: 문서 처리 및 임베딩 생성
  - Confluence 페이지 가져오기
  - 문서 분류 및 청크 생성
  - 임베딩 생성 및 Supabase 저장
  - 시맨틱 용어 추출

Phase 2: 지식 그래프 구축
  - 문서 간 관계 추출
  - 온톨로지 규칙 검증
  - 관계 저장 및 신뢰도 강화

Usage:
    # 전체 페이지 처리 (Phase 1 + Phase 2)
    python3 run_full_pipeline.py --full

    # 특정 개수만 처리 (테스트용)
    python3 run_full_pipeline.py --max-pages 10

    # 체크포인트 리셋 후 전체 재실행
    python3 run_full_pipeline.py --full --reset-checkpoint

    # Phase 1만 실행 (Phase 2 스킵)
    python3 run_full_pipeline.py --phase1-only
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import Pipeline

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """전체 파이프라인 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Playbook Nexus 전체 파이프라인 (Phase 1 + Phase 2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s --full                    # 전체 페이지 처리 (Phase 1 + Phase 2)
  %(prog)s --max-pages 10            # 10개 페이지만 처리 (Phase 1 + Phase 2)
  %(prog)s --phase1-only             # Phase 1만 실행
  %(prog)s --full --reset-checkpoint # 체크포인트 리셋 후 전체 재실행
        """
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='전체 페이지 처리 (기본: 미처리 페이지만 처리)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='처리할 최대 페이지 수 (테스트용)'
    )

    parser.add_argument(
        '--phase1-only',
        action='store_true',
        help='Phase 1만 실행 (Phase 2 스킵)'
    )

    parser.add_argument(
        '--reset-checkpoint',
        action='store_true',
        help='체크포인트 리셋 (처음부터 재실행)'
    )

    parser.add_argument(
        '--page-ids-file',
        type=str,
        default=None,
        help='페이지 ID 파일 경로 (기본: data/page_ids.txt)'
    )

    args = parser.parse_args()

    # 설정 출력
    logger.info("=" * 70)
    logger.info("Playbook Nexus - 전체 파이프라인 시작")
    logger.info("=" * 70)
    logger.info(f"Phase 1: 문서 처리 및 임베딩 생성")
    logger.info(f"Phase 2: 지식 그래프 구축 {'(스킵)' if args.phase1_only else '(실행)'}")
    logger.info(f"처리 모드: {'전체 페이지' if args.full else '미처리 페이지만'}")

    if args.max_pages:
        logger.info(f"최대 페이지: {args.max_pages}개")

    if args.reset_checkpoint:
        logger.info(f"체크포인트: 리셋")

    logger.info("=" * 70)

    try:
        # Pipeline 생성
        pipeline = Pipeline()

        # 체크포인트 리셋 (요청 시)
        if args.reset_checkpoint:
            logger.info("체크포인트를 리셋합니다...")
            pipeline.checkpoint.reset()
            logger.info("체크포인트 리셋 완료")

        # 전체 파이프라인 실행
        # run_phase2=True로 설정하면 Phase 1 완료 후 자동으로 Phase 2 실행
        pipeline.run(
            page_ids_file=args.page_ids_file,
            skip_existing=not args.full,  # --full이면 재처리
            max_pages=args.max_pages,
            run_phase2=not args.phase1_only  # --phase1-only가 아니면 Phase 2 실행
        )

        logger.info("\n" + "=" * 70)
        logger.info("✅ 전체 파이프라인 완료!")
        logger.info("=" * 70)

        # 최종 통계
        final_stats = pipeline.checkpoint.get_stats()
        supabase_stats = pipeline.supabase.get_stats()

        logger.info("\n📊 최종 통계:")
        logger.info(f"  - 처리된 문서: {final_stats['processed']}개")
        logger.info(f"  - 실패한 문서: {final_stats['failed']}개")
        logger.info(f"  - 총 청크: {final_stats['total_chunks']}개")
        logger.info(f"  - DB 문서: {supabase_stats['total_documents']}개")
        logger.info(f"  - DB 청크: {supabase_stats['total_chunks']}개")
        logger.info(f"  - DB 시맨틱 용어: {supabase_stats['total_semantic_terms']}개")

        if not args.phase1_only:
            logger.info(f"  - DB 관계: {supabase_stats.get('total_relations', 'N/A')}개")

        logger.info("=" * 70)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\n\n파이프라인이 사용자에 의해 중단되었습니다.")
        logger.info("체크포인트가 저장되었으므로, 다음 실행 시 이어서 처리됩니다.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ 파이프라인 실패: {e}", exc_info=True)
        logger.error("\n문제가 지속되면 로그를 확인하거나 --reset-checkpoint 옵션을 사용하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
