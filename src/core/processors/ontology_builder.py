#!/usr/bin/env python3
"""
Ontology Builder for Knowledge Graph Construction (Phase 2)

이 스크립트는 Phase 1에서 추출한 semantic_terms의 raw_relations를 기반으로,
playbook_ontology_rules와 대조하여 검증된 관계를 playbook_semantic_relations에 저장합니다.

처리 흐름:
1. playbook_semantic_terms 로드 (raw_relations 포함)
2. playbook_ontology_rules 로드
3. raw_relations 검증 (ontology rules 기반)
4. 검증된 관계를 playbook_semantic_relations에 저장
5. 문서 최신성 기반 가중치 적용 (v3.1)
"""
import sys
import logging
import time
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timezone
import json

from src.shared.config import Config
from src.shared.utils import setup_logging
from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.rules.relation_classifier import RelationClassifier

logger = setup_logging()


# ============================================================================
# [v3.1] Document Recency Weight Calculation
# ============================================================================

def calculate_recency_weight(last_updated: str) -> float:
    """
    문서 최신성 기반 가중치 계산 (2026-02-01 기준 최근 1년)

    오래된 문서(74.2%)보다 최신 문서(25.8%)에 더 높은 가중치 부여

    Args:
        last_updated: ISO 8601 형식의 문서 업데이트 일자

    Returns:
        가중치 (1.0 ~ 1.5)

    가중치 정책:
        - 최근 1개월 (2.6%): 1.5x
        - 최근 3개월 (6.3%): 1.3x
        - 최근 6개월 (12.3%): 1.2x
        - 최근 1년 (25.8%): 1.1x
        - 1년 이상 (74.2%): 1.0x (기본값)
    """
    try:
        now = datetime.now(timezone.utc)

        # ISO 8601 파싱
        doc_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))

        # timezone naive인 경우 UTC로 변환
        if doc_date.tzinfo is None:
            doc_date = doc_date.replace(tzinfo=timezone.utc)

        days_old = (now - doc_date).days

        # 최신성 기반 가중치
        if days_old <= 30:      # 1개월 이내
            return 1.5
        elif days_old <= 90:    # 3개월 이내
            return 1.3
        elif days_old <= 180:   # 6개월 이내
            return 1.2
        elif days_old <= 365:   # 1년 이내
            return 1.1
        else:                   # 1년 이상
            return 1.0

    except Exception as e:
        logger.warning(f"Failed to calculate recency weight for date '{last_updated}': {e}")
        return 1.0  # 기본값


# ============================================================================
# [FIX 2] Term Matching Utilities - 한국어 조사 제거 및 정규화
# ============================================================================

def normalize_term(term: str) -> str:
    """
    용어를 정규화: 조사 제거, 띄어쓰기 제거, 소문자 변환

    Args:
        term: 원본 용어

    Returns:
        정규화된 용어
    """
    if not term:
        return ""

    # 소문자 변환
    normalized = term.lower().strip()

    # 한국어 조사 제거 (은/는/이/가/을/를/와/과/의/에/에서/으로/로/도/만/부터/까지)
    # 마지막 글자가 조사인 경우만 제거 (조사가 단어 중간에 있으면 제거하면 안 됨)
    korean_particles = ['은', '는', '이', '가', '을', '를', '와', '과', '의', '에', '에서', '으로', '로', '도', '만', '부터', '까지']
    for particle in korean_particles:
        if normalized.endswith(particle):
            normalized = normalized[:-len(particle)]
            break

    # 띄어쓰기 제거
    normalized = normalized.replace(' ', '')

    return normalized


def fuzzy_match_term(query_term: str, candidate_terms: Dict[str, Any]) -> Optional[Dict]:
    """
    Fuzzy matching으로 가장 유사한 용어 찾기

    Args:
        query_term: 찾고자 하는 용어
        candidate_terms: {normalized_key: term_object} 딕셔너리

    Returns:
        매칭된 term object 또는 None
    """
    normalized_query = normalize_term(query_term)

    # 1. Exact match (normalized)
    if normalized_query in candidate_terms:
        return candidate_terms[normalized_query]

    # 2. Substring match (normalized query가 candidate에 포함되거나, candidate가 query에 포함)
    for norm_key, term_obj in candidate_terms.items():
        if normalized_query in norm_key or norm_key in normalized_query:
            logger.debug(f"Substring match: '{query_term}' -> '{term_obj['term']}' (normalized: '{normalized_query}' ~ '{norm_key}')")
            return term_obj

    return None


class OntologyBuilder:
    """Build knowledge graph from semantic terms with ontology validation"""

    def __init__(self):
        """Initialize ontology builder"""
        self.supabase = SupabaseLoader()

        # Cache for ontology rules and terms
        self.ontology_rules: Dict[Tuple[str, str, str], Dict] = {}
        self.valid_predicates: set = set()
        self.terms_by_doc: Dict[str, List[Dict]] = defaultdict(list)
        self.terms_by_id: Dict[str, Dict] = {}
        self.terms_by_name: Dict[str, Dict] = {}  # doc_id:term -> term object mapping

        # [FIX 2C] Global term candidates (normalized_term -> term_object)
        # 문서 간 연결을 위해 전체 문서의 자주 등장하는 용어를 글로벌 후보로 관리
        self.global_term_candidates: Dict[str, Dict] = {}  # normalized_term -> term object

        logger.info("OntologyBuilder initialized")

    def load_ontology_rules(self) -> int:
        """
        Load ontology rules from playbook_ontology_rules table

        Returns:
            Number of rules loaded
        """
        try:
            response = self.supabase.client.table('playbook_ontology_rules').select(
                'id,subject_type,predicate,object_type,description'
            ).execute()

            rules = response.data if hasattr(response, 'data') else []

            for rule in rules:
                key = (
                    rule['subject_type'].lower(),
                    rule['predicate'].lower(),
                    rule['object_type'].lower()
                )
                self.ontology_rules[key] = rule
                self.valid_predicates.add(rule['predicate'].lower())

            logger.info(f"Loaded {len(rules)} ontology rules")
            logger.debug(f"Valid predicates: {sorted(self.valid_predicates)}")
            return len(rules)

        except Exception as e:
            logger.error(f"Failed to load ontology rules: {e}")
            raise

    def load_semantic_terms(self, doc_ids: List[str] = None) -> int:
        """
        Load semantic terms from playbook_semantic_terms table

        Args:
            doc_ids: Optional list of document IDs to filter

        Returns:
            Number of terms loaded
        """
        try:
            # Load all terms with pagination to avoid 1000 record limit
            all_terms = []
            page_size = 1000
            page = 0

            logger.info("Loading semantic terms with pagination...")

            while True:
                query = self.supabase.client.table('playbook_semantic_terms').select(
                    'id,doc_id,term,category,definition,frequency,confidence,raw_relations'
                ).range(page * page_size, (page + 1) * page_size - 1)

                if doc_ids:
                    query = query.in_('doc_id', doc_ids)

                response = query.execute()
                batch = response.data if hasattr(response, 'data') else []

                if not batch:
                    break

                all_terms.extend(batch)
                logger.info(f"Loaded page {page + 1}: {len(batch)} terms (total: {len(all_terms)})")
                page += 1

                # Stop if we got less than a full page (means we're done)
                if len(batch) < page_size:
                    break

            # Index by document, ID, and term name
            for term in all_terms:
                self.terms_by_doc[term['doc_id']].append(term)
                self.terms_by_id[term['id']] = term

                # Also index by term name (lowercase) for lookup
                term_name_key = f"{term['doc_id']}:{term['term'].lower()}"
                self.terms_by_name[term_name_key] = term

                # [FIX 2C] Build global term candidates (normalized)
                # 빈도가 높거나 confidence가 높은 용어를 글로벌 후보로 추가
                if term.get('frequency', 0) >= 2 or term.get('confidence', 0) >= 0.8:
                    normalized_term = normalize_term(term['term'])
                    if normalized_term:
                        # 같은 normalized term이 여러 문서에 있을 수 있으므로,
                        # frequency가 더 높은 것을 우선 선택
                        existing = self.global_term_candidates.get(normalized_term)
                        if not existing or term.get('frequency', 0) > existing.get('frequency', 0):
                            self.global_term_candidates[normalized_term] = term

            logger.info(f"Loaded {len(all_terms)} semantic terms from {len(self.terms_by_doc)} documents")
            logger.info(f"Built {len(self.global_term_candidates)} global term candidates for cross-document matching")
            return len(all_terms)

        except Exception as e:
            logger.error(f"Failed to load semantic terms: {e}")
            raise

    def validate_relationship(
        self,
        source_term: Dict,
        predicate: str,
        target_term: Dict,
        confidence: float
    ) -> Tuple[bool, str]:
        """
        Validate relationship against ontology rules

        Args:
            source_term: Source term dictionary
            predicate: Relationship predicate
            target_term: Target term dictionary
            confidence: Extraction confidence

        Returns:
            Tuple of (is_valid, reason)
        """
        source_cat = source_term.get('category', '').lower()
        target_cat = target_term.get('category', '').lower()
        pred = predicate.lower()

        # Check if predicate is valid
        if pred not in self.valid_predicates:
            return False, f"Invalid predicate '{predicate}'"

        # Check if relationship matches ontology rules
        rule_key = (source_cat, pred, target_cat)
        if rule_key not in self.ontology_rules:
            return False, f"No rule for {source_cat} -{pred}-> {target_cat}"

        # Confidence check (minimum threshold 0.5)
        if confidence < 0.5:
            return False, f"Confidence {confidence:.2f} below minimum threshold 0.5"

        return True, "Valid"

    def build_graph_for_document(self, doc_id: str) -> int:
        """
        Build knowledge graph for a single document by processing raw_relations

        Args:
            doc_id: Document ID

        Returns:
            Number of relationships created
        """
        terms_in_doc = self.terms_by_doc.get(doc_id, [])
        if len(terms_in_doc) < 2:
            logger.debug(f"Document {doc_id} has fewer than 2 terms, skipping")
            return 0

        logger.info(f"Building graph for document {doc_id} ({len(terms_in_doc)} terms)")

        # [v3.1] Get document last_updated for recency weighting
        doc_last_updated = None
        recency_weight = 1.0
        try:
            response = self.supabase.client.table('playbook_documents')\
                .select('last_updated')\
                .eq('id', doc_id)\
                .single()\
                .execute()

            if response.data and response.data.get('last_updated'):
                doc_last_updated = response.data['last_updated']
                recency_weight = calculate_recency_weight(doc_last_updated)

                # 가중치가 기본값(1.0)이 아닌 경우에만 로그
                if recency_weight > 1.0:
                    logger.info(f"Document {doc_id} recency weight: {recency_weight:.2f}x (updated: {doc_last_updated[:10]})")

        except Exception as e:
            logger.warning(f"Failed to get last_updated for doc {doc_id}: {e}")

        # [FIX 2B] Build local normalized candidate dict for current document
        local_candidates = {}
        for term_obj in terms_in_doc:
            norm_key = normalize_term(term_obj['term'])
            if norm_key:
                local_candidates[norm_key] = term_obj

        # Process raw_relations for each term
        validated_relations = []
        skipped_count = defaultdict(int)
        total_raw_relations = 0
        match_methods = defaultdict(int)  # Track which matching method was used

        for source_term in terms_in_doc:
            raw_relations = source_term.get('raw_relations', [])

            if not raw_relations:
                continue

            total_raw_relations += len(raw_relations)

            for relation in raw_relations:
                target_term_name = relation.get('target', '').lower().strip()
                predicate = relation.get('type', '').lower().strip()
                confidence = relation.get('confidence', 0.8)
                evidence = relation.get('evidence', relation.get('desc', ''))  # LLM이 제공한 근거 텍스트

                if not target_term_name or not predicate:
                    skipped_count['missing_data'] += 1
                    continue

                # [FIX 2 & FIX 3] Enhanced term matching with detailed logging
                target_term = None
                match_method = None

                # Method 1: Exact match (original key format)
                target_term_key = f"{doc_id}:{target_term_name}"
                target_term = self.terms_by_name.get(target_term_key)
                if target_term:
                    match_method = "exact_local"
                    match_methods[match_method] += 1
                else:
                    # Method 2: Fuzzy match within current document
                    target_term = fuzzy_match_term(target_term_name, local_candidates)
                    if target_term:
                        match_method = "fuzzy_local"
                        match_methods[match_method] += 1
                    else:
                        # Method 3: Fuzzy match in global candidates (cross-document)
                        target_term = fuzzy_match_term(target_term_name, self.global_term_candidates)
                        if target_term:
                            match_method = "fuzzy_global"
                            match_methods[match_method] += 1

                # [FIX 3] Detailed logging for matching failures
                if not target_term:
                    skipped_count['term_not_found'] += 1
                    normalized_query = normalize_term(target_term_name)

                    # Show available candidates for debugging
                    local_sample = list(local_candidates.keys())[:5]
                    global_sample = list(self.global_term_candidates.keys())[:5]

                    logger.debug(
                        f"[MATCH FAIL] Source: '{source_term['term']}' -{predicate}-> Target: '{target_term_name}' (normalized: '{normalized_query}')\n"
                        f"  Local candidates (sample): {local_sample}\n"
                        f"  Global candidates (sample): {global_sample}"
                    )
                    continue
                else:
                    # Log successful match with method
                    logger.debug(
                        f"[MATCH OK] '{source_term['term']}' -{predicate}-> '{target_term_name}' "
                        f"matched to '{target_term['term']}' via {match_method}"
                    )

                # Validate against ontology rules
                is_valid, reason = self.validate_relationship(
                    source_term=source_term,
                    predicate=predicate,
                    target_term=target_term,
                    confidence=confidence
                )

                if not is_valid:
                    skipped_count[reason] += 1
                    logger.debug(
                        f"[VALIDATION FAIL] {source_term['term']} -{predicate}-> {target_term['term']} ({reason})"
                    )
                    continue

                # [HUB FIX] Check if relation should be filtered due to abstract source term
                if RelationClassifier.should_filter_abstract_relation(
                    source_term['term'],
                    target_term['term'],
                    prefer_specific=True
                ):
                    skipped_count['abstract_source_filtered'] += 1
                    logger.debug(
                        f"[HUB FILTER] {source_term['term']} -{predicate}-> {target_term['term']} "
                        f"(source term is too abstract)"
                    )
                    continue

                # [v3.1] Apply recency weight to confidence
                weighted_confidence = confidence * recency_weight

                # Cap at 1.0 (maximum confidence)
                weighted_confidence = min(weighted_confidence, 1.0)

                # Prepare validated relation for insertion
                validated_relations.append({
                    'source_term_id': source_term['id'],
                    'predicate': predicate,
                    'target_term_id': target_term['id'],
                    'confidence': weighted_confidence,  # 최신성 가중치 적용
                    'evidence_chunk_id': None,  # Can be enriched later if needed
                    'evidence': evidence  # LLM이 추출한 근거 텍스트 저장
                })

                # Log recency boost for high-weighted relations
                if recency_weight > 1.0 and confidence < weighted_confidence:
                    logger.debug(
                        f"[RECENCY BOOST] {source_term['term']} -{predicate}-> {target_term['term']} "
                        f"confidence: {confidence:.2f} -> {weighted_confidence:.2f} ({recency_weight:.2f}x)"
                    )

        # Log statistics
        logger.info(f"Processed {total_raw_relations} raw relations from {len(terms_in_doc)} terms")

        # [v3.1] Log recency weight statistics
        if recency_weight > 1.0:
            boosted_count = sum(1 for r in validated_relations if r['confidence'] > 0.8)
            logger.info(f"Recency weight {recency_weight:.2f}x applied - {boosted_count} high-confidence relations boosted")

        # [FIX 3] Log match method statistics
        if match_methods:
            logger.info(f"Match method breakdown: {dict(match_methods)}")

        if skipped_count:
            logger.info(f"Skipped relationships breakdown: {dict(skipped_count)}")

        # Insert validated relationships
        if validated_relations:
            loaded_count = self.load_relations(validated_relations)
            logger.info(f"✓ Loaded {loaded_count}/{len(validated_relations)} relationships for document {doc_id}")
            return loaded_count
        else:
            logger.warning(f"No valid relationships to load for document {doc_id}")
            return 0

    def load_relations(self, relations: List[Dict]) -> int:
        """
        Load relationships with confidence reinforcement logic.

        When a relationship (source, target, predicate) is seen multiple times:
        - Increases confidence using: new_conf = old_conf + (1.0 - old_conf) * (input_conf * 0.2)
        - Appends new evidence (up to 3 most recent)
        - Tracks occurrence count and last verified timestamp

        Args:
            relations: List of relationship dictionaries

        Returns:
            Number of relationships loaded (new + updated)
        """
        if not relations:
            return 0

        try:
            total_loaded = 0
            reinforced_count = 0

            for rel in relations:
                # Check if relationship already exists
                existing = self.supabase.client.table('playbook_semantic_relations').select(
                    '*'
                ).eq('source_term_id', rel['source_term_id']).eq(
                    'target_term_id', rel['target_term_id']
                ).eq('predicate', rel['predicate']).execute()

                if existing.data and len(existing.data) > 0:
                    # Relationship exists - Apply reinforcement
                    old_record = existing.data[0]
                    old_conf = old_record['confidence']
                    input_conf = rel['confidence']

                    # Reinforcement formula: gradual confidence increase
                    # new_conf = old_conf + (1.0 - old_conf) * (input_conf * 0.2)
                    new_conf = min(1.0, old_conf + (1.0 - old_conf) * (input_conf * 0.2))

                    # Parse existing evidence
                    try:
                        if isinstance(old_record['evidence'], str):
                            # Try to parse as JSON array
                            evidence_list = json.loads(old_record['evidence'])
                            if not isinstance(evidence_list, list):
                                evidence_list = [old_record['evidence']]
                        elif isinstance(old_record['evidence'], list):
                            evidence_list = old_record['evidence']
                        else:
                            evidence_list = [str(old_record['evidence'])]
                    except (json.JSONDecodeError, TypeError):
                        evidence_list = [old_record['evidence']]

                    # Add new evidence (keep up to 3 most recent)
                    new_evidence = rel.get('evidence', '')
                    if new_evidence and new_evidence not in evidence_list:
                        evidence_list.append(new_evidence)
                        evidence_list = evidence_list[-3:]  # Keep last 3

                    # Build update data (only include columns that exist)
                    update_data = {
                        'confidence': new_conf,
                        'evidence': json.dumps(evidence_list, ensure_ascii=False)
                    }

                    # Add optional reinforcement columns if they exist
                    if 'occurrence_count' in old_record:
                        occurrence_count = old_record.get('occurrence_count', 1) + 1
                        update_data['occurrence_count'] = occurrence_count
                    else:
                        occurrence_count = None

                    if 'last_verified_at' in old_record:
                        update_data['last_verified_at'] = 'now()'

                    self.supabase.client.table('playbook_semantic_relations').update(
                        update_data
                    ).eq('id', old_record['id']).execute()

                    reinforced_count += 1
                    if occurrence_count:
                        logger.debug(
                            f"Reinforced: {rel['predicate']} "
                            f"(conf: {old_conf:.3f} → {new_conf:.3f}, "
                            f"count: {occurrence_count})"
                        )
                    else:
                        logger.debug(
                            f"Reinforced: {rel['predicate']} "
                            f"(conf: {old_conf:.3f} → {new_conf:.3f})"
                        )
                else:
                    # New relationship - Insert with initial values
                    insert_data = rel.copy()
                    # Wrap evidence in JSON array for consistency
                    if 'evidence' in insert_data:
                        insert_data['evidence'] = json.dumps([insert_data['evidence']], ensure_ascii=False)

                    # Add optional reinforcement columns if table supports them
                    # Try to add them, but don't fail if columns don't exist
                    try:
                        insert_data['occurrence_count'] = 1
                        insert_data['last_verified_at'] = 'now()'
                    except:
                        pass

                    self.supabase.client.table('playbook_semantic_relations').insert(
                        insert_data
                    ).execute()

                    logger.debug(f"Inserted new: {rel['predicate']} (conf: {rel['confidence']:.3f})")

                total_loaded += 1

            if reinforced_count > 0:
                logger.info(f"✓ Reinforced {reinforced_count}/{total_loaded} existing relationships")

            return total_loaded

        except Exception as e:
            logger.error(f"Failed to load relationships: {e}", exc_info=True)
            raise

    def build_graph(self, doc_ids: List[str] = None, max_docs: int = None) -> Dict[str, Any]:
        """
        Build knowledge graph for multiple documents

        Args:
            doc_ids: Optional list of document IDs to process
            max_docs: Optional maximum number of documents to process

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("Starting Knowledge Graph Construction (Phase 2)")
        logger.info("=" * 70)

        # Load ontology rules
        rules_count = self.load_ontology_rules()
        if rules_count == 0:
            logger.error("No ontology rules found")
            sys.exit(1)

        # Load semantic terms
        terms_count = self.load_semantic_terms(doc_ids=doc_ids)
        if terms_count == 0:
            logger.error("No semantic terms found")
            sys.exit(1)

        # Get documents to process
        docs_to_process = list(self.terms_by_doc.keys())
        if max_docs:
            docs_to_process = docs_to_process[:max_docs]

        logger.info(f"Processing {len(docs_to_process)} documents")

        # Process each document
        total_relations = 0
        success_count = 0
        start_time = time.time()

        for idx, doc_id in enumerate(docs_to_process):
            logger.info(f"\n[{idx+1}/{len(docs_to_process)}] Processing document: {doc_id}")

            try:
                relations_count = self.build_graph_for_document(doc_id)
                total_relations += relations_count
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to process document {doc_id}: {e}")
                continue

        # Final statistics
        elapsed_time = time.time() - start_time
        logger.info("=" * 70)
        logger.info("Knowledge Graph Construction Completed")
        logger.info("=" * 70)
        logger.info(f"Total time: {elapsed_time:.2f}s ({elapsed_time/60:.1f}m)")
        logger.info(f"Documents processed: {success_count}/{len(docs_to_process)}")
        logger.info(f"Relationships created: {total_relations}")
        logger.info(f"Average: {total_relations/success_count:.1f} relations per document" if success_count > 0 else "")
        logger.info("=" * 70)

        return {
            'total_documents': len(docs_to_process),
            'processed_documents': success_count,
            'total_relationships': total_relations,
            'elapsed_time': elapsed_time
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Knowledge Graph from Semantic Terms (Phase 2)"
    )
    parser.add_argument(
        '--doc-ids',
        type=str,
        nargs='+',
        help='Specific document IDs to process'
    )
    parser.add_argument(
        '--max-docs',
        type=int,
        help='Maximum number of documents to process'
    )

    args = parser.parse_args()

    # Create ontology builder
    builder = OntologyBuilder()

    # Build knowledge graph
    try:
        stats = builder.build_graph(
            doc_ids=args.doc_ids,
            max_docs=args.max_docs
        )

        logger.info("Knowledge graph construction completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Knowledge graph construction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
