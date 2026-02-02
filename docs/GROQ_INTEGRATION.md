# Groq Integration Guide

Complete guide to integrate Groq (ultra-fast LLM inference) into your Yalom app.

## What is Groq?

Groq provides **the fastest LLM inference in the world** using their custom LPU (Language Processing Unit) hardware.

**Key Benefits:**
- ⚡ **10-50x faster** than OpenAI (500+ tokens/second vs 40-60 tokens/second)
- 🆓 **Free tier** more than sufficient (14,400 requests/day)
- 🎯 **High quality** models (Llama 3.1 70B comparable to GPT-4)
- 🚀 **Perfect for demos** where response speed matters

---

## Step 1: Get Your Groq API Key

### Sign Up (2 minutes)

1. **Go to Groq Console**: https://console.groq.com
2. **Click "Sign Up"** or "Get Started"
3. **Sign up with**:
   - Email
   - Or GitHub account
   - Or Google account
4. **Verify your email** (if using email signup)

### Get API Key

1. **After logging in**, you'll land on the dashboard
2. **Click "API Keys"** in the left sidebar
3. **Click "Create API Key"**
4. **Name your key**: e.g., `yalom-production`
5. **Copy the key**: Starts with `gsk_...`
6. **Save it securely**: You won't be able to see it again!

```
Example API Key:
gsk_1234567890abcdefghijklmnopqrstuvwxyz
```

---

## Step 2: Install Groq SDK

```bash
# Using pip
pip install groq

# Or add to requirements.txt
echo "groq>=0.4.0" >> requirements.txt
pip install -r requirements.txt

# Or using poetry (if using poetry)
poetry add groq
```

---

## Step 3: Update Your Code

### Option A: Minimal Changes (Add Groq Support)

Update your RAG pipeline to support Groq alongside existing providers:

**File: `src/rag/pipeline.py`**

```python
import os
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic

class RAGPipeline:
    def __init__(self):
        self.llm_provider = os.environ.get('LLM_PROVIDER', 'groq').lower()

        # Initialize appropriate client based on provider
        if self.llm_provider == 'groq':
            self.client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
            self.model = os.environ.get('GROQ_MODEL', 'llama-3.1-70b-versatile')
        elif self.llm_provider == 'openai':
            self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            self.model = os.environ.get('OPENAI_MODEL', 'gpt-4')
        elif self.llm_provider == 'anthropic':
            self.client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
            self.model = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

    def query(self, user_query: str, context: str = None):
        """
        Query the LLM with context from vector search
        """
        # Build messages
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in Andrew Huberman's podcast content. "
                          "Answer questions based on the provided context from his episodes."
            }
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context from Huberman Lab podcasts:\n\n{context}\n\n"
                          f"Question: {user_query}"
            })
        else:
            messages.append({"role": "user", "content": user_query})

        # Call appropriate API
        if self.llm_provider == 'groq':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False
            )
            return response.choices[0].message.content

        elif self.llm_provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content

        elif self.llm_provider == 'anthropic':
            # Anthropic has different API format
            system_msg = messages[0]['content']
            user_messages = messages[1:]

            response = self.client.messages.create(
                model=self.model,
                system=system_msg,
                messages=user_messages,
                max_tokens=1024,
                temperature=0.7
            )
            return response.content[0].text
```

### Option B: Groq-Only Implementation (Simpler)

If you only want to use Groq:

**File: `src/rag/pipeline.py`**

```python
import os
from groq import Groq

class RAGPipeline:
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.client = Groq(api_key=api_key)
        self.model = os.environ.get('GROQ_MODEL', 'llama-3.1-70b-versatile')

    def query(self, user_query: str, context: str = None):
        """
        Query Groq LLM with context from vector search
        """
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in Andrew Huberman's podcast content. "
                          "Answer questions based on the provided context from his episodes. "
                          "Be concise, accurate, and cite specific episodes when possible."
            }
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context from Huberman Lab podcasts:\n\n{context}\n\n"
                          f"Question: {user_query}"
            })
        else:
            messages.append({"role": "user", "content": user_query})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        return response.choices[0].message.content
```

---

## Step 4: Add Streaming Support (Optional)

For real-time responses in your Streamlit app:

**File: `src/rag/pipeline.py`**

```python
def query_stream(self, user_query: str, context: str = None):
    """
    Stream responses from Groq for real-time display
    """
    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant specialized in Andrew Huberman's podcast content."
        }
    ]

    if context:
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {user_query}"
        })
    else:
        messages.append({"role": "user", "content": user_query})

    stream = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        stream=True  # Enable streaming
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**Update Streamlit app to use streaming:**

**File: `app/streamlit_app.py`**

```python
import streamlit as st
from src.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

st.title("Huberman Lab AI Assistant")

user_query = st.text_input("Ask a question about Huberman Lab podcasts:")

if user_query:
    with st.spinner("Searching for relevant content..."):
        # Get context from vector search
        context = get_relevant_context(user_query)  # Your vector search function

    st.write("**Answer:**")

    # Stream the response
    response_placeholder = st.empty()
    full_response = ""

    for chunk in pipeline.query_stream(user_query, context):
        full_response += chunk
        response_placeholder.markdown(full_response + "▌")  # Cursor effect

    response_placeholder.markdown(full_response)
```

---

## Step 5: Set Environment Variables

### Local Development

**Create `.env` file:**

```bash
# Groq Configuration
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Optional: If supporting multiple providers
LLM_PROVIDER=groq

# Vector DB (Pinecone example)
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=yalom-transcripts

# OpenAI for embeddings (cheaper than alternatives)
OPENAI_API_KEY=sk_your_openai_key_for_embeddings_only
```

**Load environment variables:**

```python
# At top of your main files
from dotenv import load_dotenv
load_dotenv()
```

### AWS Lambda Deployment

```bash
# Set environment variables via AWS Console or CLI
aws lambda update-function-configuration \
  --function-name yalom-api \
  --environment Variables="{
    GROQ_API_KEY=gsk_your_key,
    GROQ_MODEL=llama-3.1-70b-versatile,
    PINECONE_API_KEY=your_key,
    OPENAI_API_KEY=sk_your_key
  }"
```

### Docker/Docker Compose

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL=llama-3.1-70b-versatile
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    env_file:
      - .env
```

---

## Available Groq Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **llama-3.1-70b-versatile** | 70B | Very Fast | ⭐⭐⭐⭐⭐ | **Recommended - Best balance** |
| llama-3.1-8b-instant | 8B | Fastest | ⭐⭐⭐⭐ | Quick responses, simpler queries |
| mixtral-8x7b-32768 | 47B | Fast | ⭐⭐⭐⭐ | Long context (32K tokens) |
| gemma-7b-it | 7B | Very Fast | ⭐⭐⭐ | Lightweight queries |
| llama-3.2-90b-vision-preview | 90B | Fast | ⭐⭐⭐⭐⭐ | Multimodal (text + images) |

**Recommendation:** Use `llama-3.1-70b-versatile` for best quality/speed balance.

---

## Testing Your Integration

### Quick Test Script

**File: `test_groq.py`**

```python
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def test_groq():
    client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is neuroplasticity in 2 sentences?"}
        ],
        temperature=0.7,
        max_tokens=100
    )

    print("Response:", response.choices[0].message.content)
    print(f"\nTokens used: {response.usage.total_tokens}")
    print(f"Model: {response.model}")

if __name__ == "__main__":
    test_groq()
```

**Run test:**

```bash
python test_groq.py
```

**Expected output:**

```
Response: Neuroplasticity refers to the brain's ability to reorganize itself by forming new neural connections throughout life. This process allows the brain to adapt, learn, and recover from injuries by modifying its structure and function in response to experiences and environmental changes.

Tokens used: 89
Model: llama-3.1-70b-versatile
```

---

## Rate Limits & Best Practices

### Free Tier Limits

```
Requests per day:    14,400 (way more than you need!)
Requests per minute: 300
Requests per second: 30
```

**Your usage:** ~100 queries/month = 3-4 queries/day ✅

### Best Practices

1. **Set reasonable max_tokens**: Don't request more than needed
2. **Use temperature 0.7-0.8**: Good balance for RAG
3. **Handle errors gracefully**: Add retry logic
4. **Cache common queries**: Reduce API calls

**Example with error handling:**

```python
from groq import Groq
import time

def query_with_retry(client, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

---

## Comparison: Before vs After

### Before (OpenAI GPT-4)

```python
# Cost: ~$6/month for 100 queries
# Speed: 40-60 tokens/second
# Response time: 5-10 seconds

from openai import OpenAI
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    temperature=0.7,
    max_tokens=1024
)
```

### After (Groq Llama 3.1 70B)

```python
# Cost: FREE (within limits)
# Speed: 500+ tokens/second
# Response time: 1-2 seconds

from groq import Groq
client = Groq(api_key=os.environ['GROQ_API_KEY'])

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[...],
    temperature=0.7,
    max_tokens=1024
)
```

**Same API interface, 10x faster, $0 cost!** ✨

---

## Troubleshooting

### Error: "Invalid API key"

```bash
# Check your API key is set
echo $GROQ_API_KEY

# Verify it starts with 'gsk_'
# Re-generate if needed at console.groq.com
```

### Error: "Rate limit exceeded"

```python
# Add exponential backoff
import time

def call_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "rate limit" in str(e).lower():
                wait = 2 ** i
                time.sleep(wait)
            else:
                raise
```

### Slow responses?

- Check your internet connection
- Reduce `max_tokens` if requesting too many
- Try a faster model like `llama-3.1-8b-instant`

---

## Next Steps

1. ✅ Get Groq API key
2. ✅ Install Groq SDK: `pip install groq`
3. ✅ Update your code (use Option A or B above)
4. ✅ Set environment variable: `GROQ_API_KEY=gsk_...`
5. ✅ Test with `test_groq.py`
6. ✅ Deploy to your chosen platform (Lambda, Cloud Run, etc.)

---

## Resources

- **Groq Console**: https://console.groq.com
- **Groq Docs**: https://console.groq.com/docs
- **Groq Python SDK**: https://github.com/groq/groq-python
- **Model Playground**: https://console.groq.com/playground

---

**You're all set!** 🚀 Your app will now use Groq's blazing-fast inference for free!
