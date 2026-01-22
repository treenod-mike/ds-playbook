#!/usr/bin/env python3
"""
Quick test script for Playbook Nexus pipeline
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.shared.utils import setup_logging
from src.core.processors.confluence_processor import ConfluenceProcessor
from src.core.processors.semantic_processor import SemanticProcessor
from src.core.loaders.supabase_loader import SupabaseLoader

logger = setup_logging()


def test_connections():
    """Test all API connections"""
    logger.info("=" * 70)
    logger.info("Testing Connections")
    logger.info("=" * 70)

    try:
        # Validate configuration
        Config.validate()
        logger.info("✓ Configuration validated")
    except ValueError as e:
        logger.error(f"✗ Configuration error: {e}")
        return False

    all_passed = True

    # Test Confluence
    try:
        confluence = ConfluenceProcessor()
        if confluence.test_connection():
            logger.info("✓ Confluence API connection successful")
        else:
            logger.error("✗ Confluence API connection failed")
            all_passed = False
    except Exception as e:
        logger.error(f"✗ Confluence API error: {e}")
        all_passed = False

    # Test OpenAI
    try:
        semantic = SemanticProcessor()
        if semantic.test_connection():
            logger.info("✓ OpenAI API connection successful")
        else:
            logger.error("✗ OpenAI API connection failed")
            all_passed = False
    except Exception as e:
        logger.error(f"✗ OpenAI API error: {e}")
        all_passed = False

    # Test Supabase
    try:
        supabase = SupabaseLoader()
        if supabase.test_connection():
            logger.info("✓ Supabase connection successful")
        else:
            logger.error("✗ Supabase connection failed")
            all_passed = False
    except Exception as e:
        logger.error(f"✗ Supabase error: {e}")
        all_passed = False

    logger.info("=" * 70)
    return all_passed


def test_supabase_schema():
    """Test Supabase schema by checking tables and columns"""
    logger.info("=" * 70)
    logger.info("Testing Supabase Schema")
    logger.info("=" * 70)

    try:
        supabase = SupabaseLoader()

        # Check playbook_documents table
        logger.info("\nChecking playbook_documents table...")
        try:
            response = supabase.client.table('playbook_documents').select('*').limit(1).execute()
            logger.info("✓ playbook_documents table exists")
        except Exception as e:
            logger.error(f"✗ playbook_documents table error: {e}")
            return False

        # Check playbook_chunks table
        logger.info("\nChecking playbook_chunks table...")
        try:
            response = supabase.client.table('playbook_chunks').select('*').limit(1).execute()
            logger.info("✓ playbook_chunks table exists")
        except Exception as e:
            logger.error(f"✗ playbook_chunks table error: {e}")
            return False

        # Check playbook_semantic_terms table
        logger.info("\nChecking playbook_semantic_terms table...")
        try:
            response = supabase.client.table('playbook_semantic_terms').select('*').limit(1).execute()
            logger.info("✓ playbook_semantic_terms table exists")

            # Check if frequency and confidence columns exist
            logger.info("\nChecking semantic_terms columns...")

            # Try to query with frequency and confidence
            response = supabase.client.table('playbook_semantic_terms').select(
                'doc_id,term,category,frequency,confidence,relation,evidence,context'
            ).limit(1).execute()

            logger.info("✓ All columns exist (doc_id, term, category, frequency, confidence, relation, evidence, context)")

        except Exception as e:
            logger.error(f"✗ playbook_semantic_terms table error: {e}")
            logger.error("Note: Make sure you ran the migration SQL!")
            return False

        # Get statistics
        logger.info("\nGetting statistics...")
        stats = supabase.get_stats()
        logger.info(f"Current data:")
        logger.info(f"  - Documents: {stats['total_documents']}")
        logger.info(f"  - Chunks: {stats['total_chunks']}")
        logger.info(f"  - Semantic Terms: {stats['total_semantic_terms']}")

        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error(f"Schema test error: {e}")
        return False


def test_chunking():
    """Test improved chunking with sample text"""
    logger.info("=" * 70)
    logger.info("Testing Improved Chunking")
    logger.info("=" * 70)

    sample_text = """
# Architecture Overview

Our system is built on microservices architecture using Kubernetes for orchestration.

## Key Components

The main components include:
- API Gateway for request routing
- Authentication service using OAuth 2.0
- Data processing pipeline with Apache Kafka

## Performance Metrics

We achieve 99.9% uptime with average response time under 100ms. The system handles 10,000 requests per second during peak hours.

### Monitoring

We use Prometheus for metrics collection and Grafana for visualization.
"""

    try:
        semantic = SemanticProcessor()
        chunks = semantic.chunk_text(sample_text, "test_page_001")

        logger.info(f"\nCreated {len(chunks)} chunks from sample text:")
        for i, chunk in enumerate(chunks):
            logger.info(f"\n--- Chunk {i+1} (ID: {chunk.chunk_id}) ---")
            logger.info(f"Size: {len(chunk.content)} chars")
            logger.info(f"Preview: {chunk.content[:100]}...")

        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error(f"Chunking test error: {e}")
        return False


def test_embedding():
    """Test embedding generation"""
    logger.info("=" * 70)
    logger.info("Testing Embedding Generation")
    logger.info("=" * 70)

    test_texts = [
        "Kubernetes is a container orchestration platform.",
        "We use microservices architecture for scalability.",
        "The API gateway handles authentication and routing."
    ]

    try:
        semantic = SemanticProcessor()
        embeddings = semantic.get_embeddings(test_texts)

        logger.info(f"\nGenerated {len(embeddings)} embeddings:")
        for i, emb in enumerate(embeddings):
            if emb:
                logger.info(f"  - Embedding {i+1}: {len(emb)} dimensions")
                logger.info(f"    Sample values: [{emb[0]:.4f}, {emb[1]:.4f}, {emb[2]:.4f}, ...]")
            else:
                logger.error(f"  - Embedding {i+1}: FAILED")

        logger.info("=" * 70)
        return all(emb is not None for emb in embeddings)

    except Exception as e:
        logger.error(f"Embedding test error: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info("Playbook Nexus Pipeline Test Suite")
    logger.info("=" * 70 + "\n")

    results = {}

    # Test 1: Connections
    results['connections'] = test_connections()

    # Test 2: Supabase Schema
    if results['connections']:
        results['schema'] = test_supabase_schema()
    else:
        logger.warning("Skipping schema test due to connection failure")
        results['schema'] = False

    # Test 3: Chunking
    results['chunking'] = test_chunking()

    # Test 4: Embedding
    if results['connections']:
        results['embedding'] = test_embedding()
    else:
        logger.warning("Skipping embedding test due to connection failure")
        results['embedding'] = False

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Results Summary")
    logger.info("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name.upper()}: {status}")

    all_passed = all(results.values())

    if all_passed:
        logger.info("\n🎉 All tests passed! Ready to run pipeline.")
        logger.info("\nNext step: python3 main.py --max-pages 1")
    else:
        logger.error("\n⚠️  Some tests failed. Please check the errors above.")
        logger.error("\nCommon fixes:")
        logger.error("  1. Check .env configuration")
        logger.error("  2. Run supabase_migration.sql in Supabase SQL Editor")
        logger.error("  3. Verify API keys and URLs")

    logger.info("=" * 70 + "\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
