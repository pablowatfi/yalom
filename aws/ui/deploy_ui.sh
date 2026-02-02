#!/bin/bash
set -e

AWS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$AWS_DIR/terraform"
UI_DIR="$AWS_DIR/ui"

API_ENDPOINT=$(cd "$TF_DIR" && terraform output -raw api_endpoint)
HISTORY_LIMIT=$(python -c "from src.config import RAG_HISTORY_LIMIT; print(RAG_HISTORY_LIMIT)")
TOP_K=$(python -c "from src.config import RAG_TOP_K; print(RAG_TOP_K)")
SIMILARITY_THRESHOLD=$(python -c "from src.config import RAG_SIMILARITY_THRESHOLD; print(RAG_SIMILARITY_THRESHOLD)")
UI_BUCKET=$(cd "$TF_DIR" && terraform output -raw ui_bucket_name)
UI_DIST_ID=$(cd "$TF_DIR" && terraform output -raw ui_distribution_id)

# Update config.js with API endpoint
cat > "$UI_DIR/config.js" <<EOF
// Set by deploy script
const API_ENDPOINT = "${API_ENDPOINT}";
const HISTORY_LIMIT = ${HISTORY_LIMIT};
const TOP_K = ${TOP_K};
const SIMILARITY_THRESHOLD = ${SIMILARITY_THRESHOLD};
EOF

# Sync UI to S3
aws s3 sync "$UI_DIR" "s3://$UI_BUCKET" --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id "$UI_DIST_ID" --paths "/*" >/dev/null

UI_URL=$(cd "$TF_DIR" && terraform output -raw ui_url)

echo "✅ UI deployed: ${UI_URL}"
