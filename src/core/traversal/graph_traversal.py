"""
Graph traversal algorithms for knowledge graph exploration
"""
import logging
from typing import List, Dict, Optional, Set
from collections import deque
from dataclasses import dataclass

from supabase import Client

from src.shared.config import Config

logger = logging.getLogger("playbook_nexus.traversal")


@dataclass
class TraversalPath:
    """
    Represents a path in the knowledge graph

    Attributes:
        nodes: List of term names in the path
        edges: List of predicates (relationships) connecting the nodes
        depth: Number of hops from start to end
        total_confidence: Product of all edge confidences in the path
    """
    nodes: List[str]
    edges: List[str]
    depth: int
    total_confidence: float

    def __str__(self):
        """Pretty print the path"""
        path_str = " -> ".join(self.nodes)
        edges_str = " -> ".join(self.edges)
        return (f"Path (depth={self.depth}, confidence={self.total_confidence:.3f}):\n"
                f"  Nodes: {path_str}\n"
                f"  Edges: {edges_str}")


class GraphTraversal:
    """
    Graph traversal algorithms for knowledge graph exploration

    Provides BFS, DFS, and other graph algorithms to explore relationships
    in the knowledge graph stored in Supabase.
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize graph traversal

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.table_terms = Config.TABLE_SEMANTIC
        self.table_relations = Config.TABLE_RELATIONS

        logger.info("GraphTraversal initialized")

    def bfs_traversal(
        self,
        start_term: str,
        target_category: Optional[str] = None,
        max_depth: int = 5,
        min_confidence: float = 0.5,
        limit: int = 100
    ) -> List[TraversalPath]:
        """
        Breadth-first search traversal from start term

        Explores the graph level by level, finding shortest paths to nodes
        matching the target category.

        Args:
            start_term: Starting term name (e.g., "더블폭탄")
            target_category: Target category to find (e.g., "resource").
                           If None, explores all reachable nodes.
            max_depth: Maximum search depth (number of hops)
            min_confidence: Minimum edge confidence threshold (0.0-1.0)
            limit: Maximum number of paths to return

        Returns:
            List of TraversalPath objects, sorted by confidence (descending)

        Example:
            >>> traversal = GraphTraversal(supabase_client)
            >>> paths = traversal.bfs_traversal("더블폭탄", "resource", max_depth=3)
            >>> for path in paths[:3]:
            ...     print(path)
        """
        logger.info(f"Starting BFS from '{start_term}' "
                   f"(target_category={target_category}, max_depth={max_depth})")

        # Get start node ID
        start_id = self._get_term_id(start_term)
        if not start_id:
            logger.warning(f"Start term '{start_term}' not found")
            return []

        # BFS initialization
        # Queue: (current_id, node_path, edge_path, depth, cumulative_confidence)
        queue = deque([(start_id, [start_term], [], 0, 1.0)])
        visited: Set[str] = {start_id}
        paths: List[TraversalPath] = []

        while queue and len(paths) < limit:
            current_id, node_path, edge_path, depth, confidence = queue.popleft()

            # Depth limit check
            if depth >= max_depth:
                continue

            # Get outgoing edges from current node
            relations = self._get_outgoing_relations(current_id, min_confidence)

            for rel in relations:
                target_id = rel['target_term_id']
                target_term = rel['target_term']
                target_category_name = rel['target_category']
                predicate = rel['predicate']
                rel_confidence = rel['confidence']

                # Skip if already visited (cycle prevention)
                if target_id in visited:
                    continue

                # Build new path
                new_node_path = node_path + [target_term]
                new_edge_path = edge_path + [predicate]
                new_confidence = confidence * rel_confidence
                new_depth = depth + 1

                # Check if target category reached
                if target_category and target_category_name == target_category:
                    path = TraversalPath(
                        nodes=new_node_path,
                        edges=new_edge_path,
                        depth=new_depth,
                        total_confidence=new_confidence
                    )
                    paths.append(path)
                    logger.debug(f"Found path to {target_category}: {path}")

                # Add to queue for further exploration
                visited.add(target_id)
                queue.append((target_id, new_node_path, new_edge_path,
                            new_depth, new_confidence))

        # Sort by confidence (highest first)
        paths.sort(key=lambda p: p.total_confidence, reverse=True)

        logger.info(f"BFS completed: found {len(paths)} paths")
        return paths[:limit]

    def dfs_traversal(
        self,
        start_term: str,
        max_depth: int = 5,
        min_confidence: float = 0.5
    ) -> Dict[int, List[str]]:
        """
        Depth-first search traversal for impact analysis

        Explores deeply to find all reachable nodes, organized by depth level.
        Useful for understanding the full impact range of a change.

        Args:
            start_term: Starting term name
            max_depth: Maximum search depth
            min_confidence: Minimum edge confidence threshold

        Returns:
            Dictionary mapping depth -> list of reachable terms at that depth
            {0: ['start'], 1: ['neighbor1', 'neighbor2'], 2: [...], ...}

        Example:
            >>> impact = traversal.dfs_traversal("난이도상향", max_depth=3)
            >>> for depth, terms in impact.items():
            ...     print(f"Depth {depth}: {', '.join(terms)}")
        """
        logger.info(f"Starting DFS from '{start_term}' (max_depth={max_depth})")

        start_id = self._get_term_id(start_term)
        if not start_id:
            logger.warning(f"Start term '{start_term}' not found")
            return {}

        visited: Set[str] = set()
        depth_map: Dict[int, List[str]] = {0: [start_term]}

        def dfs_helper(current_id: str, current_term: str, depth: int):
            """Recursive DFS helper"""
            if depth >= max_depth or current_id in visited:
                return

            visited.add(current_id)

            # Get next level nodes
            relations = self._get_outgoing_relations(current_id, min_confidence)

            for rel in relations:
                target_id = rel['target_term_id']
                target_term = rel['target_term']

                # Add to depth map
                next_depth = depth + 1
                if next_depth not in depth_map:
                    depth_map[next_depth] = []

                if target_term not in depth_map[next_depth]:
                    depth_map[next_depth].append(target_term)

                # Recursive call
                dfs_helper(target_id, target_term, next_depth)

        dfs_helper(start_id, start_term, 0)

        logger.info(f"DFS completed: reached {sum(len(v) for v in depth_map.values())} nodes")
        return depth_map

    def _get_term_id(self, term: str) -> Optional[str]:
        """
        Get term ID by term name

        Args:
            term: Term name to look up

        Returns:
            Term UUID or None if not found
        """
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
        """
        Get full term data by ID

        Args:
            term_id: Term UUID

        Returns:
            Dictionary with id, term, category, definition
        """
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
        """
        Get all outgoing edges from a node

        Args:
            term_id: Source term UUID
            min_confidence: Minimum edge confidence

        Returns:
            List of relation dictionaries with target term data
        """
        try:
            # Query relations with joined target term data
            result = self.client.table(self.table_relations)\
                .select("""
                    target_term_id,
                    predicate,
                    confidence,
                    playbook_semantic_terms!target_term_id(term, category)
                """)\
                .eq("source_term_id", term_id)\
                .gte("confidence", min_confidence)\
                .execute()

            # Flatten the joined data structure
            relations = []
            for rel in result.data:
                target_data = rel.get('playbook_semantic_terms')
                if target_data:
                    relations.append({
                        'target_term_id': rel['target_term_id'],
                        'target_term': target_data['term'],
                        'target_category': target_data['category'],
                        'predicate': rel['predicate'],
                        'confidence': rel['confidence']
                    })

            return relations

        except Exception as e:
            logger.error(f"Error getting outgoing relations for '{term_id}': {e}")
            return []

    def find_shortest_path(
        self,
        start_term: str,
        end_term: str,
        max_depth: int = 5,
        min_confidence: float = 0.5
    ) -> Optional[TraversalPath]:
        """
        Find shortest path between two terms

        Uses BFS to find the shortest path (fewest hops) between start and end.

        Args:
            start_term: Starting term name
            end_term: Target term name
            max_depth: Maximum search depth
            min_confidence: Minimum edge confidence

        Returns:
            TraversalPath if path exists, None otherwise

        Example:
            >>> path = traversal.find_shortest_path("더블폭탄", "체리")
            >>> if path:
            ...     print(f"Found path with {path.depth} hops")
        """
        logger.info(f"Finding shortest path: '{start_term}' -> '{end_term}'")

        start_id = self._get_term_id(start_term)
        end_id = self._get_term_id(end_term)

        if not start_id or not end_id:
            logger.warning(f"Start or end term not found")
            return None

        # BFS
        queue = deque([(start_id, [start_term], [], 0, 1.0)])
        visited = {start_id}

        while queue:
            current_id, node_path, edge_path, depth, confidence = queue.popleft()

            # Found target
            if current_id == end_id:
                path = TraversalPath(
                    nodes=node_path,
                    edges=edge_path,
                    depth=depth,
                    total_confidence=confidence
                )
                logger.info(f"Found shortest path: {path}")
                return path

            # Depth limit
            if depth >= max_depth:
                continue

            # Explore neighbors
            relations = self._get_outgoing_relations(current_id, min_confidence)

            for rel in relations:
                target_id = rel['target_term_id']

                if target_id in visited:
                    continue

                visited.add(target_id)
                queue.append((
                    target_id,
                    node_path + [rel['target_term']],
                    edge_path + [rel['predicate']],
                    depth + 1,
                    confidence * rel['confidence']
                ))

        logger.info(f"No path found between '{start_term}' and '{end_term}'")
        return None
