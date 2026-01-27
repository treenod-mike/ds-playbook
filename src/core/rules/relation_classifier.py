"""
Relation Type Classifier and Weight Calculator

Classifies relationships into CORE (structural) or FLOW (causal/process)
and assigns appropriate weights for graph traversal prioritization.
"""
from typing import Dict, Tuple
import logging

logger = logging.getLogger("playbook_nexus.relation_classifier")


class RelationClassifier:
    """
    Classify relationships and assign weights based on predicate semantics
    """

    # CORE predicates: structural definitions, compositions
    CORE_PREDICATES = {
        'contains': 1,
        'consists_of': 1,
        'composed_of': 1,
        'includes': 1,
        'requires': 1,
        'is_a': 1,
        'part_of': 1,
        'has': 1,
        'belongs_to': 1,
    }

    # FLOW predicates: causal relationships, processes
    FLOW_PREDICATES_HIGH = {
        'guarantees': 2,
        'targets': 2,
        'sells': 2,
    }

    FLOW_PREDICATES_MEDIUM = {
        'increases': 3,
        'decreases': 3,
        'causes': 3,
        'triggers': 3,
        'consumes': 3,
        'produces': 3,
        'rewards': 3,
        'boosts': 3,
        'accelerates': 3,
        'generates': 3,
        'performs': 3,
        'converts_to': 3,
        'acquires': 3,
    }

    FLOW_PREDICATES_LOW = {
        'promotes': 4,
        'utilizes': 4,
        'induces': 4,
        'influences': 4,
    }

    # Abstract/generic terms that should be deprioritized
    ABSTRACT_TERMS = {
        '스테이지', 'stage',
        '유저', 'user',
        '이벤트', 'event',
        '아이템', 'item',
        '보상', 'reward',
        '콘텐츠', 'content',
        '시스템', 'system',
        '게임', 'game',
        '플레이어', 'player',
    }

    # Modifiers that make terms more specific
    SPECIFICITY_MODIFIERS = {
        # 형용사
        '보스', '일반', '특수', '한정', '고난이도', '저난이도',
        '신규', '기존', '복귀', '이탈', '활성',
        '무료', '유료', '프리미엄',
        # 수식어
        '첫', '마지막', '최종', '초기',
        # 영어
        'boss', 'special', 'limited', 'new', 'returning',
        'free', 'paid', 'premium',
    }

    @classmethod
    def classify_relation(cls, predicate: str) -> Tuple[str, int]:
        """
        Classify relation type and assign weight

        Args:
            predicate: Relationship predicate (e.g., "contains", "increases")

        Returns:
            Tuple of (relation_type, weight)
            - relation_type: 'CORE' or 'FLOW'
            - weight: 1 (highest) to 5 (lowest)
        """
        predicate_lower = predicate.lower().strip()

        # Check CORE predicates
        if predicate_lower in cls.CORE_PREDICATES:
            return ('CORE', cls.CORE_PREDICATES[predicate_lower])

        # Check FLOW predicates (high priority)
        if predicate_lower in cls.FLOW_PREDICATES_HIGH:
            return ('FLOW', cls.FLOW_PREDICATES_HIGH[predicate_lower])

        # Check FLOW predicates (medium priority)
        if predicate_lower in cls.FLOW_PREDICATES_MEDIUM:
            return ('FLOW', cls.FLOW_PREDICATES_MEDIUM[predicate_lower])

        # Check FLOW predicates (low priority)
        if predicate_lower in cls.FLOW_PREDICATES_LOW:
            return ('FLOW', cls.FLOW_PREDICATES_LOW[predicate_lower])

        # Default: FLOW with medium weight
        logger.debug(f"Unknown predicate '{predicate}', defaulting to FLOW with weight 3")
        return ('FLOW', 3)

    @classmethod
    def calculate_specificity(cls, term: str) -> Tuple[bool, float]:
        """
        Calculate term specificity score

        Args:
            term: Term string (e.g., "보스 스테이지", "스테이지")

        Returns:
            Tuple of (is_abstract, specificity_score)
            - is_abstract: True if term is generic without modifiers
            - specificity_score: 0.0 (very abstract) to 1.0 (very specific)
        """
        term_lower = term.lower().strip()
        term_words = term_lower.split()

        # Check if base term is abstract
        is_base_abstract = any(abstract in term_lower for abstract in cls.ABSTRACT_TERMS)

        if not is_base_abstract:
            # Not an abstract term, keep high specificity
            return (False, 1.0)

        # Check for modifiers
        has_modifier = any(modifier in term_lower for modifier in cls.SPECIFICITY_MODIFIERS)

        if has_modifier:
            # Abstract term with modifier -> medium specificity
            specificity = 0.7
            is_abstract = False
        elif len(term_words) > 1:
            # Multi-word term (likely has context) -> medium-low specificity
            specificity = 0.5
            is_abstract = False
        else:
            # Single abstract term without modifier -> very abstract
            specificity = 0.2
            is_abstract = True

        return (is_abstract, specificity)

    @classmethod
    def enrich_relation_metadata(cls, relation: Dict) -> Dict:
        """
        Enrich relation with type and weight

        Args:
            relation: Relation dictionary with 'predicate' key

        Returns:
            Enriched relation with 'relation_type' and 'weight'
        """
        predicate = relation.get('predicate', '')
        relation_type, weight = cls.classify_relation(predicate)

        relation['relation_type'] = relation_type
        relation['weight'] = weight

        logger.debug(
            f"Classified relation: {relation.get('source_term', '')} "
            f"→ [{predicate}] → {relation.get('target_term', '')} "
            f"as {relation_type} (weight={weight})"
        )

        return relation

    @classmethod
    def should_filter_abstract_relation(
        cls,
        source_term: str,
        target_term: str,
        prefer_specific: bool = True
    ) -> bool:
        """
        Determine if a relation should be filtered due to abstract nodes

        Args:
            source_term: Source term
            target_term: Target term
            prefer_specific: If True, filter relations with abstract source

        Returns:
            True if relation should be filtered (deprioritized)
        """
        if not prefer_specific:
            return False

        source_is_abstract, source_specificity = cls.calculate_specificity(source_term)
        target_is_abstract, target_specificity = cls.calculate_specificity(target_term)

        # Filter if source is very abstract (specificity < 0.3)
        if source_specificity < 0.3:
            logger.debug(
                f"Filtering abstract relation: {source_term} (specificity={source_specificity:.2f})"
            )
            return True

        return False
