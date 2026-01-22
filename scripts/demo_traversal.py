#!/usr/bin/env python3
"""
Demo script for graph traversal functionality

이 스크립트는 실제 지식 그래프에서 탐색 기능을 시연합니다.
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.traversal import GraphTraversal, SubgraphExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo():
    """Run traversal demo"""
    logger.info("=" * 70)
    logger.info("Graph Traversal Demo - Playbook Nexus")
    logger.info("=" * 70)

    # Initialize
    logger.info("\n1️⃣ Initializing Supabase connection...")
    supabase = SupabaseLoader()
    traversal = GraphTraversal(supabase.client)
    extractor = SubgraphExtractor(supabase.client)

    logger.info("✅ Connected to Supabase")

    # Get sample terms
    logger.info("\n2️⃣ Fetching sample terms from database...")
    result = supabase.client.table('playbook_semantic_terms')\
        .select("term, category")\
        .limit(5)\
        .execute()

    if not result.data:
        logger.error("❌ No terms found. Please run Phase 1 + Phase 2 first:")
        logger.error("   python3 run_full_pipeline.py --full")
        return

    terms = result.data
    logger.info(f"✅ Found {len(terms)} sample terms:")
    for term in terms:
        logger.info(f"   - {term['term']} ({term['category']})")

    # Demo 1: BFS Traversal
    start_term = terms[0]['term']
    logger.info("\n" + "=" * 70)
    logger.info(f"Demo 1: BFS Traversal from '{start_term}'")
    logger.info("=" * 70)

    paths = traversal.bfs_traversal(
        start_term=start_term,
        max_depth=3,
        min_confidence=0.5,
        limit=5
    )

    if paths:
        logger.info(f"\n✅ Found {len(paths)} paths:\n")
        for i, path in enumerate(paths, 1):
            logger.info(f"Path {i} (confidence: {path.total_confidence:.3f}):")
            logger.info(f"  {' -> '.join(path.nodes)}")
            logger.info(f"  [{' -> '.join(path.edges)}]\n")
    else:
        logger.info("⚠️ No paths found (graph may be sparse)")

    # Demo 2: Subgraph Extraction
    logger.info("\n" + "=" * 70)
    logger.info(f"Demo 2: Subgraph around '{start_term}' (radius=1)")
    logger.info("=" * 70)

    subgraph = extractor.extract_subgraph(
        center_term=start_term,
        radius=1,
        min_confidence=0.5
    )

    logger.info(f"\n✅ Extracted subgraph:")
    logger.info(f"   Nodes: {len(subgraph['nodes'])}")
    logger.info(f"   Edges: {len(subgraph['edges'])}")

    if subgraph['edges']:
        logger.info(f"\n   Sample relationships:")
        for edge in subgraph['edges'][:5]:
            src_node = next((n for n in subgraph['nodes'] if n['id'] == edge['source']), None)
            tgt_node = next((n for n in subgraph['nodes'] if n['id'] == edge['target']), None)
            if src_node and tgt_node:
                logger.info(f"   - {src_node['term']} --[{edge['predicate']}]--> {tgt_node['term']}")

    # Demo 3: Shortest Path
    if len(terms) >= 2:
        term_a = terms[0]['term']
        term_b = terms[1]['term']

        logger.info("\n" + "=" * 70)
        logger.info(f"Demo 3: Shortest Path")
        logger.info(f"  From: '{term_a}'")
        logger.info(f"  To:   '{term_b}'")
        logger.info("=" * 70)

        path = traversal.find_shortest_path(
            start_term=term_a,
            end_term=term_b,
            max_depth=5
        )

        if path:
            logger.info(f"\n✅ Found path (depth: {path.depth}):")
            logger.info(f"   {' -> '.join(path.nodes)}")
        else:
            logger.info("\n⚠️ No path found (terms not connected)")

    # Demo 4: DFS Impact Analysis
    logger.info("\n" + "=" * 70)
    logger.info(f"Demo 4: Impact Analysis from '{start_term}'")
    logger.info("=" * 70)

    impact = traversal.dfs_traversal(
        start_term=start_term,
        max_depth=3,
        min_confidence=0.5
    )

    if impact:
        logger.info(f"\n✅ Impact range by depth:")
        for depth in sorted(impact.keys()):
            logger.info(f"   Level {depth}: {len(impact[depth])} terms")
            if depth < 2 and impact[depth]:
                logger.info(f"     {', '.join(impact[depth][:5])}")
    else:
        logger.info("\n⚠️ No impact found")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Demo Complete! 🎉")
    logger.info("=" * 70)
    logger.info("\nYou can now:")
    logger.info("  1. Use GraphTraversal for path finding and analysis")
    logger.info("  2. Use SubgraphExtractor for visualization data")
    logger.info("  3. Integrate into your application or API")
    logger.info("\nSee docs/TRAVERSAL_DESIGN.md for more details.")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}", exc_info=True)
        sys.exit(1)
