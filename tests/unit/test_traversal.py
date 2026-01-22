#!/usr/bin/env python3
"""
Unit tests for graph traversal functionality
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.traversal import GraphTraversal, SubgraphExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bfs_basic():
    """Test basic BFS traversal"""
    logger.info("=" * 70)
    logger.info("Test 1: Basic BFS Traversal")
    logger.info("=" * 70)

    try:
        # Initialize
        supabase = SupabaseLoader()
        traversal = GraphTraversal(supabase.client)

        # Get a sample term from database
        result = supabase.client.table('playbook_semantic_terms')\
            .select("term")\
            .limit(1)\
            .execute()

        if not result.data:
            logger.warning("⚠️ No terms found in database. Run Phase 1 first.")
            return False

        start_term = result.data[0]['term']
        logger.info(f"Starting BFS from: '{start_term}'")

        # Run BFS with max_depth=2
        paths = traversal.bfs_traversal(
            start_term=start_term,
            max_depth=2,
            min_confidence=0.5,
            limit=5
        )

        if paths:
            logger.info(f"✅ Found {len(paths)} paths")
            for i, path in enumerate(paths[:3], 1):
                logger.info(f"\nPath {i}:")
                logger.info(f"  Nodes: {' -> '.join(path.nodes)}")
                logger.info(f"  Edges: {' -> '.join(path.edges)}")
                logger.info(f"  Confidence: {path.total_confidence:.3f}")
        else:
            logger.info("⚠️ No paths found (graph may be sparse)")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_dfs_basic():
    """Test basic DFS traversal"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 2: Basic DFS Traversal")
    logger.info("=" * 70)

    try:
        supabase = SupabaseLoader()
        traversal = GraphTraversal(supabase.client)

        # Get a sample term
        result = supabase.client.table('playbook_semantic_terms')\
            .select("term")\
            .limit(1)\
            .execute()

        if not result.data:
            logger.warning("⚠️ No terms found in database")
            return False

        start_term = result.data[0]['term']
        logger.info(f"Starting DFS from: '{start_term}'")

        # Run DFS
        impact_map = traversal.dfs_traversal(
            start_term=start_term,
            max_depth=3,
            min_confidence=0.5
        )

        if impact_map:
            logger.info("✅ Impact analysis:")
            for depth, terms in sorted(impact_map.items()):
                logger.info(f"  Depth {depth}: {len(terms)} terms")
                if depth < 2:  # Show first 2 levels in detail
                    logger.info(f"    {', '.join(terms[:5])}")
        else:
            logger.info("⚠️ No impact found")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_shortest_path():
    """Test shortest path finding"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 3: Shortest Path")
    logger.info("=" * 70)

    try:
        supabase = SupabaseLoader()
        traversal = GraphTraversal(supabase.client)

        # Get two sample terms
        result = supabase.client.table('playbook_semantic_terms')\
            .select("term")\
            .limit(2)\
            .execute()

        if len(result.data) < 2:
            logger.warning("⚠️ Need at least 2 terms in database")
            return False

        start_term = result.data[0]['term']
        end_term = result.data[1]['term']

        logger.info(f"Finding path: '{start_term}' -> '{end_term}'")

        path = traversal.find_shortest_path(
            start_term=start_term,
            end_term=end_term,
            max_depth=5
        )

        if path:
            logger.info("✅ Path found:")
            logger.info(f"  {path}")
        else:
            logger.info("⚠️ No path found (not connected)")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_subgraph_extraction():
    """Test subgraph extraction"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 4: Subgraph Extraction")
    logger.info("=" * 70)

    try:
        supabase = SupabaseLoader()
        extractor = SubgraphExtractor(supabase.client)

        # Get a sample term
        result = supabase.client.table('playbook_semantic_terms')\
            .select("term")\
            .limit(1)\
            .execute()

        if not result.data:
            logger.warning("⚠️ No terms found in database")
            return False

        center_term = result.data[0]['term']
        logger.info(f"Extracting subgraph around: '{center_term}'")

        # Extract subgraph with radius=1
        subgraph = extractor.extract_subgraph(
            center_term=center_term,
            radius=1,
            min_confidence=0.5
        )

        logger.info(f"✅ Subgraph extracted:")
        logger.info(f"  Nodes: {len(subgraph['nodes'])}")
        logger.info(f"  Edges: {len(subgraph['edges'])}")

        if subgraph['nodes']:
            logger.info(f"\n  Sample nodes:")
            for node in subgraph['nodes'][:3]:
                logger.info(f"    - {node['term']} ({node['category']})")

        if subgraph['edges']:
            logger.info(f"\n  Sample edges:")
            for edge in subgraph['edges'][:3]:
                src_node = next((n for n in subgraph['nodes'] if n['id'] == edge['source']), None)
                tgt_node = next((n for n in subgraph['nodes'] if n['id'] == edge['target']), None)
                if src_node and tgt_node:
                    logger.info(f"    - {src_node['term']} --[{edge['predicate']}]--> {tgt_node['term']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_ego_network():
    """Test ego network extraction"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 5: Ego Network")
    logger.info("=" * 70)

    try:
        supabase = SupabaseLoader()
        extractor = SubgraphExtractor(supabase.client)

        # Get a sample term
        result = supabase.client.table('playbook_semantic_terms')\
            .select("term")\
            .limit(1)\
            .execute()

        if not result.data:
            logger.warning("⚠️ No terms found in database")
            return False

        term = result.data[0]['term']
        logger.info(f"Extracting ego network for: '{term}'")

        # Extract ego network
        ego = extractor.extract_ego_network(
            term=term,
            include_incoming=True,
            include_outgoing=True
        )

        logger.info(f"✅ Ego network extracted:")
        logger.info(f"  Total nodes: {len(ego['nodes'])}")
        logger.info(f"  Total edges: {len(ego['edges'])}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🧪 Graph Traversal Unit Tests")
    logger.info("=" * 70)

    tests = [
        ("BFS Traversal", test_bfs_basic),
        ("DFS Traversal", test_dfs_basic),
        ("Shortest Path", test_shortest_path),
        ("Subgraph Extraction", test_subgraph_extraction),
        ("Ego Network", test_ego_network),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")

    logger.info("\n" + "=" * 70)
    logger.info(f"Result: {passed}/{total} tests passed")
    logger.info("=" * 70)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
