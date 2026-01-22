"""
Subgraph extraction for visualization and focused analysis
"""
import logging
from typing import Dict, List, Optional, Set
from collections import deque

from supabase import Client

from src.shared.config import Config

logger = logging.getLogger("playbook_nexus.traversal")


class SubgraphExtractor:
    """
    Extract subgraphs from the knowledge graph

    Provides functionality to extract focused subsets of the graph
    for visualization, analysis, or export.
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize subgraph extractor

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.table_terms = Config.TABLE_SEMANTIC
        self.table_relations = Config.TABLE_RELATIONS

        logger.info("SubgraphExtractor initialized")

    def extract_subgraph(
        self,
        center_term: str,
        radius: int = 2,
        predicates: Optional[List[str]] = None,
        min_confidence: float = 0.0
    ) -> Dict:
        """
        Extract subgraph around a center node

        Returns all nodes and edges within the specified radius from the
        center node. Useful for visualization and focused analysis.

        Args:
            center_term: Center node term name
            radius: Number of hops from center (1 = immediate neighbors)
            predicates: List of predicates to include (None = all)
            min_confidence: Minimum edge confidence threshold

        Returns:
            Dictionary with 'nodes' and 'edges' lists in JSON format:
            {
                'nodes': [
                    {'id': 'uuid-1', 'term': '더블폭탄', 'category': 'gameobject'},
                    ...
                ],
                'edges': [
                    {
                        'source': 'uuid-1',
                        'target': 'uuid-2',
                        'predicate': 'clears',
                        'confidence': 0.95
                    },
                    ...
                ]
            }

        Example:
            >>> extractor = SubgraphExtractor(supabase_client)
            >>> subgraph = extractor.extract_subgraph("더블폭탄", radius=2)
            >>> print(f"Found {len(subgraph['nodes'])} nodes")
        """
        logger.info(f"Extracting subgraph around '{center_term}' "
                   f"(radius={radius}, predicates={predicates})")

        # Get center node
        center_id = self._get_term_id(center_term)
        if not center_id:
            logger.warning(f"Center term '{center_term}' not found")
            return {'nodes': [], 'edges': []}

        # BFS to collect nodes within radius
        nodes: Dict[str, Dict] = {}
        edges: List[Dict] = []
        visited: Set[str] = set()
        queue = deque([(center_id, 0)])

        while queue:
            current_id, depth = queue.popleft()

            if current_id in visited:
                continue

            if depth > radius:
                continue

            visited.add(current_id)

            # Add node data
            node_data = self._get_term_data(current_id)
            if node_data:
                nodes[current_id] = node_data

            # Get outgoing edges
            out_relations = self._get_outgoing_relations(
                current_id,
                min_confidence
            )

            for rel in out_relations:
                # Filter by predicate if specified
                if predicates and rel['predicate'] not in predicates:
                    continue

                # Add edge
                edges.append({
                    'source': current_id,
                    'target': rel['target_term_id'],
                    'predicate': rel['predicate'],
                    'confidence': rel['confidence']
                })

                # Queue target node for next level
                if depth < radius:
                    queue.append((rel['target_term_id'], depth + 1))

        logger.info(f"Extracted subgraph: {len(nodes)} nodes, {len(edges)} edges")

        return {
            'nodes': list(nodes.values()),
            'edges': edges
        }

    def extract_ego_network(
        self,
        term: str,
        include_incoming: bool = True,
        include_outgoing: bool = True,
        min_confidence: float = 0.0
    ) -> Dict:
        """
        Extract ego network (1-hop neighborhood) of a term

        Returns the focal node plus all its direct neighbors and connections.
        Useful for understanding immediate relationships.

        Args:
            term: Focal term name
            include_incoming: Include incoming edges (term is target)
            include_outgoing: Include outgoing edges (term is source)
            min_confidence: Minimum edge confidence

        Returns:
            Subgraph dictionary with nodes and edges

        Example:
            >>> ego = extractor.extract_ego_network("더블폭탄")
            >>> print(f"Ego network has {len(ego['edges'])} connections")
        """
        logger.info(f"Extracting ego network for '{term}'")

        term_id = self._get_term_id(term)
        if not term_id:
            logger.warning(f"Term '{term}' not found")
            return {'nodes': [], 'edges': []}

        nodes: Dict[str, Dict] = {}
        edges: List[Dict] = []

        # Add focal node
        focal_node = self._get_term_data(term_id)
        if focal_node:
            nodes[term_id] = focal_node

        # Outgoing edges
        if include_outgoing:
            out_relations = self._get_outgoing_relations(term_id, min_confidence)
            for rel in out_relations:
                target_id = rel['target_term_id']

                # Add target node
                if target_id not in nodes:
                    target_data = self._get_term_data(target_id)
                    if target_data:
                        nodes[target_id] = target_data

                # Add edge
                edges.append({
                    'source': term_id,
                    'target': target_id,
                    'predicate': rel['predicate'],
                    'confidence': rel['confidence']
                })

        # Incoming edges
        if include_incoming:
            in_relations = self._get_incoming_relations(term_id, min_confidence)
            for rel in in_relations:
                source_id = rel['source_term_id']

                # Add source node
                if source_id not in nodes:
                    source_data = self._get_term_data(source_id)
                    if source_data:
                        nodes[source_id] = source_data

                # Add edge
                edges.append({
                    'source': source_id,
                    'target': term_id,
                    'predicate': rel['predicate'],
                    'confidence': rel['confidence']
                })

        logger.info(f"Ego network: {len(nodes)} nodes, {len(edges)} edges")

        return {
            'nodes': list(nodes.values()),
            'edges': edges
        }

    def extract_by_predicate(
        self,
        predicate: str,
        limit: int = 100
    ) -> Dict:
        """
        Extract all edges of a specific predicate type

        Useful for analyzing specific types of relationships across the graph.

        Args:
            predicate: Predicate name (e.g., "triggers", "clears")
            limit: Maximum number of edges to return

        Returns:
            Subgraph dictionary with nodes and edges

        Example:
            >>> subgraph = extractor.extract_by_predicate("triggers")
            >>> print(f"Found {len(subgraph['edges'])} trigger relationships")
        """
        logger.info(f"Extracting edges with predicate='{predicate}' (limit={limit})")

        try:
            # Get edges with this predicate
            result = self.client.table(self.table_relations)\
                .select("""
                    source_term_id,
                    target_term_id,
                    predicate,
                    confidence
                """)\
                .eq("predicate", predicate)\
                .limit(limit)\
                .execute()

            edges = result.data

            # Collect unique node IDs
            node_ids = set()
            for edge in edges:
                node_ids.add(edge['source_term_id'])
                node_ids.add(edge['target_term_id'])

            # Get node data
            nodes_dict = {}
            for node_id in node_ids:
                node_data = self._get_term_data(node_id)
                if node_data:
                    nodes_dict[node_id] = node_data

            # Format edges
            formatted_edges = [
                {
                    'source': e['source_term_id'],
                    'target': e['target_term_id'],
                    'predicate': e['predicate'],
                    'confidence': e['confidence']
                }
                for e in edges
            ]

            logger.info(f"Extracted: {len(nodes_dict)} nodes, {len(formatted_edges)} edges")

            return {
                'nodes': list(nodes_dict.values()),
                'edges': formatted_edges
            }

        except Exception as e:
            logger.error(f"Error extracting by predicate '{predicate}': {e}")
            return {'nodes': [], 'edges': []}

    def _get_term_id(self, term: str) -> Optional[str]:
        """Get term ID by term name"""
        try:
            result = self.client.table(self.table_terms)\
                .select("id")\
                .eq("term", term)\
                .limit(1)\
                .execute()

            if result.data:
                return result.data[0]['id']
            return None

        except Exception as e:
            logger.error(f"Error getting term ID for '{term}': {e}")
            return None

    def _get_term_data(self, term_id: str) -> Optional[Dict]:
        """Get full term data by ID"""
        try:
            result = self.client.table(self.table_terms)\
                .select("id, term, category, definition")\
                .eq("id", term_id)\
                .limit(1)\
                .execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting term data for '{term_id}': {e}")
            return None

    def _get_outgoing_relations(
        self,
        term_id: str,
        min_confidence: float
    ) -> List[Dict]:
        """Get all outgoing edges from a node"""
        try:
            result = self.client.table(self.table_relations)\
                .select("target_term_id, predicate, confidence")\
                .eq("source_term_id", term_id)\
                .gte("confidence", min_confidence)\
                .execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting outgoing relations for '{term_id}': {e}")
            return []

    def _get_incoming_relations(
        self,
        term_id: str,
        min_confidence: float
    ) -> List[Dict]:
        """Get all incoming edges to a node"""
        try:
            result = self.client.table(self.table_relations)\
                .select("source_term_id, predicate, confidence")\
                .eq("target_term_id", term_id)\
                .gte("confidence", min_confidence)\
                .execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting incoming relations for '{term_id}': {e}")
            return []
