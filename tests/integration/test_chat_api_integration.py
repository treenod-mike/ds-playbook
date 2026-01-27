#!/usr/bin/env python3
"""
Integration tests for Chat API with GraphRAG
Requires running FastAPI server on localhost:8000
"""
import sys
import logging
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test API health check endpoint"""
    logger.info("=" * 70)
    logger.info("Test 1: Health Check")
    logger.info("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api/health")

        if response.status_code != 200:
            logger.error(f"❌ Expected 200, got {response.status_code}")
            return False

        data = response.json()

        if data["status"] != "healthy":
            logger.error("❌ Health check failed")
            return False

        logger.info("✅ Health check passed")
        logger.info(f"  Status: {data['status']}")
        logger.info(f"  Supabase: {data.get('supabase', 'unknown')}")

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
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지에 대해 설명해줘"}
                ],
                "use_graph": True
            }
        )

        if response.status_code != 200:
            logger.error(f"❌ Expected 200, got {response.status_code}")
            return False

        data = response.json()

        # Check required fields
        required_fields = ["message", "search_process", "graph_data"]
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing '{field}' field")
                return False

        logger.info("✅ Response structure validated")
        logger.info(f"  Message length: {len(data['message'])} chars")
        logger.info(f"  Has search process: {data['search_process'] is not None}")
        logger.info(f"  Has graph data: {data['graph_data'] is not None}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_search_process_steps():
    """Test search process has all 7 required steps"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 3: Search Process Steps (7 steps)")
    logger.info("=" * 70)

    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
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
        required_fields = ["steps", "found_terms", "center_term", "nodes_count", "edges_count"]
        for field in required_fields:
            if field not in search_process:
                logger.error(f"❌ Missing '{field}' field in search_process")
                return False

        steps = search_process["steps"]
        if len(steps) != 7:
            logger.error(f"❌ Expected 7 steps, got {len(steps)}")
            return False

        # Check step names
        expected_steps = [
            "데이터베이스 조회",
            "데이터 로드 완료",
            "용어 매칭",
            "용어 매칭 완료",
            "관계 그래프 탐색",
            "그래프 추출 완료",
            "컨텍스트 생성"
        ]

        for i, (step, expected_name) in enumerate(zip(steps, expected_steps), 1):
            if step["name"] != expected_name:
                logger.error(f"❌ Step {i} name mismatch: expected '{expected_name}', got '{step['name']}'")
                return False

        logger.info("✅ Search process validated (7 steps)")
        logger.info(f"  Steps: {[s['name'] for s in steps]}")
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
        response = requests.post(
            f"{BASE_URL}/api/chat",
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

        if len(term_keys) != len(unique_keys):
            logger.error(f"❌ Found duplicates: {len(term_keys)} terms, {len(unique_keys)} unique")
            # Show duplicates
            from collections import Counter
            counts = Counter(term_keys)
            duplicates = {k: v for k, v in counts.items() if v > 1}
            logger.error(f"  Duplicates: {duplicates}")
            return False

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
    """Test that ontology rules are loaded (step 2)"""
    logger.info("\n" + "=" * 70)
    logger.info("Test 5: Ontology Rules Loading")
    logger.info("=" * 70)

    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
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
        if "온톨로지 룰" not in load_step["description"]:
            logger.error("❌ Ontology rules not mentioned in load step")
            return False

        # Extract number of rules from description
        import re
        match = re.search(r'온톨로지 룰 (\d+)개', load_step["description"])
        if not match:
            logger.error("❌ Could not find ontology rule count")
            return False

        rule_count = int(match.group(1))
        if rule_count == 0:
            logger.error(f"❌ Expected >0 ontology rules, got {rule_count}")
            return False

        logger.info("✅ Ontology rules loaded")
        logger.info(f"  Rule count: {rule_count}")
        logger.info(f"  Load step: {load_step['description']}")

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
        response = requests.post(
            f"{BASE_URL}/api/chat",
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
            if "nodes" not in graph_data or "edges" not in graph_data:
                logger.error("❌ Missing 'nodes' or 'edges' in graph_data")
                return False

            # Check node structure
            if graph_data["nodes"]:
                node = graph_data["nodes"][0]
                required_node_fields = ["id", "label", "category"]
                for field in required_node_fields:
                    if field not in node:
                        logger.error(f"❌ Node missing '{field}'")
                        return False

            # Check edge structure
            if graph_data["edges"]:
                edge = graph_data["edges"][0]
                required_edge_fields = ["from", "to", "label", "confidence"]
                for field in required_edge_fields:
                    if field not in edge:
                        logger.error(f"❌ Edge missing '{field}'")
                        return False

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
    logger.info("Test 7: Conversation History (Multi-turn)")
    logger.info("=" * 70)

    try:
        # First message
        response1 = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지란 뭐야?"}
                ],
                "use_graph": True
            }
        )

        if response1.status_code != 200:
            logger.error("❌ First message failed")
            return False

        message1 = response1.json()["message"]

        # Second message with history
        response2 = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "스테이지란 뭐야?"},
                    {"role": "assistant", "content": message1},
                    {"role": "user", "content": "그렇다면 미션은?"}
                ],
                "use_graph": True
            }
        )

        if response2.status_code != 200:
            logger.error("❌ Second message failed")
            return False

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
    logger.info("🧪 Chat API Integration Tests")
    logger.info("=" * 70)
    logger.info(f"Target: {BASE_URL}")
    logger.info("=" * 70)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code not in [200, 503]:
            logger.error(f"❌ Server not responding correctly (status: {response.status_code})")
            logger.error("Please start FastAPI server: uvicorn src.api.main:app --reload --port 8000")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to server at http://localhost:8000")
        logger.error("Please start FastAPI server: uvicorn src.api.main:app --reload --port 8000")
        sys.exit(1)

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
