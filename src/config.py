"""
Configuration settings for the YouTube transcript scraper.
"""
import os
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).parent.parent

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://yalom_user:yalom_password@localhost:5432/yalom_transcripts'
)

# Scraping configuration
DEFAULT_DELAY_SECONDS = 15  # Delay between video fetches to avoid rate limiting
DEFAULT_LANGUAGE = 'en'
MAX_RETRIES = 3
RETRY_DELAY = 30  # Initial retry delay in seconds
RETRY_COOLDOWN = 120  # Cooldown period after exhausting all retries
REQUEST_TIMEOUT = 30

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# YouTube configuration
YT_DLP_OPTIONS = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
}

# Vectorization configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))  # Characters per chunk
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))  # Overlap between chunks
CHUNKING_STRATEGY = os.getenv('CHUNKING_STRATEGY', 'recursive')  # recursive, character, or token
# FastEmbed default (384 dimensions, no torch)
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '384'))

# Vector Store configuration (Hybrid approach)
VECTOR_STORE = os.getenv('VECTOR_STORE', 'qdrant')  # 'qdrant' (local) or 'pinecone' (cloud)

# Qdrant configuration (local development with Docker)
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'huberman_transcripts')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')  # Optional, for Qdrant Cloud

# Pinecone configuration (cloud/production)
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', '')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'yalom-transcripts')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'gcp-starter')  # Free tier

# AWS ingestion configuration
S3_PREFIX = os.getenv('S3_PREFIX', 'transcripts')
S3_BUCKET = os.getenv('S3_BUCKET', 'yalom-transcripts-backup')
DDB_TABLE = os.getenv('DDB_TABLE', '')

# RAG configuration
RAG_TOP_K = int(os.getenv('RAG_TOP_K', '7'))  # Number of chunks to return after filtering
RAG_RETRIEVAL_MULTIPLIER = int(os.getenv('RAG_RETRIEVAL_MULTIPLIER', '2'))  # Retrieve top_k × multiplier candidates
RAG_SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.3'))  # Minimum cosine similarity (0-1)
RAG_TEMPERATURE = float(os.getenv('RAG_TEMPERATURE', '0.7'))  # LLM temperature
RAG_HISTORY_LIMIT = int(os.getenv('RAG_HISTORY_LIMIT', '10'))
RAG_QUERY_REWRITING = os.getenv('RAG_QUERY_REWRITING', 'true').lower() == 'true'  # Enable multi-query rewriting
RAG_RERANKING = os.getenv('RAG_RERANKING', 'false').lower() == 'true'  # Enable cross-encoder re-ranking (slower)
RAG_DEBUG_LOGS = os.getenv('RAG_DEBUG_LOGS', 'false').lower() == 'true'
RAG_DEBUG_MAX_CHUNKS = int(os.getenv('RAG_DEBUG_MAX_CHUNKS', '10'))
RAG_DEBUG_MAX_PROMPT_CHARS = int(os.getenv('RAG_DEBUG_MAX_PROMPT_CHARS', '800'))

# Groq configuration
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
GROQ_MAX_TOKENS = int(os.getenv('GROQ_MAX_TOKENS', '1024'))

# Ingestion configuration
YOUTUBE_TRANSCRIPTS_PREFIX = os.getenv('YOUTUBE_TRANSCRIPTS_PREFIX', 'transcripts/youtube')

# API configuration (optional)
API_BASE_URL = os.getenv('API_BASE_URL', os.getenv('API_ENDPOINT', ''))
