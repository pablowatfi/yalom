#!/bin/bash
set -e

echo "🔨 Building AWS Lambda packages..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the repo root
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Create builds directory
mkdir -p builds

# Build in temp directories to avoid cluttering lambda folders
BUILD_ROOT=$(mktemp -d)

# Build ingestion Lambda
echo -e "\n${YELLOW}Building ingestion Lambda...${NC}"
INGEST_DIR="$BUILD_ROOT/ingestion"
mkdir -p "$INGEST_DIR"
cp lambda_ingestion/handler.py lambda_ingestion/requirements.txt "$INGEST_DIR/"
cp -R "$REPO_ROOT/src" "$INGEST_DIR/src"
python3 -m pip install -r lambda_ingestion/requirements.txt -t "$INGEST_DIR" \
	--upgrade \
	--platform manylinux2014_x86_64 \
	--implementation cp \
	--python-version 3.11 \
	--abi cp311 \
	--only-binary=:all:
cd "$INGEST_DIR"
zip -r "$REPO_ROOT/aws/builds/ingestion.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info/RECORD"
cd "$REPO_ROOT/aws"
echo -e "${GREEN}✅ Ingestion Lambda built ($(du -h builds/ingestion.zip | cut -f1))${NC}"

# Build query Lambda
echo -e "\n${YELLOW}Building query Lambda...${NC}"
QUERY_DIR="$BUILD_ROOT/query"
mkdir -p "$QUERY_DIR"
cp lambda_query/handler.py lambda_query/requirements.txt "$QUERY_DIR/"
cp -R "$REPO_ROOT/src" "$QUERY_DIR/src"
REQ_NO_LANG=$(mktemp)
grep -v '^langdetect' lambda_query/requirements.txt > "$REQ_NO_LANG"
python3 -m pip install -r "$REQ_NO_LANG" -t "$QUERY_DIR" \
	--upgrade \
	--platform manylinux2014_x86_64 \
	--implementation cp \
	--python-version 3.11 \
	--abi cp311 \
	--only-binary=:all:
rm "$REQ_NO_LANG"
python3 -m pip install langdetect==1.0.9 -t "$QUERY_DIR" --no-deps
cd "$QUERY_DIR"
zip -r "$REPO_ROOT/aws/builds/query.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info/RECORD"
cd "$REPO_ROOT/aws"
echo -e "${GREEN}✅ Query Lambda built ($(du -h builds/query.zip | cut -f1))${NC}"

# Cleanup temp build
echo -e "\n${YELLOW}Cleaning up...${NC}"
rm -rf "$BUILD_ROOT"

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "${YELLOW}Note: Lambda handlers now import from src/ (no code duplication)${NC}"
