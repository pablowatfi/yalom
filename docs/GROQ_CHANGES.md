# Groq Integration - Changes Summary

## What Was Changed

Your Yalom app now uses **Groq API** with the **llama-3.1-70b-versatile** model by default for ultra-fast, free LLM inference.

### Files Modified

1. **pyproject.toml**
   - Added `langchain-groq = "^0.3.1"` to dependencies

2. **src/rag/pipeline.py**
   - Added `import os` for environment variable reading
   - Added `from langchain_groq import ChatGroq` import
   - Updated default `llm_provider` from `"ollama"` to `"groq"`
   - Added Groq initialization with automatic `GROQ_YALOM_API_KEY` reading
   - Auto-selects `llama-3.1-70b-versatile` model for Groq
   - Updated docstrings to list Groq as primary option

3. **app/streamlit_app.py**
   - Changed default provider to `"groq"`
   - Changed default model to `"llama-3.1-70b-versatile"`
   - Added Groq option to sidebar radio buttons
   - Added Groq-specific UI with API key input and model selector
   - Reads from `GROQ_YALOM_API_KEY` environment variable

4. **test_groq_integration.py** (NEW)
   - Created test script to verify Groq integration
   - Tests API key, pipeline initialization, and query execution

---

## How to Use

### 1. Set Your API Key

```bash
export GROQ_YALOM_API_KEY=gsk_your_api_key_here
```

**Get your API key from:** https://console.groq.com

### 2. Install Dependencies

```bash
poetry install
```

### 3. Test the Integration

```bash
poetry run python test_groq_integration.py
```

### 4. Run the Streamlit App

```bash
poetry run streamlit run app/streamlit_app.py
```

The app will now default to Groq with the llama-3.1-70b-versatile model!

---

## Available Models (Free Tier)

In the Streamlit UI, you can choose from:

- **llama-3.1-70b-versatile** (Recommended - Best quality)
- **llama-3.1-8b-instant** (Fastest - Good for quick responses)
- **mixtral-8x7b-32768** (Long context - 32K tokens)

All models are free within Groq's generous limits (14,400 requests/day).

---

## API Key Environment Variable

The code looks for the API key in this order:

1. `api_key` parameter passed to `RAGPipeline()`
2. `GROQ_YALOM_API_KEY` environment variable
3. If neither is found, raises an error

### Setting it Permanently

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export GROQ_YALOM_API_KEY=gsk_your_key_here
```

Then reload:
```bash
source ~/.zshrc
```

---

## Code Examples

### Basic Usage

```python
from src.rag.pipeline import RAGPipeline

# Uses Groq by default, reads GROQ_YALOM_API_KEY automatically
pipeline = RAGPipeline()

result = pipeline.ask("What is neuroplasticity?")
print(result['answer'])
```

### With Explicit API Key

```python
pipeline = RAGPipeline(
    llm_provider="groq",
    model_name="llama-3.1-70b-versatile",
    api_key="gsk_your_key_here"
)
```

### Using Different Model

```python
# For fastest responses
pipeline = RAGPipeline(
    model_name="llama-3.1-8b-instant"
)

# For long context (32K tokens)
pipeline = RAGPipeline(
    model_name="mixtral-8x7b-32768"
)
```

---

## Benefits of Groq

✅ **Free** - 14,400 requests/day (way more than you need)
✅ **Ultra-fast** - 500+ tokens/second (10x faster than OpenAI)
✅ **High quality** - llama-3.1-70b comparable to GPT-4
✅ **No local setup** - No need to run Ollama locally
✅ **Perfect for demos** - Blazing fast responses impress interviewers

---

## Troubleshooting

### Error: "Groq requires api_key parameter"

**Solution:** Set the environment variable:
```bash
export GROQ_YALOM_API_KEY=gsk_your_key_here
```

### Error: "Rate limit exceeded"

**Solution:** You've hit the free tier limit (unlikely with 14,400 req/day). Wait or upgrade.

### Streamlit not showing Groq option

**Solution:** Restart Streamlit:
```bash
# Stop with Ctrl+C, then:
poetry run streamlit run app/streamlit_app.py
```

---

## Next Steps

1. ✅ Get your Groq API key from https://console.groq.com
2. ✅ Set `GROQ_YALOM_API_KEY` environment variable
3. ✅ Run `poetry install` to install dependencies
4. ✅ Test with `poetry run python test_groq_integration.py`
5. ✅ Launch app with `poetry run streamlit run app/streamlit_app.py`
6. ✅ Select "groq" in the sidebar (should be default)
7. ✅ Enjoy ultra-fast free LLM responses!

---

**Ready to go!** Your app is now powered by Groq's blazing-fast inference. 🚀
