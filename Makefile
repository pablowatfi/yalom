.PHONY: help install test lint format clean docker-up docker-down aws-deploy

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

# Repo root (directory containing this Makefile)
REPO_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

help: ## Show this help message
	@echo "$(BLUE)Yalom - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	poetry install
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

test: ## Run tests
	@echo "$(YELLOW)Running tests...$(NC)"
	poetry run pytest tests/ -v
	@echo "$(GREEN)✅ Tests complete$(NC)"

test-vector-store: ## Test vector store factory (Qdrant/Pinecone)
	@echo "$(YELLOW)Testing vector store...$(NC)"
	poetry run python tests/test_vector_store_factory.py

test-coverage: ## Run tests with coverage
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

lint: ## Run linting checks
	@echo "$(YELLOW)Running linters...$(NC)"
	poetry run ruff check src/ app/ scripts/ tests/
	@echo "$(GREEN)✅ Linting complete$(NC)"

format: ## Format code with black and ruff
	@echo "$(YELLOW)Formatting code...$(NC)"
	poetry run black src/ app/ scripts/ tests/
	poetry run ruff check --fix src/ app/ scripts/ tests/
	@echo "$(GREEN)✅ Code formatted$(NC)"

clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ dist/ build/
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

docker-up: ## Start Docker services (Qdrant)
	@echo "$(YELLOW)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Docker services started$(NC)"

docker-down: ## Stop Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Docker services stopped$(NC)"

docker-logs: ## Show Docker logs
	docker-compose logs -f

run-streamlit: ## Run Streamlit app locally
	@echo "$(YELLOW)Starting Streamlit app...$(NC)"
	poetry run streamlit run app/streamlit_app.py

run-cli: ## Run CLI (usage: make run-cli ARGS="your query")
	@echo "$(YELLOW)Running CLI...$(NC)"
	poetry run python scripts/cli.py $(ARGS)

populate-db: ## Populate vector database
	@echo "$(YELLOW)Populating database...$(NC)"
	poetry run python scripts/populate_vector_db.py
	@echo "$(GREEN)✅ Database populated$(NC)"

export-postgres-s3: ## Export Postgres transcripts to S3
	@echo "$(YELLOW)Exporting Postgres transcripts to S3...$(NC)"
	poetry run python scripts/export_postgres_to_s3.py
	@echo "$(GREEN)✅ Export complete$(NC)"

ingest-s3-local: ## Ingest S3 transcripts into Pinecone using local embeddings
	@echo "$(YELLOW)Ingesting S3 transcripts into Pinecone (local embeddings)...$(NC)"
	poetry run python scripts/ingest_s3_to_pinecone_local.py
	@echo "$(GREEN)✅ Ingestion complete$(NC)"

check-env: ## Check environment variables
	@echo "$(YELLOW)Checking environment...$(NC)"
	@poetry run python -c "import os; print('GROQ_YALOM_API_KEY:', 'set' if os.getenv('GROQ_YALOM_API_KEY') else 'NOT SET')"
	@echo "$(GREEN)✅ Environment check complete$(NC)"

aws-build: ## Build AWS Lambda packages
	@echo "$(YELLOW)Building Lambda packages...$(NC)"
	cd aws && ./build.sh
	@echo "$(GREEN)✅ Lambda packages built$(NC)"

aws-test-ingestion: ## Test ingestion Lambda locally
	@echo "$(YELLOW)Testing ingestion Lambda locally...$(NC)"
	poetry run python aws/test_ingestion_local.py

aws-test-query: ## Test query Lambda locally (usage: make aws-test-query QUERY="your question")
	@echo "$(YELLOW)Testing query Lambda locally...$(NC)"
	poetry run python aws/test_query_local.py $(QUERY)

aws-test: aws-test-query ## Run all Lambda local tests

aws-deploy: ## Deploy to AWS with Terraform
	@echo "$(YELLOW)Deploying to AWS...$(NC)"
	cd aws && ./deploy.sh
	@echo "$(GREEN)✅ Deployment complete$(NC)"

ui-deploy: ## Deploy static UI to S3 + CloudFront
	@echo "$(YELLOW)Deploying UI...$(NC)"
	cd aws && ./ui/deploy_ui.sh
	@echo "$(GREEN)✅ UI deployed$(NC)"

ui-on: ## Turn ON the CloudFront UI distribution
	@echo "$(YELLOW)Turning UI ON...$(NC)"
	cd aws && ./ui/ui_on.sh
	@echo "$(GREEN)✅ UI ON$(NC)"

ui-off: ## Turn OFF the CloudFront UI distribution
	@echo "$(YELLOW)Turning UI OFF...$(NC)"
	cd $(REPO_ROOT) && ./aws/ui/ui_off.sh
	@echo "$(GREEN)✅ UI OFF$(NC)"

aws-destroy: ## Destroy AWS infrastructure
	@echo "$(YELLOW)Destroying AWS infrastructure...$(NC)"
	cd aws/terraform && terraform destroy
	@echo "$(GREEN)✅ Infrastructure destroyed$(NC)"

dev: docker-up run-streamlit ## Start dev environment (Docker + Streamlit)

all: clean install test lint ## Run full CI pipeline
