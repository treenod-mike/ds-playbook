"""
Term Entity - Repository Layer

용어 데이터 접근 레이어
"""
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TermRepository:
    """용어 Repository - DB 접근 추상화"""

    def __init__(self, supabase_client):
        """
        Args:
            supabase_client: Supabase 클라이언트 인스턴스
        """
        self.client = supabase_client

    def find_all(self) -> List[Dict[str, Any]]:
        """
        모든 용어 조회

        Returns:
            용어 리스트
        """
        try:
            result = self.client.table('playbook_semantic_terms')\
                .select('id, term, category, document_id')\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch all terms: {e}")
            return []

    def find_by_id(self, term_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 용어 조회

        Args:
            term_id: 용어 ID

        Returns:
            용어 데이터 또는 None
        """
        try:
            result = self.client.table('playbook_semantic_terms')\
                .select('*')\
                .eq('id', term_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to fetch term by id {term_id}: {e}")
            return None

    def find_by_ids(self, term_ids: List[str]) -> List[Dict[str, Any]]:
        """
        여러 ID로 용어 조회

        Args:
            term_ids: 용어 ID 리스트

        Returns:
            용어 리스트
        """
        try:
            result = self.client.table('playbook_semantic_terms')\
                .select('*')\
                .in_('id', term_ids)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch terms by ids: {e}")
            return []

    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리로 용어 조회

        Args:
            category: 용어 카테고리

        Returns:
            용어 리스트
        """
        try:
            result = self.client.table('playbook_semantic_terms')\
                .select('*')\
                .eq('category', category)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch terms by category {category}: {e}")
            return []

    def count(self) -> int:
        """
        전체 용어 개수 조회

        Returns:
            용어 개수
        """
        try:
            result = self.client.table('playbook_semantic_terms')\
                .select('id', count='exact')\
                .execute()
            return result.count if result.count else 0
        except Exception as e:
            logger.error(f"Failed to count terms: {e}")
            return 0
