# AWS Lambda Architecture

## DRY Principle - Single Source of Truth

The Lambda functions follow **Don't Repeat Yourself (DRY)** principles:

### Structure
```
yalom/
├── src/                          # ✅ Single source of truth
│   ├── vectorization/
│   │   ├── simple_embeddings.py  # Embeddings logic
│   │   └── chunking.py           # Text chunking
│   └── rag/
│       └── prompts.py            # System prompts
│
├── aws/
│   ├── lambda_ingestion/
│   │   └── handler.py            # ⚠️ Thin wrapper (imports from src/)
│   ├── lambda_query/
│   │   └── handler.py            # ⚠️ Thin wrapper (imports from src/)
│   └── build.sh                  # Copies src/ during build
```

### How It Works

1. **Development**: All logic lives in `src/`
   - Embeddings: `src/vectorization/simple_embeddings.py`
   - Chunking: `src/vectorization/chunking.py`
   - Prompts: `src/rag/prompts.py`

2. **Lambda Handlers**: Thin wrappers that import from `src/`
   ```python
   # aws/lambda_query/handler.py
   from vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings
   from rag.prompts import get_active_prompt
   ```

3. **Build Process**: `build.sh` copies `src/` into Lambda packages
   ```bash
   cp -r $REPO_ROOT/src lambda_ingestion/
   cp -r $REPO_ROOT/src lambda_query/
   # ... build zip files ...
   rm -rf lambda_*/src  # cleanup
   ```

4. **Deployment**: Lambda packages include both handler + src/
   ```
   ingestion.zip
   ├── handler.py
   ├── src/
   │   ├── vectorization/
   │   └── rag/
   └── dependencies/
   ```

### Benefits

✅ **No Code Duplication**
- Embeddings logic written once in `src/vectorization/`
- RAG prompts maintained in one place: `src/rag/prompts.py`

✅ **Consistent Behavior**
- Local Streamlit app uses same code as AWS Lambda
- Changes in `src/` automatically apply to both

✅ **Easy Testing**
- Test `src/` modules directly
- Lambda handlers become trivial integration tests

✅ **Maintainability**
- Fix bugs once in `src/`
- Update prompts once in `src/rag/prompts.py`

### Development Workflow

```bash
# 1. Make changes in src/
vim src/vectorization/simple_embeddings.py

# 2. Test locally
make test

# 3. Deploy to AWS (automatically includes src/)
make aws-deploy
```

### What Gets Packaged

**Before DRY refactor:**
- 🔴 Embeddings code duplicated in both handler.py files
- 🔴 Chunking logic duplicated
- 🔴 Prompts hardcoded in handlers

**After DRY refactor:**
- ✅ Handler imports from src/
- ✅ src/ copied during build
- ✅ Single source of truth maintained

### File Sizes

```
Without src/ reuse:
  ingestion.zip: ~120MB (deps + duplicated logic)
  query.zip:     ~120MB (deps + duplicated logic)

With src/ reuse:
  ingestion.zip: ~121MB (deps + src/ ~1MB)
  query.zip:     ~121MB (deps + src/ ~1MB)
```

Minimal size increase, massive maintainability gain!

## Example: Changing Embeddings Model

**Before (BAD - change in 3 places):**
```python
# src/vectorization/simple_embeddings.py
model = "all-MiniLM-L6-v2"

# aws/lambda_ingestion/handler.py
model = SentenceTransformer("all-MiniLM-L6-v2")  # 😱 duplicated

# aws/lambda_query/handler.py
model = SentenceTransformer("all-MiniLM-L6-v2")  # 😱 duplicated
```

**After (GOOD - change in 1 place):**
```python
# src/vectorization/simple_embeddings.py
model = "all-MiniLM-L6-v2"

# aws/lambda_ingestion/handler.py
from vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings
embeddings = SimpleSentenceTransformerEmbeddings()  # ✅ uses src/

# aws/lambda_query/handler.py
from vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings
embeddings = SimpleSentenceTransformerEmbeddings()  # ✅ uses src/
```

Change once, applies everywhere!
