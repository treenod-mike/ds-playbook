"""
Utility functions for configuration, logging, and checkpoint management
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Set
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Config:
    """Central configuration management"""

    # Confluence settings
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://your-domain.atlassian.net/wiki")
    CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # For LiteLLM proxy
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Supabase settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Table names
    TABLE_DOCUMENTS = os.getenv("TABLE_DOCUMENTS", "playbook_documents")
    TABLE_CHUNKS = os.getenv("TABLE_CHUNKS", "playbook_chunks")
    TABLE_SEMANTIC = os.getenv("TABLE_SEMANTIC", "playbook_semantic_terms")

    # Processing settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    # File paths
    CONFLUENCE_IDS_FILE = os.getenv("CONFLUENCE_IDS_FILE", "confluence_ids.txt")
    CHECKPOINT_FILE = os.getenv("CHECKPOINT_FILE", "data/checkpoint.json")
    LOG_FILE = os.getenv("LOG_FILE", "logs/playbook.log")

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required environment variables are set"""
        required = [
            ("CONFLUENCE_EMAIL", cls.CONFLUENCE_EMAIL),
            ("CONFLUENCE_API_TOKEN", cls.CONFLUENCE_API_TOKEN),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY),
        ]

        missing = [name for name, value in required if not value]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True


def setup_logging(log_file: str = None) -> logging.Logger:
    """Setup logging configuration"""
    log_file = log_file or Config.LOG_FILE

    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("playbook_nexus")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class CheckpointManager:
    """Manage processing checkpoints to resume from failures"""

    def __init__(self, checkpoint_file: str = None):
        self.checkpoint_file = checkpoint_file or Config.CHECKPOINT_FILE

        # Ensure checkpoint directory exists
        checkpoint_dir = Path(self.checkpoint_file).parent
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load checkpoint data from file"""
        if Path(self.checkpoint_file).exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load checkpoint: {e}")
                return self._default_data()
        return self._default_data()

    def _default_data(self) -> Dict[str, Any]:
        """Return default checkpoint data structure"""
        return {
            "processed_page_ids": [],
            "failed_page_ids": [],
            "last_processed_index": -1,
            "total_documents": 0,
            "total_chunks": 0,
        }

    def save(self):
        """Save checkpoint data to file"""
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")

    def mark_processed(self, page_id: str, index: int):
        """Mark a page as successfully processed"""
        if page_id not in self.data["processed_page_ids"]:
            self.data["processed_page_ids"].append(page_id)
        self.data["last_processed_index"] = index
        self.data["total_documents"] += 1
        self.save()

    def mark_failed(self, page_id: str):
        """Mark a page as failed"""
        if page_id not in self.data["failed_page_ids"]:
            self.data["failed_page_ids"].append(page_id)
        self.save()

    def add_chunks(self, count: int):
        """Increment total chunks counter"""
        self.data["total_chunks"] += count
        self.save()

    def is_processed(self, page_id: str) -> bool:
        """Check if a page has been processed"""
        return page_id in self.data["processed_page_ids"]

    def get_processed_ids(self) -> Set[str]:
        """Get set of processed page IDs"""
        return set(self.data["processed_page_ids"])

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "processed": len(self.data["processed_page_ids"]),
            "failed": len(self.data["failed_page_ids"]),
            "total_documents": self.data["total_documents"],
            "total_chunks": self.data["total_chunks"],
        }

    def reset(self):
        """Reset checkpoint data"""
        self.data = self._default_data()
        self.save()


def load_page_ids(file_path: str = None) -> list[str]:
    """Load Confluence page IDs from file"""
    file_path = file_path or Config.CONFLUENCE_IDS_FILE

    if not Path(file_path).exists():
        raise FileNotFoundError(f"Page IDs file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        # Filter out comments and empty lines
        page_ids = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith('#')
        ]

    return page_ids
