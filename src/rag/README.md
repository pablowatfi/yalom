# RAG (Retrieval-Augmented Generation) System

Ask questions about Huberman Lab podcasts and get AI-powered answers with source citations.

## How It Works

1. **User asks a question** → "What are the best supplements for sleep?"
2. **Vector search** → Finds 10 most relevant transcript chunks from 245 episodes
3. **Context building** → Extracts text from relevant chunks
4. **LLM generation** → Sends context + question to GPT-4
5. **Answer with sources** → Returns answer citing specific episodes

## Quick Start

### 1. Set your OpenAI API key

```bash
export OPENAI_API_KEY='sk-...'
```

### 2. Run the interactive chat

```bash
poetry run python chat_cli.py
```

### 3. Ask questions!

```
You: What does Huberman say about morning sunlight exposure?

🤔 Searching transcripts and generating answer...

ANSWER:
Andrew Huberman emphasizes that getting morning sunlight exposure within
30-60 minutes of waking is one of the most important things you can do for
your circadian rhythm and overall health...

SOURCES (5 transcript excerpts):
1. Master Your Sleep & Be More Alert When Awake
2. Optimize Your Learning & Creativity with Science-Based Tools
3. ...
```

## Usage Examples

### Interactive Chat (Recommended)

```bash
poetry run python chat_cli.py
```

Features:
- Maintains conversation history
- Type `reset` to clear history
- Type `quit` to exit

### Programmatic Usage

```python
from src.rag import RAGPipeline

# Initialize
rag = RAGPipeline(
    api_key="your-openai-key",
    model_name="gpt-4o-mini",  # Fast and cheap
    top_k=10,  # Number of chunks to retrieve
    temperature=0.7  # Creativity level
)

# Ask a question
result = rag.ask("How can I improve my focus?")

print(result["answer"])
print(f"Sources: {len(result['sources'])} episodes")

# Continue conversation
result2 = rag.ask("Can you elaborate on the dopamine aspect?")
```

### Simple Test

```bash
poetry run python test_rag.py
```

## Configuration

### Model Options

```python
# Fast and cheap (recommended)
RAGPipeline(model_name="gpt-4o-mini")  # ~$0.00015 per question

# More powerful
RAGPipeline(model_name="gpt-4o")  # ~$0.0025 per question

# Most capable
RAGPipeline(model_name="gpt-4-turbo")
```

### Retrieval Settings

```python
RAGPipeline(
    top_k=10,  # Number of chunks to retrieve (5-20 recommended)
    temperature=0.7  # 0 = factual, 1 = creative
)
```

## Architecture

```
src/rag/
├── __init__.py          # Module exports
├── pipeline.py          # Main RAG orchestration
└── (future)
    ├── custom_llm.py    # Support for other LLMs
    └── evaluation.py    # Answer quality metrics
```

## Cost Estimation

Using `gpt-4o-mini`:
- Input: ~$0.00015 per 1000 tokens
- Output: ~$0.0006 per 1000 tokens

Typical question:
- Retrieves 10 chunks × ~500 tokens = 5,000 tokens
- Answer: ~500 tokens
- **Cost per question: ~$0.001 (tenth of a cent)**

100 questions ≈ **$0.10**

## Features

✅ Retrieves relevant content from 245 episodes
✅ Cites sources (episode titles)
✅ Maintains conversation context
✅ Customizable prompt templates
✅ Multiple LLM options
✅ Free local embeddings (no cost for search)

## Tips

1. **Be specific**: "What supplements does Huberman recommend for sleep?" works better than "sleep"
2. **Follow up**: The system remembers context, so ask clarifying questions
3. **Reset when changing topics**: Use `reset` command to clear history
4. **Adjust top_k**: Increase for complex questions, decrease for faster responses

## Troubleshooting

**"No relevant information found"**
- Try rephrasing your question
- Make sure you've populated the vector database
- Check that Qdrant is running: `docker ps | grep qdrant`

**API errors**
- Verify OPENAI_API_KEY is set correctly
- Check you have API credits
- Try reducing top_k if rate limited

**Slow responses**
- Decrease top_k (try 5)
- Use gpt-4o-mini instead of gpt-4
