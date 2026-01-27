#!/usr/bin/env python3
"""
Unit tests for Chat API with GraphRAG integration
"""
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from src.api.main import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_health_check():
    """Test API health check endpoint"""
    logger.info("=" * 70)
    logger.info("Test 1: Health Check")
    logger.info("=" * 70)

    try:
        client = TestClient(app)
        response = client.get("/api/health")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy", "Health check failed"
        assert "supabase" in data, "Missing supabase status"

        logger.info("✅ Health check passed")
        logger.info(f"  Status: {data['status']}")
        logger.info(f"  Supabase: {data['supabase']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_chat_api_structure():
    """Test chat API response structure"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 2: Chat API Response Structure")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        # Test with a simple question
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Check required fields
        assert "message" in data, "Missing 'message' field"
        assert "search_process" in data, "Missing 'search_process' field"
        assert "graph_data" in data, "Missing 'graph_data' field"

        logger.info("✅ Response structure validated")
        logger.info(f"  Message length: {len(data['message'])} chars")
        logger.info(f"  Has search process: {data['search_process'] is not None}")
        logger.info(f"  Has graph data: {data['graph_data'] is not None}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_search_process_steps():
    """Test search process has all required steps"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 3: Search Process Steps")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        data = response.json()
        search_process = data.get("search_process", {})

        # Check required fields
        assert "steps" in search_process, "Missing 'steps' field"
        assert "found_terms" in search_process, "Missing 'found_terms' field"
        assert "center_term" in search_process, "Missing 'center_term' field"
        assert "nodes_count" in search_process, "Missing 'nodes_count' field"
        assert "edges_count" in search_process, "Missing 'edges_count' field"

        steps = search_process["steps"]
        assert len(steps) == 7, f"Expected 7 steps, got {len(steps)}"

        # Check each step has required fields
        expected_steps = [
            "데이터베이스 조회",
            "데이터 로드 완료",
            "용어 매칭",
            "용어 매칭 완료",
            "관계 그래프 탐색",
            "그래프 추출 완료",
            "컨텍스트 생성"
        ]

        for i, step in enumerate(steps):
            assert "step" in step, f"Step {i} missing 'step' number"
            assert "name" in step, f"Step {i} missing 'name'"
            assert "description" in step, f"Step {i} missing 'description'"
            assert step["name"] == expected_steps[i], f"Step {i+1} name mismatch: expected '{expected_steps[i]}', got '{step['name']}'"

        logger.info("✅ Search process validated")
        logger.info(f"  Total steps: {len(steps)}")
        logger.info(f"  Found terms: {len(search_process['found_terms'])}")
        logger.info(f"  Center term: {search_process['center_term']}")
        logger.info(f"  Nodes: {search_process['nodes_count']}")
        logger.info(f"  Edges: {search_process['edges_count']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_term_deduplication():
    """Test that found_terms has no duplicates"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 4: Term Deduplication")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        data = response.json()
        found_terms = data["search_process"]["found_terms"]

        # Check for duplicates
        term_keys = [f"{t['term']}_{t['category']}" for t in found_terms]
        unique_keys = set(term_keys)

        assert len(term_keys) == len(unique_keys), f"Found duplicates: {len(term_keys)} terms, {len(unique_keys)} unique"

        logger.info("✅ No duplicate terms found")
        logger.info(f"  Total terms: {len(found_terms)}")
        logger.info(f"  Unique terms: {len(unique_keys)}")

        if found_terms:
            logger.info(f"  Sample terms: {[t['term'] for t in found_terms[:3]]}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_ontology_rules_loaded():
    """Test that ontology rules are loaded"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 5: Ontology Rules Loading")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        data = response.json()
        steps = data["search_process"]["steps"]

        # Check step 2 (데이터 로드 완료) mentions ontology rules
        load_step = steps[1]
        assert "온톨로지 룰" in load_step["description"], "Ontology rules not mentioned in load step"

        # Extract number of rules from description
        import re
        match = re.search(r'온톨로지 룰 (\d+)개', load_step["description"])
        assert match, "Could not find ontology rule count"

        rule_count = int(match.group(1))
        assert rule_count > 0, f"Expected >0 ontology rules, got {rule_count}"

        logger.info("✅ Ontology rules loaded")
        logger.info(f"  Rule count: {rule_count}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_graph_data_structure():
    """Test graph_data has correct structure when available"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 6: Graph Data Structure")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        data = response.json()
        graph_data = data.get("graph_data")

        if graph_data:
            assert "nodes" in graph_data, "Missing 'nodes' in graph_data"
            assert "edges" in graph_data, "Missing 'edges' in graph_data"

            # Check node structure
            if graph_data["nodes"]:
                node = graph_data["nodes"][0]
                assert "id" in node, "Node missing 'id'"
                assert "label" in node, "Node missing 'label'"
                assert "category" in node, "Node missing 'category'"

            # Check edge structure
            if graph_data["edges"]:
                edge = graph_data["edges"][0]
                assert "from" in edge, "Edge missing 'from'"
                assert "to" in edge, "Edge missing 'to'"
                assert "label" in edge, "Edge missing 'label'"
                assert "confidence" in edge, "Edge missing 'confidence'"

            logger.info("✅ Graph data structure validated")
            logger.info(f"  Nodes: {len(graph_data['nodes'])}")
            logger.info(f"  Edges: {len(graph_data['edges'])}")
        else:
            logger.info("⚠️  No graph data returned (term may have no relations)")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_conversation_history():
    """Test multi-turn conversation"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 7: Conversation History")
    logger.info("=" * 70)

    try:
        client = TestClient(app)

        # First message
        response1 = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지란 뭐야?"}
                ],
                "use_graph": True
            }
        )

        assert response1.status_code == 200, "First message failed"
        message1 = response1.json()["message"]

        # Second message with history
        response2 = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지란 뭐야?"},
                    {"role": "assistant", "content": message1},
                    {"role": "user", "content": "그렇다면 미션은?"}
                ],
                "use_graph": True
            }
        )

        assert response2.status_code == 200, "Second message failed"

        logger.info("✅ Conversation history handled")
        logger.info(f"  First message length: {len(message1)} chars")
        logger.info(f"  Second response length: {len(response2.json()['message'])} chars")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🧪 Chat API Unit Tests")
    logger.info("=" * 70)

    tests = [
        ("Health Check", test_health_check),
        ("Response Structure", test_chat_api_structure),
        ("Search Process Steps", test_search_process_steps),
        ("Term Deduplication", test_term_deduplication),
        ("Ontology Rules Loading", test_ontology_rules_loaded),
        ("Graph Data Structure", test_graph_data_structure),
        ("Conversation History", test_conversation_history),
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
