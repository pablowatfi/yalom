# Configuration Guide

All configuration is centralized in `src/config.py` and can be overridden with environment variables.

## Quick Start

```bash
# Copy example env file
cp .env.example .env

# Edit your settings
nano .env
```

## Key Settings

### Vectorization Performance

**For faster responses (recommended):**
```bash
CHUNK_SIZE=500          # Smaller chunks
CHUNK_OVERLAP=100       # Less overlap
RAG_TOP_K=5             # Fewer chunks
```

**For better context:**
```bash
CHUNK_SIZE=1000         # Larger chunks
CHUNK_OVERLAP=200       # More overlap
RAG_TOP_K=10            # More chunks
```

### Trade-offs

| Setting | Small (Fast) | Large (Context) |
|---------|--------------|-----------------|
| CHUNK_SIZE | 400-600 | 1000-1500 |
| CHUNK_OVERLAP | 80-120 | 200-300 |
| RAG_TOP_K | 3-5 | 8-12 |
| Response Time | ~5-10s | ~20-40s |
| Answer Quality | Precise | Comprehensive |

### Changing Settings

After modifying `CHUNK_SIZE` or `CHUNK_OVERLAP`, you must re-vectorize:

```bash
# Re-vectorize with new chunk settings
poetry run python clean_timestamps.py
```

After modifying `RAG_TOP_K` or `RAG_TEMPERATURE`, just restart the chat:

```bash
# No re-vectorization needed
poetry run python chat_cli.py
```

## Environment Variables

All settings can be overridden via environment variables:

```bash
# Quick test with different settings
CHUNK_SIZE=400 RAG_TOP_K=3 poetry run python populate_vector_db.py
```

## Default Values

See `.env.example` for all available settings and their defaults.
