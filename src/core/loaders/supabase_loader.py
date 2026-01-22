"""
Supabase data loader for storing documents and chunks
"""
import logging
from typing import List, Dict, Any

from supabase import create_client, Client

from src.shared.config import Config

logger = logging.getLogger("playbook_nexus.supabase")


class SupabaseLoader:
    """Load data into Supabase tables"""

    def __init__(self, url: str = None, key: str = None):
        """
        Initialize Supabase loader

        Args:
            url: Supabase project URL
            key: Supabase API key
        """
        self.url = url or Config.SUPABASE_URL
        self.key = key or Config.SUPABASE_KEY

        if not all([self.url, self.key]):
            raise ValueError("Supabase credentials not properly configured")

        self.client: Client = create_client(self.url, self.key)

        # Table names
        self.table_documents = Config.TABLE_DOCUMENTS
        self.table_chunks = Config.TABLE_CHUNKS
        self.table_semantic = Config.TABLE_SEMANTIC

    def load_document(self, page_data: Dict[str, Any]) -> bool:
        """
        Load document into playbook_documents table (원본 저장)

        Args:
            page_data: Document data with keys:
                - page_id: document ID
                - title: document title
                - space_key: space key
                - url: document URL
                - content: full content text
                - last_updated: last update timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.table(self.table_documents).upsert({
                "id": page_data["page_id"],
                "title": page_data["title"],
                "space": page_data.get("space_key", "unknown"),
                "url": page_data.get("url", ""),
                "content_length": len(page_data["content"]),
                "last_updated": page_data.get("last_updated")
            }).execute()

            logger.info(f"Successfully loaded document {page_data['page_id']}")
            return True

        except Exception as e:
            logger.error(f"Error loading document {page_data.get('page_id', 'unknown')}: {e}")
            raise

    def load_chunks(self, chunks_data: List[Dict[str, Any]]) -> int:
        """
        Load chunks into playbook_chunks table (청크 + 임베딩 저장)

        Args:
            chunks_data: List of chunk dictionaries with keys:
                - doc_id: document ID
                - chunk_index: chunk index number
                - content: chunk content text (pure text)
                - metadata: JSONB metadata (title, chunk_index, total_chunks, doc_type)
                - embedding: embedding vector
                - char_count: character count

        Returns:
            Number of successfully loaded chunks
        """
        if not chunks_data:
            logger.warning("No chunks to load")
            return 0

        # Prepare batch data with new schema
        batch = []
        for chunk in chunks_data:
            batch.append({
                "doc_id": chunk["doc_id"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],  # Pure text
                "metadata": chunk["metadata"],  # JSONB
                "embedding": chunk["embedding"],
                "char_count": chunk.get("char_count", len(chunk["content"]))
            })

        # Insert in batches of 50 for safety
        total_loaded = 0
        batch_size = 50

        try:
            for i in range(0, len(batch), batch_size):
                sub_batch = batch[i:i + batch_size]
                self.client.table(self.table_chunks).insert(sub_batch).execute()
                total_loaded += len(sub_batch)
                logger.info(f"Loaded batch {i//batch_size + 1}: {len(sub_batch)} chunks")

            logger.info(f"Total loaded: {total_loaded}/{len(chunks_data)} chunks")
            return total_loaded

        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test Supabase connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to query the documents table
            response = self.client.table(self.table_documents).select(
                'id'
            ).limit(1).execute()

            logger.info("Supabase connection successful")
            return True

        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            return False

    def load_semantic_terms(self, terms_data: List[Dict[str, Any]]) -> int:
        """
        Load semantic terms into playbook_semantic_terms table

        Args:
            terms_data: List of term dictionaries with keys:
                - doc_id: document ID
                - term: extracted term/keyword
                - category: term category (person, location, concept, etc.)
                - definition: one-line definition (optional)
                - raw_relations: JSONB array of related terms with type and confidence
                - frequency: occurrence count in document
                - confidence: extraction confidence (0.0-1.0)
                - evidence: JSONB array of chunk IDs where term appears (optional)
                - context: sample context where term is used (optional)

        Returns:
            Number of successfully loaded terms
        """
        if not terms_data:
            logger.warning("No semantic terms to load")
            return 0

        # Prepare batch data
        batch = []
        for term in terms_data:
            batch.append({
                "doc_id": term["doc_id"],
                "term": term["term"],
                "category": term.get("category"),
                "definition": term.get("definition", ""),
                "raw_relations": term.get("raw_relations", []),
                "frequency": term.get("frequency", 1),
                "confidence": term.get("confidence", 0.0)
            })

        # Insert in batches
        total_loaded = 0
        batch_size = 50

        try:
            for i in range(0, len(batch), batch_size):
                sub_batch = batch[i:i + batch_size]

                # Use upsert to handle duplicates (update frequency if term exists)
                self.client.table(self.table_semantic).upsert(
                    sub_batch,
                    on_conflict="doc_id,term"
                ).execute()

                total_loaded += len(sub_batch)
                logger.info(f"Loaded semantic terms batch {i//batch_size + 1}: {len(sub_batch)} terms")

            logger.info(f"Total loaded: {total_loaded}/{len(terms_data)} semantic terms")
            return total_loaded

        except Exception as e:
            logger.error(f"Error loading semantic terms: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored data

        Returns:
            Dictionary with statistics
        """
        try:
            # Count documents
            doc_response = self.client.table(self.table_documents).select(
                'id', count='exact'
            ).execute()

            # Count chunks
            chunk_response = self.client.table(self.table_chunks).select(
                'id', count='exact'
            ).execute()

            # Count semantic terms
            terms_response = self.client.table(self.table_semantic).select(
                'id', count='exact'
            ).execute()

            return {
                'total_documents': doc_response.count if hasattr(doc_response, 'count') else 0,
                'total_chunks': chunk_response.count if hasattr(chunk_response, 'count') else 0,
                'total_semantic_terms': terms_response.count if hasattr(terms_response, 'count') else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'total_semantic_terms': 0,
            }
