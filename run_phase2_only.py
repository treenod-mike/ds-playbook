#!/usr/bin/env python3
"""
Phase 2만 실행: 이미 추출된 시맨틱 용어에서 관계 생성

기존에 추출된 시맨틱 용어 (playbook_semantic_terms)와
온톨로지 룰 (playbook_ontology_rules)을 사용하여
관계 (playbook_semantic_relations)를 생성합니다.

Usage:
    python3 run_phase2_only.py
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.processors.ontology_builder import OntologyBuilder

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Phase 2만 실행"""

    logger.info("=" * 70)
    logger.info("Phase 2 Only: 지식 그래프 관계 생성")
    logger.info("=" * 70)
    logger.info("이미 추출된 시맨틱 용어를 사용하여 관계를 생성합니다.")
    logger.info("=" * 70)

    try:
        # OntologyBuilder 생성
        builder = OntologyBuilder()

        # 관계 그래프 생성
        phase2_stats = builder.build_graph()

        # 결과 출력
        logger.info("\n" + "=" * 70)
        logger.info("✅ Phase 2 완료!")
        logger.info("=" * 70)
        logger.info(f"처리된 문서: {phase2_stats['processed_documents']}개")
        logger.info(f"생성된 관계: {phase2_stats['total_relationships']}개")
        logger.info(f"소요 시간: {phase2_stats['elapsed_time']:.2f}s ({phase2_stats['elapsed_time']/60:.1f}m)")
        logger.info("=" * 70)

        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Phase 2 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
