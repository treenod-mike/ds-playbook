-- Migration: Add relation_type and weight columns to playbook_semantic_relations
-- Purpose: Enable edge weight-based graph traversal and hub node distribution
-- Date: 2026-01-27

-- Step 1: Create ENUM type for relation_type
CREATE TYPE relation_type_enum AS ENUM ('CORE', 'FLOW');

-- Step 2: Add new columns to playbook_semantic_relations
ALTER TABLE playbook_semantic_relations
ADD COLUMN relation_type relation_type_enum DEFAULT 'FLOW',
ADD COLUMN weight INT DEFAULT 3 CHECK (weight >= 1 AND weight <= 5);

-- Step 3: Add comments for documentation
COMMENT ON COLUMN playbook_semantic_relations.relation_type IS
'Type of relationship: CORE (structural/definition) or FLOW (causal/process)';

COMMENT ON COLUMN playbook_semantic_relations.weight IS
'Relationship weight (1-5): 1=highest priority (CORE), 3=medium (FLOW), 5=lowest';

-- Step 4: Create index for efficient querying by weight
CREATE INDEX idx_relations_weight ON playbook_semantic_relations(weight);
CREATE INDEX idx_relations_type ON playbook_semantic_relations(relation_type);

-- Step 5: Update existing relations based on predicate patterns
-- CORE relations (structural definitions)
UPDATE playbook_semantic_relations
SET relation_type = 'CORE', weight = 1
WHERE predicate IN ('contains', 'consists_of', 'composed_of', 'includes', 'requires', 'is_a', 'part_of');

-- FLOW relations (causal/process)
UPDATE playbook_semantic_relations
SET relation_type = 'FLOW', weight = 3
WHERE predicate IN ('increases', 'decreases', 'causes', 'triggers', 'consumes', 'produces', 'rewards', 'boosts', 'accelerates');

-- High priority FLOW relations
UPDATE playbook_semantic_relations
SET weight = 2
WHERE predicate IN ('guarantees', 'targets', 'sells')
AND relation_type = 'FLOW';

-- Low priority FLOW relations
UPDATE playbook_semantic_relations
SET weight = 4
WHERE predicate IN ('promotes', 'utilizes', 'induces')
AND relation_type = 'FLOW';

-- Step 6: Add column to semantic_terms for abstract concept marking
ALTER TABLE playbook_semantic_terms
ADD COLUMN is_abstract BOOLEAN DEFAULT FALSE,
ADD COLUMN specificity_score FLOAT DEFAULT 1.0 CHECK (specificity_score >= 0.0 AND specificity_score <= 1.0);

COMMENT ON COLUMN playbook_semantic_terms.is_abstract IS
'TRUE if term is a generic concept without modifiers (e.g., "스테이지" vs "보스 스테이지")';

COMMENT ON COLUMN playbook_semantic_terms.specificity_score IS
'Term specificity (0.0-1.0): 0.0=very abstract, 1.0=very specific';

-- Step 7: Mark common abstract terms
UPDATE playbook_semantic_terms
SET is_abstract = TRUE, specificity_score = 0.2
WHERE term IN ('스테이지', '유저', '이벤트', '아이템', '보상', '콘텐츠', '시스템');

-- Step 8: Create index for abstract filtering
CREATE INDEX idx_terms_abstract ON playbook_semantic_terms(is_abstract);
CREATE INDEX idx_terms_specificity ON playbook_semantic_terms(specificity_score);

-- Rollback script (in case of issues)
-- DROP INDEX IF EXISTS idx_relations_weight;
-- DROP INDEX IF EXISTS idx_relations_type;
-- DROP INDEX IF EXISTS idx_terms_abstract;
-- DROP INDEX IF EXISTS idx_terms_specificity;
-- ALTER TABLE playbook_semantic_relations DROP COLUMN IF EXISTS relation_type;
-- ALTER TABLE playbook_semantic_relations DROP COLUMN IF EXISTS weight;
-- ALTER TABLE playbook_semantic_terms DROP COLUMN IF EXISTS is_abstract;
-- ALTER TABLE playbook_semantic_terms DROP COLUMN IF EXISTS specificity_score;
-- DROP TYPE IF EXISTS relation_type_enum;
