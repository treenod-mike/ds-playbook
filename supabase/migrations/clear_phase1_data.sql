-- ============================================================
-- Playbook Nexus - Phase 1 데이터 초기화 스크립트
-- Version: v2.0 (2025-01-30)
-- Description: Phase 1 데이터만 삭제 (온톨로지 룰은 유지)
--
-- ⚠️ 경고: 이 스크립트는 다음 테이블의 데이터를 삭제합니다:
--   - playbook_semantic_relations (최종 관계)
--   - playbook_semantic_terms (추출된 용어)
--   - playbook_chunks (청크 + 임베딩)
--   - playbook_documents (문서 메타데이터)
--
-- 온톨로지 룰 (playbook_ontology_rules)은 유지됩니다.
-- ============================================================

-- [1. 관계 데이터 삭제]
-- Foreign Key 의존성 순서: relations -> terms -> chunks -> documents
DELETE FROM playbook_semantic_relations;

-- [2. 용어 데이터 삭제]
DELETE FROM playbook_semantic_terms;

-- [3. 청크 데이터 삭제]
DELETE FROM playbook_chunks;

-- [4. 문서 메타데이터 삭제]
DELETE FROM playbook_documents;

-- [5. 시퀀스 초기화 (필요시)]
-- ALTER SEQUENCE IF EXISTS playbook_documents_id_seq RESTART WITH 1;

-- [6. 삭제 결과 확인]
DO $$
DECLARE
    doc_count INTEGER;
    chunk_count INTEGER;
    term_count INTEGER;
    rel_count INTEGER;
    rule_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO doc_count FROM playbook_documents;
    SELECT COUNT(*) INTO chunk_count FROM playbook_chunks;
    SELECT COUNT(*) INTO term_count FROM playbook_semantic_terms;
    SELECT COUNT(*) INTO rel_count FROM playbook_semantic_relations;
    SELECT COUNT(*) INTO rule_count FROM playbook_ontology_rules;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Phase 1 데이터 초기화 완료';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Documents: % rows deleted', doc_count;
    RAISE NOTICE 'Chunks: % rows deleted', chunk_count;
    RAISE NOTICE 'Terms: % rows deleted', term_count;
    RAISE NOTICE 'Relations: % rows deleted', rel_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Ontology Rules: % rows (유지됨)', rule_count;
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE '다음 단계:';
    RAISE NOTICE '  1. Phase 1 재실행: bash run_phase1_test.sh';
    RAISE NOTICE '  2. 결과 확인: python3 scripts/diagnose_relations.py';
    RAISE NOTICE '============================================================';
END $$;
