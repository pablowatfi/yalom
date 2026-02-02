# Free LLM Setup with Ollama

Run LLMs **100% free and local** - no API keys needed!

## Quick Start

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Or download from:** https://ollama.ai/download

### 2. Pull a model

```bash
# Recommended: Fast and good (3B params, ~2GB)
ollama pull llama3.2

# Alternative options:
ollama pull mistral        # 7B params, better quality, slower
ollama pull phi3           # 3.8B params, good for reasoning
ollama pull gemma2:2b      # 2B params, very fast
```

### 3. Verify it's running

```bash
ollama list
```

Should show your downloaded models.

### 4. Run the chat!

```bash
poetry run python chat_cli.py
```

Choose option `1` for Ollama.

## Model Recommendations

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2** | 3B (2GB) | ⚡⚡⚡ | ⭐⭐⭐ | **General use (recommended)** |
| mistral | 7B (4GB) | ⚡⚡ | ⭐⭐⭐⭐ | Better answers, slower |
| phi3 | 3.8B (2.3GB) | ⚡⚡⚡ | ⭐⭐⭐ | Reasoning tasks |
| gemma2:2b | 2B (1.6GB) | ⚡⚡⚡⚡ | ⭐⭐ | Very fast responses |

## Usage in Code

```python
from src.rag import RAGPipeline

# Use Ollama (free, local)
rag = RAGPipeline(
    llm_provider="ollama",
    model_name="llama3.2"  # or mistral, phi3, etc.
)

# Ask questions
result = rag.ask("What does Huberman say about sleep?")
print(result["answer"])
```

## Switching Between LLMs

It's super easy to switch:

```python
# Free local (Ollama)
rag = RAGPipeline(llm_provider="ollama", model_name="llama3.2")

# OpenAI (paid)
rag = RAGPipeline(llm_provider="openai", model_name="gpt-4o-mini", api_key="sk-...")
```

## Troubleshooting

**"Connection refused"**
```bash
# Start Ollama server
ollama serve
```

**"Model not found"**
```bash
# Download the model first
ollama pull llama3.2
```

**"Out of memory"**
- Use a smaller model (gemma2:2b)
- Close other applications
- Check available RAM: `ollama show llama3.2`

## Comparison: Ollama vs OpenAI

| Feature | Ollama | OpenAI |
|---------|--------|--------|
| **Cost** | 💰 FREE | ~$0.001/question |
| **Speed** | ⚡ Depends on hardware | ⚡⚡⚡ Very fast |
| **Privacy** | ✅ 100% local | ❌ Sent to API |
| **Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Setup** | Install once | Need API key |
| **Internet** | ❌ Not required | ✅ Required |

## Hardware Requirements

**Minimum:**
- 8GB RAM
- ~3GB free disk space
- CPU: Any modern processor

**Recommended:**
- 16GB RAM
- Apple Silicon or GPU (for faster inference)

## Advanced: Run Multiple Models

```bash
# Download multiple models
ollama pull llama3.2
ollama pull mistral
ollama pull phi3

# Switch easily in code
rag = RAGPipeline(llm_provider="ollama", model_name="mistral")
```

## Next Steps

Once Ollama is set up:

1. **Test it:** `poetry run python test_rag.py`
2. **Chat:** `poetry run python chat_cli.py`
3. **Experiment:** Try different models and see which works best for you!

## Cost Comparison

**Asking 100 questions:**
- Ollama: **$0.00** ✅
- OpenAI (gpt-4o-mini): **$0.10**
- OpenAI (gpt-4): **$1.50**

Ollama is perfect for development, testing, and personal use!
