FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY README.md ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root --only main

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app/streamlit_app.py", \
  "--server.port=8501", \
  "--server.address=0.0.0.0", \
  "--server.headless=true", \
  "--browser.gatherUsageStats=false"]
