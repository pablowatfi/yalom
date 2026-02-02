# Prompt Versioning System

All prompts are tracked with semantic versioning in `src/rag/prompts.py`.

## Quick Start

**View all prompt versions:**
```bash
poetry run python view_prompts.py
```

**View active prompt:**
```bash
poetry run python view_prompts.py --active
```

**View specific version:**
```bash
poetry run python view_prompts.py --show 1.0.0
```

## Version History

### v1.1.0 (Current)
- Added warning about informal speech and personal experiences
- Added instruction to not mention chapter names
- Date: 2026-01-26

### v1.0.0
- Initial prompt with conversation history support
- Basic instructions for Huberman Lab content
- Date: 2026-01-26

## Creating a New Version

1. Edit `src/rag/prompts.py`
2. Add new version to `PROMPTS` dict:

```python
"1.2.0": {
    "version": "1.2.0",
    "date": "2026-01-27",
    "changelog": "What changed from previous version",
    "system": """Your new system prompt here

    Context from Huberman Lab transcripts:
    {context}""",
    "human": "{question}"
}
```

3. Update `ACTIVE_VERSION = "1.2.0"`

4. Test with chat:
```bash
poetry run python chat_cli.py
# Check logs for: "Using prompt version: 1.2.0"
```

## Best Practices

### Semantic Versioning

- **Major (2.0.0)**: Complete rewrite, fundamentally different approach
- **Minor (1.1.0)**: New instructions, significant changes
- **Patch (1.0.1)**: Typo fixes, minor wording tweaks

### Changelog Guidelines

Be specific about what changed:
- ✅ "Added instruction to cite sources with timestamps"
- ❌ "Updated prompt"

### Testing New Prompts

Before making a version active:

1. Create the version but don't set as active
2. Test manually in code:
   ```python
   from src.rag.prompts import get_prompt
   prompt = get_prompt("1.2.0")  # Test version
   ```
3. Compare outputs
4. Set as active when satisfied

## Tracking in Git

Each prompt version should be committed separately:

```bash
git add src/rag/prompts.py
git commit -m "feat: Add prompt v1.2.0 - improve citation accuracy"
git tag prompt-v1.2.0
```

## Rollback

To rollback to a previous version:

```python
# In src/rag/prompts.py
ACTIVE_VERSION = "1.0.0"  # Change to desired version
```

No code changes needed - just update the version number!

## A/B Testing

To compare two prompts:

```python
from src.rag.prompts import get_prompt

# Test question
question = "What does Huberman say about sleep?"

# Version A
rag_a = RAGPipeline()  # Uses active version
result_a = rag_a.ask(question)

# Version B
prompt_b = get_prompt("1.0.0")
# Manually create RAG with old prompt
# Compare results...
```

## Monitoring

Future enhancement: Log prompt version with each query for analytics:

```python
{
    "question": "...",
    "answer": "...",
    "prompt_version": "1.1.0",
    "timestamp": "2026-01-26T10:00:00Z"
}
```
