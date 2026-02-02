# Web UI

Beautiful chat interface for the Huberman Lab AI Assistant using Streamlit.

## Quick Start

**1. Make sure Ollama is running:**
```bash
ollama serve
ollama pull llama3.2
```

**2. Launch the web UI:**
```bash
poetry run streamlit run web_ui.py
```

The app will open in your browser at `http://localhost:8501`

## Features

✅ **Chat Interface**: Ask questions and see answers in real-time
✅ **Conversation History**: Full dialog preserved during session
✅ **Source Citations**: Expandable sources for each answer
✅ **LLM Provider Choice**: Switch between Ollama (free) and OpenAI
✅ **Reset Button**: Clear conversation and start fresh
✅ **Responsive Design**: Works on desktop and mobile

## Screenshots

### Main Chat Interface
- Clean chat bubbles for questions and answers
- Collapsible source citations
- Persistent conversation history

### Sidebar Settings
- LLM provider selection (Ollama/OpenAI)
- Model selection
- API key input (for OpenAI)
- Reset conversation button
- Live statistics

## Configuration

Settings are loaded from `src/config.py`:
- `RAG_TOP_K`: Number of chunks to retrieve (default: 5)
- `RAG_TEMPERATURE`: LLM creativity (default: 0.7)

To change chunking parameters, edit `.env` or `src/config.py` and re-vectorize.

## Using OpenAI Instead of Ollama

1. Click "openai" in the sidebar
2. Enter your OpenAI API key
3. Select a model (gpt-4o-mini recommended)
4. Start chatting

Cost: ~$0.001 per question with gpt-4o-mini

## Deployment

### Local Network Access

Make the UI available to other devices on your network:

```bash
poetry run streamlit run web_ui.py --server.address 0.0.0.0
```

Access from other devices: `http://YOUR_IP:8501`

### Cloud Deployment

**Streamlit Community Cloud (Free):**
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Deploy from your repo
4. Add secrets for API keys

**Note:** For Ollama, you'll need a VM with Docker (see Oracle Cloud guide)

## Keyboard Shortcuts

- `Ctrl/Cmd + K`: Focus chat input
- `Enter`: Send message
- `Ctrl/Cmd + R`: Reload app

## Troubleshooting

**"Failed to initialize":**
- Check Ollama is running: `ollama list`
- Verify model is installed: `ollama pull llama3.2`
- Check Qdrant is running: `docker ps | grep qdrant`

**Slow responses:**
- Reduce `RAG_TOP_K` in config (less chunks = faster)
- Try a smaller model: `phi3` or `gemma2:2b`

**NumPy errors:**
```bash
poetry run pip uninstall -y numpy && poetry run pip install "numpy<2"
```

## Development

**Auto-reload on code changes:**
Streamlit automatically reloads when you edit `web_ui.py`

**Debug mode:**
```bash
poetry run streamlit run web_ui.py --server.runOnSave true
```

## Next Steps

- [ ] Add export conversation feature
- [ ] Add favorite questions
- [ ] Add dark mode toggle
- [ ] Add mobile-optimized layout
- [ ] Add voice input support
