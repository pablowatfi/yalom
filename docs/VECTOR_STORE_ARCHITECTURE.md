# Vector Store Hybrid Architecture

## Overview

Yalom uses a **hybrid vector store approach**:
- **Local Development**: Qdrant (Docker) - fast, offline, free
- **Production (AWS)**: Pinecone (cloud) - managed, scalable, ~$0.02/month

This follows industry best practices used by companies like Anthropic, OpenAI, and modern engineering teams.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│          Unified Vector Store Interface              │
│                 (Adapter Pattern)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  LOCAL DEV               PRODUCTION                  │
│  ┌────────────┐          ┌────────────┐            │
│  │  Qdrant    │          │  Pinecone  │            │
│  │  (Docker)  │          │  (Cloud)   │            │
│  └────────────┘          └────────────┘            │
│       ↓                        ↓                     │
│  Fast, Offline           Managed, Scalable          │
│  No cost                 $0.02/month                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Abstract Interface
**File**: `src/vectorization/vector_store_interface.py`

Defines common operations:
- `upsert()` - Insert/update vectors
- `search()` - Find similar vectors
- `delete()` - Remove vectors
- `get_stats()` - Get metrics
- `collection_exists()` - Check if exists
- `create_collection()` - Initialize

### 2. Qdrant Adapter
**File**: `src/vectorization/qdrant_adapter.py`

Local development implementation:
```python
from vectorization.factory import VectorStoreFactory

# Automatic from environment
store = VectorStoreFactory.create()  # Uses VECTOR_STORE=qdrant

# Explicit
store = VectorStoreFactory.create(
    'qdrant',
    url='http://localhost:6333'
)
```

### 3. Pinecone Adapter
**File**: `src/vectorization/pinecone_adapter.py`

Production implementation:
```python
# Automatic from environment
store = VectorStoreFactory.create()  # Uses VECTOR_STORE=pinecone

# Explicit
store = VectorStoreFactory.create(
    'pinecone',
    api_key='your-key'
)
```

### 4. Factory Pattern
**File**: `src/vectorization/factory.py`

Creates appropriate adapter based on configuration:
```python
# Environment-driven (best practice)
VECTOR_STORE=qdrant → QdrantVectorStore
VECTOR_STORE=pinecone → PineconeVectorStore
```

## Usage Examples

### Local Development (Qdrant)

```bash
# .env
VECTOR_STORE=qdrant

# Start Qdrant
docker-compose up -d qdrant

# Run app
poetry run streamlit run app/streamlit_app.py
```

### Production Testing (Pinecone)

```bash
# .env
VECTOR_STORE=pinecone
PINECONE_API_KEY=your-key

# Run app (uses Pinecone)
poetry run streamlit run app/streamlit_app.py
```

### In Code

```python
from vectorization.factory import VectorStoreFactory
from vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings

# Create vector store (auto-detects from env)
store = VectorStoreFactory.create()

# Use unified interface
embeddings = SimpleSentenceTransformerEmbeddings()
query_vector = embeddings.embed_query("What is neuroplasticity?")

results = store.search(
    query_vector=query_vector,
    top_k=5
)

for result in results:
    print(f"Score: {result.score}, Text: {result.metadata['text'][:100]}")
```

## Configuration

### Environment Variables

```bash
# Which vector store to use
VECTOR_STORE=qdrant  # or 'pinecone'

# Qdrant settings
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=huberman_transcripts

# Pinecone settings
PINECONE_API_KEY=your-key-here
PINECONE_INDEX=yalom-transcripts
PINECONE_ENVIRONMENT=gcp-starter
```

### Docker Compose (Local Qdrant)

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```

## Benefits

### ✅ Clean Architecture
- Single interface for all code
- Easy to switch providers
- No vendor lock-in
- Testable design

### ✅ Cost Efficiency
```
Development: $0 (Docker Qdrant)
Production:  $0.02/month (Pinecone free tier)
```

### ✅ Developer Experience
- Fast local queries (no network)
- Work offline
- No API rate limits during dev
- Instant feedback loop

### ✅ Production Ready
- Managed service (Pinecone)
- Auto-scaling
- High availability
- No DevOps overhead

### ✅ Testing Flexibility
```python
# Unit tests: Mock
store = MockVectorStore()

# Integration tests: Qdrant
store = VectorStoreFactory.create('qdrant')

# E2E tests: Pinecone
store = VectorStoreFactory.create('pinecone')
```

## Migration Path

### Data Migration: Qdrant → Pinecone

```python
from vectorization.factory import VectorStoreFactory

# Read from Qdrant
qdrant = VectorStoreFactory.create('qdrant')
# ... fetch all vectors ...

# Write to Pinecone
pinecone = VectorStoreFactory.create('pinecone', api_key='key')
pinecone.upsert(vectors)
```

### Gradual Rollout

1. **Week 1**: Test Pinecone locally
   ```bash
   VECTOR_STORE=pinecone poetry run pytest
   ```

2. **Week 2**: Deploy to staging
   ```bash
   # staging.env
   VECTOR_STORE=pinecone
   ```

3. **Week 3**: Production
   ```bash
   # production.env
   VECTOR_STORE=pinecone
   ```

## Performance Comparison

| Metric | Qdrant (Local) | Pinecone (Cloud) |
|--------|----------------|------------------|
| Query Latency | ~50ms | ~150ms |
| Throughput | Unlimited | 100K queries/month |
| Setup Time | 30 seconds | 5 minutes |
| Cost | $0 | $0.02/month |
| Scalability | Manual | Automatic |
| Availability | Dev machine | 99.9% SLA |

## Troubleshooting

### Qdrant Connection Error

```bash
# Check Docker
docker ps | grep qdrant

# Restart
docker-compose restart qdrant
```

### Pinecone API Error

```bash
# Check API key
echo $PINECONE_API_KEY

# Verify index exists
python -c "from pinecone import Pinecone; print(Pinecone(api_key='key').list_indexes())"
```

### Wrong Provider Selected

```bash
# Check current setting
echo $VECTOR_STORE

# Override temporarily
VECTOR_STORE=qdrant poetry run python script.py
```

## Best Practices

1. **Environment-driven config** - Never hardcode provider
2. **Test both providers** - Ensure adapters work identically
3. **Use factory pattern** - Never instantiate adapters directly
4. **Abstract in tests** - Mock the interface, not the implementation
5. **Monitor migrations** - Log all vector operations during transitions

## Future Extensions

### Add New Provider (e.g., Weaviate)

```python
# 1. Create adapter
class WeaviateVectorStore(VectorStore):
    # Implement interface methods
    pass

# 2. Update factory
elif provider == 'weaviate':
    return WeaviateVectorStore(...)

# 3. Use it
VECTOR_STORE=weaviate
```

### Multi-Provider Support

```python
# Primary + Fallback
PRIMARY_VECTOR_STORE=pinecone
FALLBACK_VECTOR_STORE=qdrant
```

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
