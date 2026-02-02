# Vectorization Setup - LangChain + Qdrant

## Architecture

```
PostgreSQL (transcripts) → LangChain (chunking) → OpenAI (embeddings) → Qdrant (vector store)
```

## Components

### 1. **Chunking** (`src/vectorization/chunking.py`)
- Uses **LangChain text splitters**
- Strategies: Recursive, Character, Token-based
- Configurable chunk size and overlap
- Pre-configured profiles: QA, Search, Summary, Fine-grained

### 2. **Vector Store** (`src/vectorization/vector_store.py`)
- **Qdrant** integration via LangChain
- **OpenAI embeddings** (text-embedding-3-small by default)
- Operations: add, search, search_with_score, delete
- Collection management and filtering

### 3. **Pipeline** (`src/vectorization/pipeline.py`)
- End-to-end processing
- Batch processing from PostgreSQL
- Reprocessing capabilities
- Progress tracking and stats

## Quick Start

### 1. Set OpenAI API Key
```bash
export OPENAI_API_KEY="your-key-here"
```

### 2. Start Qdrant
```bash
docker-compose up -d qdrant
```

### 3. Test the Pipeline
```bash
poetry run python test_vectorization.py
```

## Usage Example

```python
from src.database import db, VideoTranscript
from src.vectorization import VectorStoreManager, VectorizationPipeline

# Initialize
db.connect()
session = db.get_session()

vector_store = VectorStoreManager(
    collection_name="huberman_transcripts",
    qdrant_url="http://localhost:6333",
    embedding_model="text-embedding-3-small"
)

vector_store.create_collection()

# Create pipeline
pipeline = VectorizationPipeline(
    vector_store_manager=vector_store,
    chunk_size=1000,
    chunk_overlap=200
)

# Process all transcripts
stats = pipeline.process_transcripts_batch(
    session=session,
    limit=10  # Start with 10 for testing
)

# Search
results = vector_store.search(
    query="How does dopamine affect motivation?",
    k=5
)

for doc in results:
    print(f"Video: {doc.metadata['video_id']}")
    print(f"Text: {doc.page_content[:200]}...")
    print()
```

## Configuration

### Chunking Strategies

```python
from src.vectorization import get_chunking_config

# Get pre-configured settings
qa_config = get_chunking_config("qa")
# {"chunk_size": 1000, "chunk_overlap": 200, "strategy": "recursive"}

search_config = get_chunking_config("search")
# {"chunk_size": 500, "chunk_overlap": 50, "strategy": "recursive"}
```

### Embedding Models

Available OpenAI models:
- `text-embedding-3-small` (1536 dim, $0.02/1M tokens) - **Default**
- `text-embedding-3-large` (3072 dim, $0.13/1M tokens) - Higher quality

## Qdrant Dashboard

Access at: http://localhost:6333/dashboard

## Next Steps

### Build RAG Application
1. Add LLM integration (OpenAI GPT-4, Claude, etc.)
2. Create retrieval chains
3. Implement question-answering
4. Add conversation memory

### Enhance Search
1. Hybrid search (vector + keyword)
2. Reranking strategies
3. Multi-query retrieval
4. Query expansion

### Production Optimization
1. Batch embedding for cost efficiency
2. Caching strategies
3. Incremental updates
4. Monitor and tune chunk sizes

## Cost Estimation

For 256 transcripts (~40M characters):

**Embedding Costs** (text-embedding-3-small):
- Chunks: ~40,000 (1000 char chunks with overlap)
- Tokens: ~10M tokens
- Cost: ~$0.20

**Qdrant**: Free (self-hosted in Docker)

## Dependencies Added

```toml
langchain = "^1.2.6"
langchain-community = "^0.4.1"
langchain-openai = "^1.1.7"
langchain-qdrant = "^1.1.0"
qdrant-client = "^1.16.2"
```

## Docker Services

```yaml
services:
  postgres:  # Main transcript database
    ports: ["5432:5432"]

  qdrant:    # Vector database
    ports: ["6333:6333", "6334:6334"]
```
