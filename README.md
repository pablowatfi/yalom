# Yalom - Huberman Lab AI Assistant

AI-powered search and Q&A system for Huberman Lab podcast transcripts using RAG (Retrieval-Augmented Generation).

## ✨ Features

- 🤖 **RAG Pipeline** - Intelligent Q&A with context retrieval
- 🔍 **Query Rewriting** - Enhanced search coverage
- 💬 **Streamlit Web UI** - Beautiful chat interface
- ⚡ **Groq API** - Fast LLM inference (free tier: 14,400 req/day)
- 🎯 **HuggingFace Embeddings** - Local, free sentence-transformers
- 🗄️ **Dual Vector Stores** - Qdrant (local) + Pinecone (AWS)
- ☁️ **AWS Serverless** - Lambda deployment (~$0.02/month)
- 🎥 **Multiple Sources** - YouTube, Kaggle, GitHub transcripts
- 📝 **Timestamped** - Precise source attribution
- 🐳 **Docker Ready** - One-command local setup

## 🚀 Quick Start

```bash
# 1. Install dependencies
make install

# 2. Set up environment
cp .env.example .env
# Edit .env and add: GROQ_YALOM_API_KEY=your-key

# 3. Start dev environment
make dev
# Opens Streamlit at http://localhost:8501
```

## 📁 Project Structure

```
yalom/
├── src/                    # Core library code
│   ├── database/          # Database models & connections
│   ├── ingestion/         # Data fetching & scraping
│   ├── rag/              # RAG pipeline & prompts
│   └── vectorization/    # Embeddings & vector store
├── app/                   # Streamlit web UI
├── scripts/              # CLI tools & utilities
├── tests/                # Unit & integration tests
├── aws/                  # AWS deployment (IaC)
│   ├── lambda_ingestion/ # Ingestion Lambda
│   ├── lambda_query/     # Query Lambda
│   ├── terraform/        # Terraform configs
│   └── deploy.sh        # Automated deployment
├── docs/                 # Documentation
└── Makefile            # Common development tasks
```

## 🛠️ Development Commands

```bash
make help              # Show all commands
make install          # Install dependencies
make test             # Run tests
make lint             # Run linting
make format           # Format code

make docker-up        # Start Qdrant
make docker-down      # Stop Qdrant
make run-streamlit    # Run Streamlit UI
make populate-db      # Populate vector database

make aws-deploy       # Deploy to AWS
```

## 📊 Data Sources

This project supports multiple transcript sources:

### 1. Kaggle Dataset (197 episodes)
- **Source**: https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts
- **Format**: Timestamped transcripts
- **Load**: `poetry run python utils/download_kaggle.py`

### 2. GitHub Repository (134 episodes)
- **Source**: https://github.com/prakhar625/huberman-podcasts-transcripts
- **Format**: Markdown transcripts
- **Load**: `poetry run python scripts/cli.py github-load`

### 3. YouTube Direct Scraping
- **Source**: YouTube API via youtube-transcript-api
- **Format**: Auto-generated captions
- **Load**: `poetry run python scripts/cli.py scrape-channel URL`
- ⚠️ **Note**: Rate limited, use Kaggle/GitHub instead

## ☁️ AWS Deployment

Deploy serverless infrastructure with Lambda + Pinecone:

```bash
# 1. Configure
cd aws/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit with your API keys

# 2. Deploy
make aws-deploy

# 3. Test
curl -X POST https://YOUR_API.execute-api.us-east-1.amazonaws.com/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is neuroplasticity?"}'
```

**Monthly Cost:** ~$0.02

See [aws/README.md](aws/README.md) for complete guide.

## 📚 Architecture

### Local Development
```
Streamlit UI → RAG Pipeline → Qdrant (Docker) → Groq API
                ↓
        HuggingFace Embeddings (all-MiniLM-L6-v2)
```

### AWS Production
```
API Gateway → Lambda → Pinecone → Response
               ↓
       Groq API + HuggingFace Embeddings
               ↓
       S3 (transcript backup)
```

## 📖 Documentation

- [AWS Deployment Guide](docs/AWS_DEPLOYMENT_COMPLETE.md)
- [Groq Integration](docs/GROQ_INTEGRATION.md)
- [Query Rewriting](docs/QUERY_REWRITING.md)
- [Configuration Options](docs/CONFIGURATION.md)
- [Kaggle Dataset Guide](docs/KAGGLE_DATASET_GUIDE.md)
- [GitHub Data Source](docs/GITHUB_FREE_SOLUTION.md)

## 🐛 Troubleshooting

**Qdrant not running:**
```bash
make docker-up
docker ps  # Verify qdrant container
```

**Groq API key error:**
```bash
export GROQ_YALOM_API_KEY="your-key-here"
make check-env
```

**NumPy compatibility:**
```bash
poetry add "numpy<2.0.0"
poetry install
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Make changes and test: `make test lint`
4. Format code: `make format`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing`
7. Open pull request

## 📝 License

MIT License

## 🙏 Credits

- **Data**: [Huberman Lab Podcast](https://hubermanlab.com/)
- **LLM**: [Groq](https://groq.com/) (llama-3.3-70b-versatile)
- **Embeddings**: [HuggingFace](https://huggingface.co/) (all-MiniLM-L6-v2)
- **Vector DB**: [Qdrant](https://qdrant.tech/) / [Pinecone](https://www.pinecone.io/)

---

Made with ❤️ for the Huberman Lab community

### Prerequisites

- Python 3.8.1+
- PostgreSQL (or Docker)
- Poetry

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

3. Start PostgreSQL:
   ```bash
   docker-compose up -d
   ```

4. Initialize the database:
   ```bash
   poetry run python cli.py init-db
   ```

## Usage

### Command Line Interface

**Scrape an entire channel:**
```bash
poetry run python cli.py scrape-channel "https://www.youtube.com/@channelname"
```

**Scrape with custom delay:**
```bash
poetry run python cli.py scrape-channel "https://www.youtube.com/@channelname" --delay 3
```

**Scrape a single video:**
```bash
poetry run python cli.py scrape-video VIDEO_ID
```

### Programmatic Usage

```python
from src import init_db, get_db_session, ChannelScraper

# Initialize database
init_db()

# Create a session and scraper
session = get_db_session()
scraper = ChannelScraper(session, delay=2)

# Scrape a channel
stats = scraper.scrape_channel("https://www.youtube.com/@channelname")
print(f"Successfully scraped {stats['success']} videos")

session.close()
```

## Project Structure

```
yalom/
├── src/                    # Main source code
│   ├── config.py           # Configuration settings
│   ├── database/           # Database models and connections
│   ├── ingestion/          # Data ingestion logic
│   ├── vectorization/      # Embedding and vector storage
│   └── rag/                # RAG pipeline and prompts
├── app/                    # Applications
│   └── streamlit_app.py    # Web UI
├── scripts/                # Utility scripts
│   ├── chat_cli.py         # Terminal chat interface
│   ├── populate_vector_db.py  # Vectorize transcripts
│   ├── clean_timestamps.py # Clean transcript timestamps
│   └── view_prompts.py     # View prompt versions
├── tests/                  # Test files
│   ├── test_rag.py
│   ├── test_multilingual.py
│   ├── test_similarity_filtering.py
│   └── ...
├── migrations/             # Database migrations
├── docs/                   # Documentation
│   ├── CONFIGURATION.md
│   ├── QUERY_REWRITING.md
│   ├── SIMILARITY_FILTERING.md
│   └── ...
├── cli.py                  # Command-line interface
├── docker-compose.yml      # PostgreSQL container config
├── pyproject.toml          # Poetry dependencies
└── README.md
```

## Configuration

Environment variables (optional, see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Best Practices Implemented

- ✅ Separation of concerns (models, database, business logic)
- ✅ Type hints throughout
- ✅ Comprehensive logging
- ✅ Context managers for resource management
- ✅ Error handling and retries
- ✅ Configuration management
- ✅ Documentation and docstrings
- ✅ Production-ready database (PostgreSQL)
- ✅ Rate limiting to respect YouTube's limits
