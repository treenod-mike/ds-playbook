"""
Semantic processing: improved chunking and embedding generation
"""
import logging
import hashlib
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from openai import OpenAI

from src.shared.config import Config
from src.core.rules.prompts import get_prompt, get_synonyms, is_synonym


logger = logging.getLogger("playbook_nexus.semantic")


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    page_id: str
    chunk_index: int
    content: str
    char_start: int
    char_end: int
    chunk_id: Optional[str] = None

    def __post_init__(self):
        """Generate chunk ID after initialization"""
        if not self.chunk_id:
            self.chunk_id = self._generate_chunk_id()

    def _generate_chunk_id(self) -> str:
        """Generate a unique ID for this chunk"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        return f"{self.page_id}_{self.chunk_index}_{content_hash}"


class ImprovedChunker:
    """
    Improved text chunking with header-aware, sentence-preserving logic
    """

    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 2000):
        """
        Initialize improved chunker

        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # Header pattern (Markdown style)
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        # Sentence ending pattern (Korean + English)
        self.sentence_pattern = re.compile(r'([.!?…])\s+|\n{2,}')

    def extract_sections(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Extract sections based on headers

        Args:
            text: Input text

        Returns:
            List of (header, content, start_pos) tuples
        """
        sections = []
        matches = list(self.header_pattern.finditer(text))

        if not matches:
            # No headers found, treat entire text as one section
            return [("", text, 0)]

        for i, match in enumerate(matches):
            header_level = len(match.group(1))
            header_text = match.group(2).strip()
            start_pos = match.start()

            # Find content until next header of same or higher level
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            content = text[match.end():end_pos].strip()

            sections.append((header_text, content, start_pos))

        return sections

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (preserving sentence boundaries)

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text or not text.strip():
            return []

        # Split by sentence endings or double newlines
        sentences = []
        last_end = 0

        for match in self.sentence_pattern.finditer(text):
            sentence = text[last_end:match.end()].strip()
            if sentence:
                sentences.append(sentence)
            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append(remaining)

        return sentences if sentences else [text.strip()]

    def create_chunks_from_sentences(
        self, sentences: List[str], header_context: str = ""
    ) -> List[str]:
        """
        Create chunks from sentences while respecting size limits

        Args:
            sentences: List of sentences
            header_context: Header context to prepend

        Returns:
            List of chunk contents
        """
        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        # Add header context if present
        header_prefix = f"[{header_context}]\n\n" if header_context else ""
        header_size = len(header_prefix)

        for sentence in sentences:
            sentence_size = len(sentence)

            # If single sentence exceeds max size, split it
            if sentence_size > self.max_chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunk_content = header_prefix + " ".join(current_chunk)
                    chunks.append(chunk_content)
                    current_chunk = []
                    current_size = 0

                # Split long sentence into smaller parts
                for i in range(0, len(sentence), self.max_chunk_size - header_size):
                    part = sentence[i:i + self.max_chunk_size - header_size]
                    chunks.append(header_prefix + part)

                continue

            # Check if adding this sentence would exceed max size
            if current_size + sentence_size + header_size > self.max_chunk_size:
                # Save current chunk if it meets minimum size
                if current_size + header_size >= self.min_chunk_size:
                    chunk_content = header_prefix + " ".join(current_chunk)
                    chunks.append(chunk_content)
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    # Current chunk too small, but adding sentence exceeds max
                    # Force save and start new chunk
                    if current_chunk:
                        chunk_content = header_prefix + " ".join(current_chunk)
                        chunks.append(chunk_content)
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Save last chunk
        if current_chunk:
            chunk_content = header_prefix + " ".join(current_chunk)
            if len(chunk_content) >= self.min_chunk_size or not chunks:
                chunks.append(chunk_content)
            elif chunks:
                # Merge with last chunk if too small
                chunks[-1] += " " + " ".join(current_chunk)

        return chunks

    def chunk_text(self, text: str, page_id: str) -> List[TextChunk]:
        """
        Chunk text with improved logic

        Args:
            text: Input text
            page_id: Page ID for reference

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for page {page_id}")
            return []

        # Extract sections based on headers
        sections = self.extract_sections(text)

        all_chunks = []
        seen_hashes = set()  # For deduplication
        chunk_index = 0
        char_position = 0

        for header, content, start_pos in sections:
            if not content.strip():
                continue

            # Split section into sentences
            sentences = self.split_into_sentences(content)

            # Create chunks from sentences
            chunk_contents = self.create_chunks_from_sentences(sentences, header)

            # Create TextChunk objects
            for chunk_content in chunk_contents:
                # Deduplicate using MD5 hash
                content_hash = hashlib.md5(chunk_content.encode()).hexdigest()

                if content_hash in seen_hashes:
                    logger.debug(f"Skipping duplicate chunk for page {page_id}")
                    continue

                seen_hashes.add(content_hash)

                chunk = TextChunk(
                    page_id=page_id,
                    chunk_index=chunk_index,
                    content=chunk_content,
                    char_start=char_position,
                    char_end=char_position + len(chunk_content)
                )
                all_chunks.append(chunk)
                chunk_index += 1
                char_position += len(chunk_content)

        logger.info(
            f"Created {len(all_chunks)} chunks for page {page_id} "
            f"(from {len(sections)} sections, {len(seen_hashes)} unique)"
        )
        return all_chunks


class SemanticProcessor:
    """Process text into chunks and generate embeddings"""

    def __init__(
        self,
        min_chunk_size: int = None,
        max_chunk_size: int = None,
        embedding_model: str = None,
        api_key: str = None
    ):
        """
        Initialize semantic processor

        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            embedding_model: OpenAI embedding model name
            api_key: OpenAI API key
        """
        self.min_chunk_size = min_chunk_size or 100
        self.max_chunk_size = max_chunk_size or 2000
        self.embedding_model = embedding_model or Config.EMBEDDING_MODEL
        self.embedding_batch_size = Config.EMBEDDING_BATCH_SIZE
        self.max_retries = Config.EMBEDDING_MAX_RETRIES

        # Initialize improved chunker
        self.chunker = ImprovedChunker(
            min_chunk_size=self.min_chunk_size,
            max_chunk_size=self.max_chunk_size
        )

        api_key = api_key or Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        # Support for LiteLLM proxy or custom base URL
        base_url = Config.OPENAI_BASE_URL
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)

    def chunk_text(self, text: str, page_id: str) -> List[TextChunk]:
        """
        Split text into chunks using improved chunking logic

        Features:
        - Header-aware section extraction
        - Sentence-preserving boundaries
        - Context preservation with header tags
        - Duplicate removal
        - Min/max size enforcement

        Args:
            text: Text to chunk
            page_id: Page ID for reference

        Returns:
            List of TextChunk objects
        """
        return self.chunker.chunk_text(text, page_id)

    def get_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches with retry logic

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failed items)
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.embedding_batch_size):
            batch = texts[i:i + self.embedding_batch_size]

            # Retry logic for each batch
            batch_embeddings = None
            for attempt in range(self.max_retries):
                try:
                    # Truncate texts if too long (max 8191 tokens)
                    # Rough estimate: 1 token ≈ 4 characters
                    max_chars = 8191 * 4
                    processed_texts = []
                    for text in batch:
                        if len(text) > max_chars:
                            processed_texts.append(text[:max_chars])
                        else:
                            processed_texts.append(text)

                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=processed_texts
                    )

                    batch_embeddings = [item.embedding for item in response.data]
                    logger.info(
                        f"Generated {len(batch_embeddings)} embeddings "
                        f"(batch {i//self.embedding_batch_size + 1})"
                    )
                    break  # Success, exit retry loop

                except Exception as e:
                    logger.warning(
                        f"Batch {i//self.embedding_batch_size + 1} attempt {attempt + 1}/{self.max_retries} failed: {e}"
                    )
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to generate embeddings for batch after {self.max_retries} attempts")
                        batch_embeddings = [None] * len(batch)

            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def extract_semantic_terms(
        self,
        chunks: List[Dict[str, Any]],
        page_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract semantic terms from chunks using LLM

        Implementation strategy:
        1. Analyze all chunks for the document
        2. Extract key terms/concepts with confidence scores
        3. Track evidence (which chunks contain each term)
        4. Calculate frequency across chunks
        5. Identify relationships between terms

        Args:
            chunks: List of chunk dictionaries with content and metadata
            page_data: Page data with doc_id and title

        Returns:
            List of semantic term dictionaries
        """
        page_id = page_data.get('page_id', '')
        title = page_data.get('title', '')

        if not chunks:
            logger.warning(f"No chunks provided for semantic term extraction: {page_id}")
            return []

        # Collect all chunk contents and IDs
        chunk_texts = []
        chunk_ids = []
        for idx, chunk in enumerate(chunks):
            chunk_texts.append(chunk.get('content', ''))
            # Generate chunk ID consistent with TextChunk
            chunk_id = f"{page_id}_{idx}_{hashlib.md5(chunk.get('content', '').encode()).hexdigest()[:8]}"
            chunk_ids.append(chunk_id)

        # Combine all chunks into analysis context
        full_text = "\n\n".join(chunk_texts)

        try:
            # Get system prompt from prompts.py (pokopoko for game logic extraction)
            system_prompt = get_prompt("pokopoko")

            user_prompt = f"""Document Title: {title}

Content:
{full_text[:8000]}

Extract semantic terms from this document."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using fast, cost-effective model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json

            # [DEBUG] Log raw LLM response for debugging
            logger.debug(f"Raw LLM response (first 500 chars): {result_text[:500]}")

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            # Parse JSON
            extracted_data = json.loads(result_text)

            # [FIX] Handle both formats: {"nodes": [...]} or direct [...]
            if isinstance(extracted_data, dict):
                extracted_terms = extracted_data.get('nodes', [])
            elif isinstance(extracted_data, list):
                extracted_terms = extracted_data
            else:
                logger.error(f"Unexpected JSON format: {type(extracted_data)}")
                return []

            logger.info(f"Extracted {len(extracted_terms)} terms from LLM response")

            # Process extracted terms
            semantic_terms = []
            all_extracted_terms = []  # For cross-term relation analysis

            for term_data in extracted_terms:
                term = term_data.get('term', '').lower().strip()
                if not term:
                    continue

                # Find which chunks contain this term
                evidence = []
                frequency = 0

                for chunk_id, chunk_text in zip(chunk_ids, chunk_texts):
                    if term in chunk_text.lower():
                        evidence.append({
                            "chunk_id": chunk_id,
                            "position": chunk_text.lower().find(term)
                        })
                        frequency += chunk_text.lower().count(term)

                if frequency > 0:
                    # Get relations from LLM response
                    llm_relations = term_data.get('relations', [])

                    # Build raw_relations array (저장용 - JSONB 형식)
                    raw_relations = []
                    for rel in llm_relations:
                        target_term = rel.get('term', '').lower().strip() if isinstance(rel.get('term'), str) else rel.get('target', '').lower().strip()
                        relation_type = rel.get('type', 'related_to')

                        raw_relations.append({
                            "target": target_term,
                            "type": relation_type,
                            "confidence": rel.get('confidence', 0.8),
                            "desc": rel.get('desc', '')
                        })

                    # Add synonym relations from synonym dictionary
                    synonyms = get_synonyms(term)
                    for syn in synonyms:
                        if syn != term:  # Don't add self-reference
                            raw_relations.append({
                                "target": syn.lower().strip(),
                                "type": "synonym",
                                "confidence": 1.0,
                                "desc": "동의어"
                            })

                    # [FIX 1] Definition fallback logic
                    definition = term_data.get('definition', '').strip()
                    if not definition:
                        # Fallback: use context as definition (first 100 chars)
                        context = term_data.get('context', '').strip()
                        if context:
                            definition = context[:100] + ('...' if len(context) > 100 else '')
                            logger.debug(f"Using context as definition for term '{term}': {definition}")
                        else:
                            # Last resort: use first evidence chunk snippet
                            if evidence and len(chunk_texts) > 0:
                                first_evidence_idx = 0
                                for idx, chunk_text in enumerate(chunk_texts):
                                    if term in chunk_text.lower():
                                        first_evidence_idx = idx
                                        break
                                chunk_snippet = chunk_texts[first_evidence_idx][:100]
                                definition = f"{term}에 대한 내용: {chunk_snippet}..."
                                logger.debug(f"Using chunk snippet as definition for term '{term}'")
                            else:
                                definition = f"{term} (정의 없음)"
                                logger.warning(f"No definition available for term '{term}'")

                    semantic_terms.append({
                        "doc_id": page_id,
                        "term": term,
                        "category": term_data.get('category', 'other'),
                        "definition": definition,  # [수정] Fallback 로직 적용
                        "raw_relations": raw_relations,  # [핵심] JSONB 저장용
                        "frequency": frequency,
                        "confidence": float(term_data.get('confidence', 0.7)),
                        "evidence": evidence,
                        "context": term_data.get('context', '')[:500]  # Limit context length
                    })

                    all_extracted_terms.append(term)

            # Second pass: enrich relations by detecting synonyms between extracted terms
            for i, term_obj in enumerate(semantic_terms):
                term1 = term_obj['term']

                for j, other_term_obj in enumerate(semantic_terms):
                    if i == j:
                        continue

                    term2 = other_term_obj['term']

                    # Check if they are synonyms
                    if is_synonym(term1, term2):
                        # Add if not already in relations
                        existing_targets = [r['target'] for r in term_obj['raw_relations']]
                        if term2 not in existing_targets:
                            term_obj['raw_relations'].append({
                                "target": term2,
                                "type": "synonym",
                                "confidence": 1.0,
                                "desc": "추출된 용어 간 동의어"
                            })

            logger.info(f"Extracted {len(semantic_terms)} semantic terms from page {page_id}")
            logger.debug(f"Total relations across all terms: {sum(len(t['raw_relations']) for t in semantic_terms)}")
            return semantic_terms

        except Exception as e:
            logger.error(f"Failed to extract semantic terms for page {page_id}: {e}", exc_info=True)
            return []

    def process_page(
        self, page_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a complete page: chunk and embed

        Args:
            page_data: Page data dictionary from Confluence processor

        Returns:
            Dictionary with chunks and embeddings
        """
        page_id = page_data.get('page_id', '')
        content = page_data.get('content', '')

        result = {
            'page_id': page_id,
            'chunks': [],
            'semantic_terms': []
        }

        if not content:
            logger.warning(f"No content found for page {page_id}")
            return result

        # Create chunks
        chunks = self.chunk_text(content, page_id)

        if not chunks:
            logger.warning(f"No chunks created for page {page_id}")
            return result

        # Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.get_embeddings(chunk_texts)

        # Combine chunks with embeddings
        # New structure: content + metadata (JSONB) + embedding
        chunk_data = []
        total_chunks = len(chunks)

        for chunk, embedding in zip(chunks, embeddings):
            if embedding:
                chunk_data.append({
                    'doc_id': chunk.page_id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,  # Pure chunk text
                    'metadata': {  # JSONB metadata
                        'title': page_data.get('title', ''),
                        'chunk_index': chunk.chunk_index,
                        'total_chunks': total_chunks,
                        'doc_type': page_data.get('doc_type', 'unknown')
                    },
                    'embedding': embedding,
                    'char_count': len(chunk.content)
                })

        result['chunks'] = chunk_data

        # Extract semantic terms from chunks
        try:
            semantic_terms = self.extract_semantic_terms(chunk_data, page_data)
            result['semantic_terms'] = semantic_terms
        except Exception as e:
            logger.error(f"Failed to extract semantic terms for page {page_id}: {e}")
            result['semantic_terms'] = []

        return result

    def test_connection(self) -> bool:
        """
        Test OpenAI API connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_text = "This is a test."
            embeddings = self.get_embeddings([test_text])

            if embeddings and embeddings[0] and len(embeddings[0]) > 0:
                logger.info(
                    f"OpenAI API connection successful "
                    f"(embedding dimension: {len(embeddings[0])})"
                )
                return True
            else:
                logger.error("OpenAI API test failed: empty embedding")
                return False

        except Exception as e:
            logger.error(f"OpenAI API connection failed: {e}")
            return False
