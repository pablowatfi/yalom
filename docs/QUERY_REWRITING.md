# Query Rewriting & Multilingual Support

Query rewriting is an intelligent retrieval enhancement that automatically converts user questions into multiple optimized search queries. Combined with automatic language detection and translation, this improves retrieval coverage and accuracy while supporting questions in any language.

## How It Works

### Query Rewriting Flow

```
User asks: "sleep stuff"
                ↓
Query Rewriter generates:
  1. sleep optimization protocols and sleep hygiene recommendations
  2. circadian rhythm and sleep quality improvement strategies
  3. sleep supplements and evening routines for better rest
                ↓
Search all 3 queries → Merge & deduplicate results
                ↓
Return top_k most relevant chunks
```

### Multilingual Translation Flow

```
User asks in Spanish: "¿Qué dice Huberman sobre el sueño?"
                ↓
1. Detect language: Spanish (es)
                ↓
2. Translate to English: "What does Huberman say about sleep?"
                ↓
3. Generate optimized queries (in English):
   - sleep recommendations and protocols
   - sleep quality and circadian rhythm
   - sleep supplements and evening routines
                ↓
4. Search vector DB (embeddings are in English)
                ↓
5. Retrieve relevant chunks
                ↓
6. Send English question + context to LLM
                ↓
7. Get answer in English
                ↓
8. Translate answer back to Spanish
                ↓
9. Return Spanish answer to user
```

**Why this approach?**
- ✅ Vector embeddings are all in English (Huberman Lab transcripts)
- ✅ Better retrieval accuracy (matches embedding language)
- ✅ LLM works better with English context
- ✅ Only translate the question and answer (not the entire context)
- ✅ Supports 20+ languages automatically

## Benefits

✅ **Better Coverage**: Finds documents that might be missed with single query
✅ **Varied Terminology**: Uses different phrasings (e.g., "focus" → "concentration", "cognitive performance")
✅ **Scientific Context**: Adds technical terms (e.g., "sleep" → "circadian rhythm")
✅ **Simple**: No complex agent loops, just 1 extra LLM call
✅ **Fast**: ~1 second overhead for query generation

## Configuration

### Enable/Disable

Edit [src/config.py](src/config.py):
```python
RAG_QUERY_REWRITING = True  # Enable (default)
```

Or via environment variable:
```bash
export RAG_QUERY_REWRITING=true
```

Or in `.env` file:
```
RAG_QUERY_REWRITING=true
```

### In Code

```python
from src.rag import RAGPipeline

# With query rewriting (default)
rag = RAGPipeline(query_rewriting=True)

# Without query rewriting
rag = RAGPipeline(query_rewriting=False)
```

## Performance Comparison

Run the test script to see the improvement:

```bash
poetry run python test_query_rewriting.py
```

Example output:
```
QUESTION: sleep tips

WITHOUT Query Rewriting:
  Retrieved: 4 unique episodes

WITH Query Rewriting:
  Retrieved: 6 unique episodes

Improvement: +2 episodes (better coverage)
```

## How Queries Are Generated

The system uses a carefully crafted prompt to generate 2-3 optimized queries:

1. **Expand vague terms**: "sleep stuff" → specific protocols, hygiene, supplements
2. **Add scientific terminology**: "focus" → "dopamine", "prefrontal cortex", "attention"
3. **Cover different aspects**: Single question → multiple search angles
4. **Keep concise**: 10-20 words each for precise matching

## Examples

| Original Question | Generated Queries |
|-------------------|-------------------|
| "sleep stuff" | 1. sleep optimization protocols and sleep hygiene<br>2. circadian rhythm and sleep quality improvement<br>3. sleep supplements and evening routines |
| "best supplements for focus" | 1. nootropics and cognitive enhancement supplements<br>2. focus and concentration supplement protocols<br>3. dopamine and attention improvement strategies |
| "dopamine" | 1. dopamine regulation and baseline optimization<br>2. dopamine receptors and neurotransmitter function<br>3. dopamine motivation and reward pathways |

## When to Disable

You might want to disable query rewriting if:

- ❌ **Very specific questions**: "What did guest John Smith say in episode 42?"
- ❌ **Speed critical**: Need fastest possible responses (saves ~1 second)
- ❌ **Debugging**: Troubleshooting retrieval issues
- ❌ **API costs**: Using paid LLM APIs (adds 1 extra call per question)

For most use cases, **keep it enabled** - the benefits outweigh the small overhead.

## Technical Details

### Implementation

- **Module**: [src/rag/query_rewriter.py](src/rag/query_rewriter.py)
- **Class**: `QueryRewriter`
- **Method**: `rewrite(question: str) -> List[str]`

### Deduplication

Retrieved documents are deduplicated by content hash:
- Query 1 finds docs [A, B, C]
- Query 2 finds docs [B, D, E]
- Query 3 finds docs [C, E, F]
- Merged result: [A, B, C, D, E, F] (no duplicates)
- Return top_k most relevant

### Error Handling

If query rewriting fails:
- ⚠️ Logs error
- ✅ Falls back to original question
- ✅ System continues working

## Monitoring

Enable logging to see generated queries:

```bash
export LOG_LEVEL=INFO
```

You'll see logs like:
```
INFO: Rewriting query: sleep stuff...
INFO: Generated 3 search queries:
INFO:   1. sleep optimization protocols and sleep hygiene
INFO:   2. circadian rhythm and sleep quality improvement
INFO:   3. sleep supplements and evening routines
INFO: Retrieved 6 unique documents from 3 queries
```

## vs Full Agents

Query rewriting gives you **80% of agent benefits** with **20% of the complexity**:

| Feature | Query Rewriting | Full Agents |
|---------|----------------|-------------|
| Better retrieval | ✅ | ✅ |
| Multi-step reasoning | ❌ | ✅ |
| External tools | ❌ | ✅ |
| Latency | +1 second | +5-10 seconds |
| Complexity | Low | High |
| Debuggability | Easy | Hard |
| Unpredictable behavior | No | Yes |

**Recommendation**: Start with query rewriting. Add full agents only if you need multi-step reasoning or external tools.

## See Also

- [RAG Pipeline](src/rag/pipeline.py) - Main RAG implementation
- [Configuration Guide](CONFIGURATION.md) - All config options
- [Prompt Versioning](PROMPT_VERSIONING.md) - Prompt management
