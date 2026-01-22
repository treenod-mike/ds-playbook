"""
Configuration module for Playbook Nexus
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration management"""

    # Confluence settings
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://your-domain.atlassian.net/wiki")
    CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
    CONFLUENCE_BATCH_SIZE = int(os.getenv("CONFLUENCE_BATCH_SIZE", "10"))
    CONFLUENCE_RATE_LIMIT_DELAY = float(os.getenv("CONFLUENCE_RATE_LIMIT_DELAY", "0.5"))
    CONFLUENCE_MAX_RETRIES = int(os.getenv("CONFLUENCE_MAX_RETRIES", "3"))

    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # For LiteLLM proxy
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    EMBEDDING_MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))

    # Supabase settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BATCH_SIZE = int(os.getenv("SUPABASE_BATCH_SIZE", "100"))
    SUPABASE_MAX_RETRIES = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))

    # Table names
    TABLE_DOCUMENTS = os.getenv("TABLE_DOCUMENTS", "playbook_documents")
    TABLE_CHUNKS = os.getenv("TABLE_CHUNKS", "playbook_chunks")
    TABLE_SEMANTIC = os.getenv("TABLE_SEMANTIC", "playbook_semantic_terms")
    TABLE_RELATIONS = os.getenv("TABLE_RELATIONS", "playbook_semantic_relations")
    TABLE_ONTOLOGY_RULES = os.getenv("TABLE_ONTOLOGY_RULES", "playbook_ontology_rules")

    # Processing settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

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


# Singleton instance
config = Config()
