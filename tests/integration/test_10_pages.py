#!/usr/bin/env python3
"""
10개 페이지만 테스트하는 스크립트 (Phase 1 + Phase 2 포함)
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import Pipeline

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """10개 페이지 테스트 실행"""
    logger.info("=" * 70)
    logger.info("10개 페이지 테스트 시작 (Phase 1 + Phase 2)")
    logger.info("=" * 70)

    try:
        # Pipeline 생성
        pipeline = Pipeline()

        # 10개 페이지만 처리 (Phase 2 포함)
        pipeline.run(
            page_ids_file=None,  # data/page_ids.txt 자동 사용
            skip_existing=True,   # 이미 처리된 페이지 스킵
            max_pages=10,         # 10개만 처리
            run_phase2=True       # Phase 2 (Knowledge Graph 구축) 실행
        )

        logger.info("\n" + "=" * 70)
        logger.info("✅ 10개 페이지 테스트 완료!")
        logger.info("=" * 70)

    except KeyboardInterrupt:
        logger.info("\n테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"테스트 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
