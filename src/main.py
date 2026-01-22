#!/usr/bin/env python3
"""
Main pipeline for processing Confluence pages into Supabase
"""
import sys
import time
import logging
from typing import Optional

from tqdm import tqdm

from src.shared.config import Config
from src.shared.utils import (
    setup_logging,
    CheckpointManager,
    load_page_ids,
)
from src.core.processors.confluence_processor import ConfluenceProcessor
from src.core.processors.semantic_processor import SemanticProcessor
from src.core.loaders.supabase_loader import SupabaseLoader
from src.core.rules.rules import classify_document


logger = setup_logging()


class Pipeline:
    """Main processing pipeline"""

    def __init__(self):
        """Initialize pipeline components"""
        logger.info("Initializing pipeline...")

        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)

        # Initialize components
        try:
            self.confluence = ConfluenceProcessor()
            self.semantic = SemanticProcessor()
            self.supabase = SupabaseLoader()
            self.checkpoint = CheckpointManager()

            logger.info("Pipeline components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            sys.exit(1)

    def test_connections(self) -> bool:
        """
        Test all external service connections

        Returns:
            True if all connections successful, False otherwise
        """
        logger.info("Testing connections...")

        tests = [
            ("Confluence API", self.confluence.test_connection),
            ("OpenAI API", self.semantic.test_connection),
            ("Supabase", self.supabase.test_connection),
        ]

        all_passed = True

        for name, test_func in tests:
            try:
                if test_func():
                    logger.info(f"✓ {name} connection successful")
                else:
                    logger.error(f"✗ {name} connection failed")
                    all_passed = False
            except Exception as e:
                logger.error(f"✗ {name} connection error: {e}")
                all_passed = False

        return all_passed

    def process_page(self, page_id: str) -> bool:
        """
        Process a single Confluence page with time measurements

        Args:
            page_id: Confluence page ID

        Returns:
            True if successful, False otherwise
        """
        page_start = time.time()

        try:
            # Step 1: Fetch page from Confluence
            step_start = time.time()
            page_data = self.confluence.process_page(page_id)
            fetch_time = time.time() - step_start

            if not page_data:
                logger.error(f"Failed to fetch page {page_id}")
                return False

            logger.debug(f"Fetch time: {fetch_time:.2f}s")

            # Step 2: Classify document
            step_start = time.time()
            category = classify_document(
                page_data.get('title', ''),
                page_data.get('content', '')
            )
            classify_time = time.time() - step_start
            logger.info(f"Page {page_id} classified as: {category} ({classify_time:.2f}s)")

            # Add category to page_data for use in metadata
            page_data['doc_type'] = category

            # Step 3: Load document into Supabase
            step_start = time.time()
            if not self.supabase.load_document(page_data):
                logger.error(f"Failed to load document {page_id}")
                return False
            doc_load_time = time.time() - step_start
            logger.debug(f"Document load time: {doc_load_time:.2f}s")

            # Step 4: Process chunks and embeddings + extract semantic terms
            step_start = time.time()
            result = self.semantic.process_page(page_data)
            chunks = result.get('chunks', [])
            semantic_terms = result.get('semantic_terms', [])
            semantic_time = time.time() - step_start

            if not chunks:
                logger.warning(f"No chunks created for page {page_id}")
                # Still consider it success if document was saved
                return True

            logger.info(
                f"Created {len(chunks)} chunks and {len(semantic_terms)} semantic terms "
                f"for page {page_id} ({semantic_time:.2f}s)"
            )

            # Step 5: Load chunks into Supabase
            step_start = time.time()
            loaded_count = self.supabase.load_chunks(chunks)
            chunk_load_time = time.time() - step_start

            if loaded_count == 0:
                logger.error(f"Failed to load chunks for page {page_id}")
                return False

            self.checkpoint.add_chunks(loaded_count)

            # Step 6: Load semantic terms into Supabase
            terms_loaded = 0
            if semantic_terms:
                step_start = time.time()
                terms_loaded = self.supabase.load_semantic_terms(semantic_terms)
                terms_load_time = time.time() - step_start
                logger.info(f"Loaded {terms_loaded} semantic terms ({terms_load_time:.2f}s)")

            # Final success summary
            total_time = time.time() - page_start
            logger.info(
                f"Successfully processed page {page_id}: "
                f"{loaded_count} chunks, {terms_loaded} terms in {total_time:.2f}s "
                f"(fetch: {fetch_time:.1f}s, semantic: {semantic_time:.1f}s)"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing page {page_id}: {e}", exc_info=True)
            return False

    def run(
        self,
        page_ids_file: str = None,
        skip_existing: bool = True,
        max_pages: Optional[int] = None,
        run_phase2: bool = False
    ):
        """
        Run the complete pipeline

        Args:
            page_ids_file: Path to file containing page IDs
            skip_existing: Skip pages that have been processed
            max_pages: Maximum number of pages to process (None = all)
            run_phase2: Run Phase 2 (ontology builder) after Phase 1
        """
        logger.info("=" * 70)
        logger.info("Starting Playbook Nexus Pipeline")
        logger.info("=" * 70)

        # Test connections first
        if not self.test_connections():
            logger.error("Connection tests failed. Please check configuration.")
            sys.exit(1)

        # Load page IDs
        try:
            page_ids = load_page_ids(page_ids_file)
            logger.info(f"Loaded {len(page_ids)} page IDs")
        except Exception as e:
            logger.error(f"Failed to load page IDs: {e}")
            sys.exit(1)

        # Filter already processed pages if requested
        if skip_existing:
            processed_ids = self.checkpoint.get_processed_ids()
            original_count = len(page_ids)
            page_ids = [pid for pid in page_ids if pid not in processed_ids]
            logger.info(
                f"Skipping {original_count - len(page_ids)} already processed pages"
            )

        # Limit number of pages if requested
        if max_pages and max_pages > 0:
            page_ids = page_ids[:max_pages]
            logger.info(f"Limited to processing {len(page_ids)} pages")

        if not page_ids:
            logger.info("No pages to process")
            return

        # Show initial statistics
        stats = self.checkpoint.get_stats()
        logger.info(f"Starting statistics: {stats}")

        # Process pages with progress bar
        logger.info(f"Processing {len(page_ids)} pages...")

        success_count = 0
        failure_count = 0
        pipeline_start = time.time()

        with tqdm(total=len(page_ids), desc="Processing pages", unit="page") as pbar:
            for idx, page_id in enumerate(page_ids):
                pbar.set_description(f"Processing page {page_id}")

                try:
                    success = self.process_page(page_id)

                    if success:
                        self.checkpoint.mark_processed(page_id, idx)
                        success_count += 1
                    else:
                        self.checkpoint.mark_failed(page_id)
                        failure_count += 1

                    pbar.set_postfix({
                        'success': success_count,
                        'failed': failure_count
                    })

                except KeyboardInterrupt:
                    logger.info("\nProcessing interrupted by user")
                    break

                except Exception as e:
                    logger.error(f"Unexpected error for page {page_id}: {e}")
                    self.checkpoint.mark_failed(page_id)
                    failure_count += 1
                    pbar.set_postfix({
                        'success': success_count,
                        'failed': failure_count
                    })

                finally:
                    pbar.update(1)

                # Small delay to avoid rate limits
                time.sleep(0.5)

        # Calculate final statistics
        pipeline_time = time.time() - pipeline_start
        avg_time_per_page = pipeline_time / len(page_ids) if page_ids else 0

        # Final statistics
        logger.info("=" * 70)
        logger.info("Pipeline completed")
        logger.info("=" * 70)
        logger.info(f"Total time: {pipeline_time:.2f}s ({pipeline_time/60:.1f}m)")
        logger.info(f"Average time per page: {avg_time_per_page:.2f}s")
        logger.info(f"Successfully processed: {success_count} pages")
        logger.info(f"Failed: {failure_count} pages")
        logger.info(f"Success rate: {100*success_count/len(page_ids):.1f}%")

        final_stats = self.checkpoint.get_stats()
        logger.info(f"Total statistics: {final_stats}")

        # Show Supabase stats
        try:
            supabase_stats = self.supabase.get_stats()
            logger.info(f"Supabase statistics: {supabase_stats}")
        except Exception as e:
            logger.warning(f"Could not retrieve Supabase stats: {e}")

        # Estimated time for remaining pages
        if skip_existing and failure_count < len(page_ids):
            try:
                page_ids_total = load_page_ids(page_ids_file)
                remaining = len(page_ids_total) - final_stats['processed']
                if remaining > 0 and success_count > 0:
                    est_remaining_time = (avg_time_per_page * remaining) / 60
                    logger.info(f"Estimated time for {remaining} remaining pages: {est_remaining_time:.1f}m")
            except:
                pass

        logger.info("=" * 70)

        # Phase 2: Ontology Builder (Optional)
        if run_phase2:
            logger.info("\n" + "=" * 70)
            logger.info("Starting Phase 2: Knowledge Graph Construction")
            logger.info("=" * 70)

            try:
                from src.core.processors.ontology_builder import OntologyBuilder

                builder = OntologyBuilder()
                phase2_stats = builder.build_graph()

                logger.info("=" * 70)
                logger.info("Phase 2 Completed Successfully")
                logger.info("=" * 70)
                logger.info(f"Documents processed: {phase2_stats['processed_documents']}")
                logger.info(f"Relationships created: {phase2_stats['total_relationships']}")
                logger.info(f"Phase 2 time: {phase2_stats['elapsed_time']:.2f}s ({phase2_stats['elapsed_time']/60:.1f}m)")
                logger.info("=" * 70)

            except Exception as e:
                logger.error(f"Phase 2 failed: {e}", exc_info=True)
                logger.warning("Phase 1 completed successfully, but Phase 2 failed")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process Confluence pages into Supabase"
    )
    parser.add_argument(
        '--page-ids-file',
        type=str,
        default=None,
        help='Path to file containing Confluence page IDs'
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Process all pages, even if already processed'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to process'
    )
    parser.add_argument(
        '--reset-checkpoint',
        action='store_true',
        help='Reset checkpoint before starting'
    )
    parser.add_argument(
        '--phase2',
        action='store_true',
        help='Run Phase 2 (Knowledge Graph Construction) after Phase 1'
    )

    args = parser.parse_args()

    # Create pipeline
    pipeline = Pipeline()

    # Reset checkpoint if requested
    if args.reset_checkpoint:
        logger.info("Resetting checkpoint...")
        pipeline.checkpoint.reset()

    # Run pipeline
    try:
        pipeline.run(
            page_ids_file=args.page_ids_file,
            skip_existing=not args.no_skip_existing,
            max_pages=args.max_pages,
            run_phase2=args.phase2
        )
    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
