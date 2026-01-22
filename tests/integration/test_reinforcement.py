#!/usr/bin/env python3
"""
Test reinforcement logic by reprocessing existing documents
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.processors.ontology_builder import OntologyBuilder

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test reinforcement by reprocessing documents"""
    logger.info("=" * 70)
    logger.info("Testing Reinforcement Logic")
    logger.info("=" * 70)

    try:
        # Create ontology builder
        builder = OntologyBuilder()

        # Reprocess the same documents to trigger reinforcement
        # Documents from previous test: 71790297109, 292099247
        stats = builder.build_graph(doc_ids=['71790297109', '292099247'])

        logger.info("\n" + "=" * 70)
        logger.info("✅ Reinforcement Test Complete!")
        logger.info("=" * 70)
        logger.info(f"Documents processed: {stats['processed_documents']}")
        logger.info(f"Relationships: {stats['total_relationships']}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
