"""
Relation Entity - Repository Layer

관계 데이터 접근 레이어
"""
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RelationRepository:
    """관계 Repository - DB 접근 추상화"""

    def __init__(self, supabase_client):
        """
        Args:
            supabase_client: Supabase 클라이언트 인스턴스
        """
        self.client = supabase_client

    def find_all(self, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        모든 관계 조회

        Args:
            min_confidence: 최소 신뢰도 (기본: 0.0)

        Returns:
            관계 리스트
        """
        try:
            result = self.client.table('playbook_semantic_relations')\
                .select('*')\
                .gte('confidence', min_confidence)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch all relations: {e}")
            return []

    def find_by_subject(self, subject_id: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Subject ID로 관계 조회 (출발 노드)

        Args:
            subject_id: Subject 용어 ID
            min_confidence: 최소 신뢰도

        Returns:
            관계 리스트
        """
        try:
            result = self.client.table('playbook_semantic_relations')\
                .select('*')\
                .eq('subject_id', subject_id)\
                .gte('confidence', min_confidence)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch relations by subject {subject_id}: {e}")
            return []

    def find_by_object(self, object_id: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Object ID로 관계 조회 (도착 노드)

        Args:
            object_id: Object 용어 ID
            min_confidence: 최소 신뢰도

        Returns:
            관계 리스트
        """
        try:
            result = self.client.table('playbook_semantic_relations')\
                .select('*')\
                .eq('object_id', object_id)\
                .gte('confidence', min_confidence)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch relations by object {object_id}: {e}")
            return []

    def find_by_term(self, term_id: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        특정 용어와 관련된 모든 관계 조회 (subject 또는 object)

        Args:
            term_id: 용어 ID
            min_confidence: 최소 신뢰도

        Returns:
            관계 리스트
        """
        try:
            # Subject로 조회
            subject_relations = self.find_by_subject(term_id, min_confidence)

            # Object로 조회
            object_relations = self.find_by_object(term_id, min_confidence)

            # 중복 제거 후 결합
            all_relations = subject_relations + object_relations
            seen_ids = set()
            unique_relations = []
            for rel in all_relations:
                if rel['id'] not in seen_ids:
                    unique_relations.append(rel)
                    seen_ids.add(rel['id'])

            return unique_relations
        except Exception as e:
            logger.error(f"Failed to fetch relations by term {term_id}: {e}")
            return []

    def find_by_terms(self, term_ids: List[str], min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        여러 용어와 관련된 관계 조회

        Args:
            term_ids: 용어 ID 리스트
            min_confidence: 최소 신뢰도

        Returns:
            관계 리스트
        """
        try:
            # Subject 또는 Object가 term_ids에 포함된 관계 조회
            result = self.client.table('playbook_semantic_relations')\
                .select('*')\
                .or_(f"subject_id.in.({','.join(term_ids)}),object_id.in.({','.join(term_ids)})")\
                .gte('confidence', min_confidence)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch relations by terms: {e}")
            return []

    def count(self) -> int:
        """
        전체 관계 개수 조회

        Returns:
            관계 개수
        """
        try:
            result = self.client.table('playbook_semantic_relations')\
                .select('id', count='exact')\
                .execute()
            return result.count if result.count else 0
        except Exception as e:
            logger.error(f"Failed to count relations: {e}")
            return 0
