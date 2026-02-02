# Project Structure

## Overview

```
yalom/
├── src/
│   ├── database/              # Database infrastructure (PostgreSQL)
│   │   ├── __init__.py
│   │   ├── connection.py           # Database connection & session management
│   │   ├── models.py               # VideoTranscript model
│   │   └── models_tapesearch.py    # PodcastTranscript model
│   │
│   ├── ingestion/             # Transcript ingestion into PostgreSQL
│   │   ├── __init__.py
│   │   ├── youtube_fetcher.py      # YouTube transcript fetching
│   │   ├── youtube_scraper.py      # YouTube channel scraping
│   │   ├── github_loader.py        # GitHub transcript loading
│   │   ├── github_scraper.py       # GitHub to DB integration
│   │   ├── kaggle_loader.py        # Kaggle dataset loading
│   │   ├── kaggle_scraper.py       # Kaggle to DB integration
│   │   ├── local_loader.py         # Local file loading
│   │   ├── tapesearch_fetcher.py   # TapeSearch API client
│   │   └── tapesearch_scraper.py   # TapeSearch to DB integration
│   │
│   ├── vectorization/         # Text-to-vector and vector DB operations
│   │   ├── __init__.py
│   │   ├── chunking.py             # Text chunking strategies
│   │   └── embeddings.py           # Embedding generation (OpenAI, ST, etc.)
│   │   # TODO: vector_store.py, search.py, rag.py
│   │
│   ├── config.py              # Application-wide configuration
│   └── __init__.py            # Package initialization
│
├── utils/                     # Utility scripts
│   ├── check_duplicates.py    # Check for duplicate episodes
│   └── download_kaggle.py     # Kaggle dataset downloader
│
├── data/                      # Local data storage
│   └── huberman-lab-podcasts/ # Downloaded transcripts
│
├── cli.py                     # Command-line interface
├── docker-compose.yml         # PostgreSQL + Vector DB (prepared)
├── pyproject.toml             # Poetry dependencies
└── README.md                  # Main documentation
```

## Module Organization

### Database (`src/database/`)

All database-related code:
- `connection.py`: Database connection, session management, initialization
- `models.py`: VideoTranscript schema (SQLAlchemy model)
- `models_tapesearch.py`: PodcastTranscript schema (separate table)

### Ingestion (`src/ingestion/`)

All transcript ingestion into PostgreSQL:

- **YouTube**: `youtube_fetcher.py`, `youtube_scraper.py`
- **GitHub**: `github_loader.py`, `github_scraper.py`
- **Kaggle**: `kaggle_loader.py`, `kaggle_scraper.py`
- **Local Files**: `local_loader.py`
- **TapeSearch**: `tapesearch_fetcher.py`, `tapesearch_scraper.py`

Each loader follows the same pattern:
1. **Loader** class: Fetches data from source
2. **Scraper** class: Saves data to PostgreSQL database

### Vectorization (`src/vectorization/`)

Text-to-vector pipeline and vector database operations:

- **Chunking** (`chunking.py`): Text splitting strategies
  - `FixedSizeChunker`: Fixed character/token chunks with overlap
  - `SentenceChunker`: Semantic sentence-based chunking
  - TODO: `TimestampChunker`, `ParagraphChunker`, `SemanticChunker`

- **Embeddings** (`embeddings.py`): Vector generation
  - `SentenceTransformerProvider`: Local open-source models (free)
  - `OpenAIProvider`: OpenAI API (text-embedding-3-small/large)
  - TODO: `CohereProvider`, `HuggingFaceProvider`

- **TODO**:
  - `vector_store.py`: Vector DB operations (Qdrant, Weaviate, pgvector)
  - `search.py`: Semantic search and retrieval
  - `rag.py`: RAG pipeline integration

### Configuration (`src/config.py`)

Application-wide settings:
- Database URL and connection settings
- API timeouts and retry logic
- yt-dlp options for YouTube scraping
- Rate limiting parameters

### Docker Compose (`docker-compose.yml`)

Container orchestration:
- **PostgreSQL 16**: Main transcript database (port 5432)
- **Vector DB placeholder**: Ready for Qdrant, Weaviate, or pgvector
- **Network**: `yalom_network` for inter-service communication
- **Volumes**: Persistent storage for both databases

### Utilities (`utils/`)

Helper scripts for maintenance and debugging:
- `check_duplicates.py`: Verify data integrity
- `download_kaggle.py`: Interactive Kaggle downloader

### CLI (`cli.py`)

Single entry point for all operations:
```bash
poetry run python cli.py [command] [options]
```

## Usage Examples

### Load Data

```bash
# From Kaggle dataset (recommended)
poetry run python cli.py kaggle-load --path /path/to/dataset

# From GitHub repository
poetry run python cli.py github-load

# From YouTube channel (slow due to rate limits)
poetry run python cli.py scrape-channel "URL"

# Load local files
poetry run python -m src.data_loaders.local_loader
```

### Utilities

```bash
# Check for duplicates
poetry run python utils/check_duplicates.py

# Download Kaggle dataset
poetry run python utils/download_kaggle.py
```

## Next Steps

Now that data loading is organized, we can focus on:

1. **Vector Embeddings**: Add semantic search capabilities
2. **Chunking Strategies**: Implement different text chunking methods
3. **RAG Application**: Build question-answering system
4. **Analysis Tools**: Create analysis and visualization utilities
