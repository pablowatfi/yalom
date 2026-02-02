# Similarity Threshold Filtering

Advanced retrieval strategy that improves answer quality by filtering out irrelevant results.

## How It Works

### Traditional RAG (Before)
```
User asks question → Retrieve 7 vectors → Return all 7 → Generate answer
```
**Problem**: If only 4 are relevant, the other 3 mislead the LLM.

### Smart Filtering (Now)
```
User asks question
    ↓
Retrieve 21 candidates (7 × 3)
    ↓
Filter by similarity ≥ 0.5
    ↓
Return top 7 that passed threshold
    ↓
Generate answer with high-quality context
```

## Configuration

```python
# src/config.py
RAG_TOP_K = 7                    # Final number to return
RAG_RETRIEVAL_MULTIPLIER = 3     # Get 7×3=21 candidates
RAG_SIMILARITY_THRESHOLD = 0.5   # Filter threshold (0-1)
```

Via environment variables:
```bash
export RAG_TOP_K=7
export RAG_RETRIEVAL_MULTIPLIER=3
export RAG_SIMILARITY_THRESHOLD=0.5
```

## Similarity Score Ranges

For `sentence-transformers/all-MiniLM-L6-v2` (cosine similarity):

| Score Range | Quality | Meaning |
|-------------|---------|---------|
| 0.8 - 1.0 | ⭐⭐⭐ Excellent | Very relevant, high confidence |
| 0.6 - 0.8 | ⭐⭐ Good | Relevant, useful information |
| 0.5 - 0.6 | ⭐ Moderate | Potentially relevant |
| 0.3 - 0.5 | ❌ Weak | Probably not relevant |
| < 0.3 | ❌ Poor | Not relevant |

**Default threshold (0.5)** filters out weak and poor matches.

## Examples

### Example 1: Good Match (Sleep Topic)
```
Question: "What are Huberman's recommendations for sleep optimization?"

Retrieval: 40 candidates
Filtering: 40/40 passed threshold 0.5 ✅
Score range: 0.553 to 0.700
Final: 7 high-quality sources
```
**Result**: All retrieved vectors are relevant!

### Example 2: Vague Query (Quantum Physics)
```
Question: "quantum physics"

Retrieval: 46 candidates
Filtering: 0/46 passed threshold 0.5 ❌
Fallback: Return top 7 with relaxed threshold
```
**Result**: System detects poor matches, warns user, provides best available.

### Example 3: Specific Query (Dopamine Protocol)
```
Question: "dopamine fasting protocol recommendations"

Retrieval: 38 candidates
Filtering: 15/38 passed threshold 0.5 ✅
Score range: 0.512 to 0.685
Final: 7 sources
```
**Result**: Filtered out 23 irrelevant results, kept only good matches.

## Benefits

✅ **Quality**: Only returns relevant information
✅ **Adaptive**: Returns 1-7 sources based on actual relevance (not forced 7)
✅ **Prevents misleading**: Filters out unrelated topics
✅ **Transparent**: Logs show filtering stats
✅ **Configurable**: Easy to tune threshold
✅ **Fallback**: Never returns zero results (relaxes threshold if needed)

## Tuning the Threshold

### Lower Threshold (e.g., 0.3)
- **More permissive**: Returns more results
- **Use when**: Broad exploration, related topics acceptable
- **Risk**: May include tangentially related content

### Default Threshold (0.5)
- **Balanced**: Good mix of coverage and precision
- **Use when**: General Q&A (recommended default)
- **Sweet spot**: Filters weak matches, keeps moderate+ quality

### Higher Threshold (e.g., 0.7)
- **More strict**: Only highly relevant results
- **Use when**: Need high confidence, specific answers
- **Risk**: May filter out useful context

## Testing

Run the test to see filtering in action:

```bash
poetry run python test_similarity_filtering.py
```

Output shows:
- How many candidates retrieved
- How many passed threshold
- Score ranges
- Final selection

## Logs

Enable INFO logging to see filtering stats:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Example logs:
```
INFO: Retrieving 21 candidates per query for filtering...
INFO: Similarity filtering: 15/38 vectors passed threshold 0.5
INFO: Score range: 0.512 to 0.685
INFO: Final selection: 7 documents for context
```

## Future Enhancements

### Cross-Encoder Re-ranking (Coming Soon)
```python
RAG_RERANKING = True  # Enable more accurate re-ranking
```

Uses specialized model to re-score candidates:
- More accurate than initial bi-encoder similarity
- Scores each (question, passage) pair directly
- Slower (~100-200ms per query)
- Better precision for complex queries

## See Also

- [Query Rewriting](QUERY_REWRITING.md) - Multi-query retrieval
- [Configuration Guide](CONFIGURATION.md) - All config options
- [RAG Pipeline](src/rag/pipeline.py) - Implementation
