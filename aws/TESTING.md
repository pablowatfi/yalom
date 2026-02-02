# Testing AWS Lambda Functions Locally

## Quick Start

Test Lambda handlers before deploying to AWS:

```bash
# Test query handler
make aws-test-query QUERY="What is neuroplasticity?"

# Test ingestion handler
make aws-test-ingestion
```

## Prerequisites

1. **Environment variables:**
   ```bash
   export PINECONE_API_KEY=your-pinecone-key
   export GROQ_API_KEY=$GROQ_YALOM_API_KEY
   ```

2. **Pinecone index created:**
   - Name: `yalom-transcripts`
   - Dimensions: 384
   - Metric: cosine

3. **Dependencies installed:**
   ```bash
   poetry install
   ```

## Test Query Lambda

The query Lambda handles RAG queries via API Gateway.

### Basic Test
```bash
make aws-test-query
```

### Custom Query
```bash
make aws-test-query QUERY="How to improve sleep?"
```

### Direct Invocation
```bash
poetry run python aws/test_query_local.py "What is dopamine?"
```

### What It Tests
- ✅ Imports from `src/vectorization/` and `src/rag/`
- ✅ Embeddings generation (sentence-transformers)
- ✅ Pinecone connection and query
- ✅ Groq API call (llama-3.3-70b-versatile)
- ✅ Response format validation

### Expected Output
```
==========================================================
Testing Lambda Query Handler Locally
==========================================================

Query: What is neuroplasticity?
Context: yalom-query-test

==========================================================

Processing query: What is neuroplasticity?

==========================================================
Response:
==========================================================
Status Code: 200

✅ Answer:
Neuroplasticity refers to the brain's ability to reorganize itself...

📚 Sources (3):
   1. Video: dQw4w9WgXcQ
      Score: 0.852
      Preview: In this episode, we discuss the fundamental principles...
```

## Test Ingestion Lambda

The ingestion Lambda fetches transcripts and uploads to Pinecone.

### Basic Test
```bash
make aws-test-ingestion
```

### Direct Invocation
```bash
poetry run python aws/test_ingestion_local.py
```

### What It Tests
- ✅ Imports from `src/vectorization/`
- ✅ Text chunking (1000 chars, 100 overlap)
- ✅ Embeddings generation
- ✅ Pinecone upsert
- ✅ S3 backup (mocked locally)

### Expected Output
```
==========================================================
Testing Lambda Ingestion Handler Locally
==========================================================

Event: {
  "video_ids": ["dQw4w9WgXcQ"]
}

Context: yalom-ingestion-test

==========================================================

✅ Processed dQw4w9WgXcQ: 45 chunks

==========================================================
Response:
==========================================================
Status Code: 200
Body: {"message": "Successfully processed 1/1 videos", ...}
```

## Debugging

### Enable Verbose Logging
```bash
export LOG_LEVEL=DEBUG
make aws-test-query
```

### Check Pinecone Index
```python
from pinecone import Pinecone
pc = Pinecone(api_key="your-key")
index = pc.Index("yalom-transcripts")
print(index.describe_index_stats())
```

### Verify Embeddings
```python
from src.vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings

embeddings = SimpleSentenceTransformerEmbeddings()
vector = embeddings.embed_query("test")
print(f"Dimension: {len(vector)}")  # Should be 384
```

## Common Issues

**Import Error: No module named 'vectorization'**
```bash
# Handler needs src/ in the package
cd aws && ./build.sh  # Copies src/ to Lambda dirs
```

**Pinecone: Index not found**
```bash
# Create index first (one-time setup)
python -c "from pinecone import Pinecone; Pinecone(api_key='key').create_index('yalom-transcripts', dimension=384, metric='cosine')"
```

**Groq API Error**
```bash
# Check API key
echo $GROQ_YALOM_API_KEY
# Or set directly
export GROQ_API_KEY=gsk_your_key_here
```

**No results returned**
```bash
# Verify Pinecone has data
make populate-db  # Populate local Qdrant
# Then manually copy to Pinecone, or run ingestion
```

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Test Lambda Handlers
  env:
    PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
    GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  run: |
    make aws-test-query QUERY="test"
```

## Comparison: Local vs AWS

| Aspect | Local Testing | AWS Lambda |
|--------|--------------|------------|
| Event | Mocked dict | Real EventBridge/API Gateway |
| Context | MockContext class | Real Lambda context |
| Environment | Your machine | AWS Linux container |
| Cold Start | No | Yes (4-6 seconds) |
| Memory | Unlimited | 1024 MB |
| Timeout | Unlimited | 30s (query), 900s (ingestion) |
| Cost | Free | ~$0.02/month |

## Next Steps

1. ✅ Test locally
2. Build package: `make aws-build`
3. Deploy: `make aws-deploy`
4. Test live: `curl API_ENDPOINT`
5. Monitor: `aws logs tail /aws/lambda/yalom-query`
