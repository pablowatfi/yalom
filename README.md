# Yalom - Huberman Lab AI Assistant

AI-powered search and Q&A system for Huberman Lab podcast transcripts using a local RAG pipeline and optional AWS deployment.

## ✨ What’s in the codebase

- **Ingestion** from YouTube, TapeSearch, Kaggle, and GitHub transcript sources
- **PostgreSQL** for transcript storage (Docker-ready)
- **Vectorization** pipeline with OpenAI embeddings (default: `text-embedding-3-small`)
- **Vector stores**: Qdrant (local) and Pinecone (cloud)
- **RAG pipeline** with query rewriting, similarity filtering, and prompt injection checks
- **Interfaces**: CLI tools, Streamlit UI (API mode), and AWS Lambdas

## ✅ Requirements

- Python 3.10+
- Poetry
- Docker (for Postgres/Qdrant)
- Optional: Groq/OpenAI API keys or Ollama for local LLMs

## 🚀 Quick start (local)

1. Install dependencies
   ```bash
   poetry install
   ```

2. Configure environment
   ```bash
   cp .env.example .env
   ```
   Update keys as needed (see Configuration below).

3. Start services
   ```bash
   docker-compose up -d
   ```

4. Initialize the database
   ```bash
   poetry run python scripts/cli.py init-db
   ```

5. Ingest transcripts (choose one)
   ```bash
   # GitHub transcripts (default repo)
   poetry run python scripts/cli.py github-load

   # Kaggle dataset (requires extracted folder)
   poetry run python scripts/cli.py kaggle-load --path /path/to/HubermanLabTranscripts

   # TapeSearch
   poetry run python scripts/cli.py tapesearch-scrape "Huberman Lab"

   # YouTube channel scrape
   poetry run python scripts/cli.py scrape-channel "https://www.youtube.com/@hubermanlab"
   ```

6. Build the vector store
   ```bash
   poetry run python scripts/populate_vector_db.py
   ```

7. Ask questions
   ```bash
   poetry run python scripts/chat_cli.py
   ```
   The CLI currently prompts for **Ollama** or **OpenAI**. Groq is supported by the core RAG pipeline for other entry points.

## 💬 Streamlit UI

The Streamlit app runs in **API mode only** and requires `API_BASE_URL` to point at a deployed API:

```bash
make run-streamlit
```

## 🛠️ Common Makefile commands

```bash
make help
make install
make test
make lint
make format
make docker-up
make docker-down
make run-streamlit
make run-cli ARGS="github-load"
make populate-db
```

## 📁 Project structure

```
yalom/
├── app/                    # Streamlit UI
├── aws/                    # AWS deployment assets
├── docs/                   # Documentation
├── scripts/                # CLI tools & utilities
├── src/                    # Core library code
│   ├── database/          # DB models & connections
│   ├── ingestion/         # Data fetching & scraping
│   ├── rag/               # RAG pipeline & prompts
│   └── vectorization/     # Embeddings & vector stores
├── tests/                  # Unit & integration tests
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## ⚙️ Configuration

See `.env.example` for the full list. Common settings:

- `DATABASE_URL` - PostgreSQL connection string
- `VECTOR_STORE` - `qdrant` or `pinecone`
- `QDRANT_URL`, `QDRANT_COLLECTION`
- `PINECONE_API_KEY`, `PINECONE_INDEX`, `PINECONE_ENVIRONMENT`
- `GROQ_YALOM_API_KEY` - Groq API key (RAG provider)
- `OPENAI_API_KEY` - OpenAI API key (RAG provider)
- `TAPESEARCH_API_KEY` - TapeSearch ingestion
- `API_BASE_URL` - Streamlit UI (API mode)

## ☁️ AWS deployment

The `aws/` folder contains Lambda handlers, Terraform, and a static UI deploy script. Start with:

- [aws/README.md](aws/README.md)
- [docs/AWS_DEPLOYMENT_COMPLETE.md](docs/AWS_DEPLOYMENT_COMPLETE.md)

## 📚 Documentation

- [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- [docs/QUERY_REWRITING.md](docs/QUERY_REWRITING.md)
- [docs/SIMILARITY_FILTERING.md](docs/SIMILARITY_FILTERING.md)
- [docs/GROQ_INTEGRATION.md](docs/GROQ_INTEGRATION.md)
- [docs/KAGGLE_DATASET_GUIDE.md](docs/KAGGLE_DATASET_GUIDE.md)
- [docs/GITHUB_FREE_SOLUTION.md](docs/GITHUB_FREE_SOLUTION.md)

## 📝 License

MIT License
