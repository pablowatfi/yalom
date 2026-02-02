# AWS Deployment - Yalom

Complete Infrastructure as Code (IaC) for deploying Yalom to AWS Lambda + Pinecone.

## 📁 Structure

```
aws/
├── lambda_ingestion/       # Ingestion Lambda function
│   ├── handler.py          # Main Lambda handler
│   └── requirements.txt    # Python dependencies
├── lambda_query/           # Query Lambda function
│   ├── handler.py          # Main Lambda handler
│   └── requirements.txt    # Python dependencies
├── terraform/              # Infrastructure as Code
│   ├── main.tf             # Terraform configuration
│   └── terraform.tfvars.example  # Example variables
├── deploy.sh               # Automated deployment script
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Install tools:**
   ```bash
   # AWS CLI
   brew install awscli

   # Terraform
   brew install terraform

   # Python 3.11+
   brew install python@3.11
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Key, Region (us-east-1)
   ```

3. **Create Pinecone account:**
   - Sign up at https://www.pinecone.io/
   - Create index: `yalom-transcripts` (384 dimensions, cosine metric)
   - Get API key

4. **Get Groq API key:**
   - Sign up at https://console.groq.com/
   - Copy API key from dashboard

5. **Get OpenAI API key (embeddings):**
  - Sign up at https://platform.openai.com/
  - Create API key (used for embeddings)

### Deploy

1. **Configure Terraform variables:**
   ```bash
   cd aws/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your API keys
   ```

2. **Run deployment script:**
   ```bash
   cd aws
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Test deployment:**
   ```bash
   # The script will output the API endpoint
   curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/query \
     -H "Content-Type: application/json" \
     -d '{"query":"What is neuroplasticity?"}'
   ```

## 🌐 Static UI (S3 + CloudFront)

### Deploy UI

```bash
make ui-deploy
```

### Turn UI ON/OFF

```bash
make ui-on
make ui-off
```

### Get UI URL

```bash
cd aws/terraform
terraform output -raw ui_url
```

## 🛠️ Manual Deployment (Without Terraform)

If you prefer AWS CLI:

### 1. Build Lambda packages

```bash
cd aws

# Build ingestion Lambda
cd lambda_ingestion
pip install -r requirements.txt -t .
zip -r ../ingestion.zip .
cd ..

# Build query Lambda
cd lambda_query
pip install -r requirements.txt -t .
zip -r ../query.zip .
cd ..
```

### 2. Create S3 bucket

```bash
aws s3 mb s3://yalom-transcripts-backup
```

### 3. Create IAM role

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name YalomLambdaRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name YalomLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name YalomLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### 4. Deploy Lambda functions

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Deploy ingestion Lambda
aws lambda create-function \
  --function-name yalom-ingestion \
  --runtime python3.11 \
  --role arn:aws:iam::$ACCOUNT_ID:role/YalomLambdaRole \
  --handler handler.lambda_handler \
  --zip-file fileb://ingestion.zip \
  --timeout 900 \
  --memory-size 1024 \
  --environment Variables="{PINECONE_API_KEY=your_key,OPENAI_API_KEY=your_key,S3_BUCKET=yalom-transcripts-backup}"

# Deploy query Lambda
aws lambda create-function \
  --function-name yalom-query \
  --runtime python3.11 \
  --role arn:aws:iam::$ACCOUNT_ID:role/YalomLambdaRole \
  --handler handler.lambda_handler \
  --zip-file fileb://query.zip \
  --timeout 30 \
  --memory-size 1024 \
  --environment Variables="{PINECONE_API_KEY=your_key,GROQ_API_KEY=your_key,OPENAI_API_KEY=your_key}"
```

### 5. Create EventBridge rule

```bash
# Create weekly cron rule
aws events put-rule \
  --name yalom-weekly-ingestion \
  --schedule-expression "cron(0 10 ? * MON *)"

# Add Lambda as target
aws events put-targets \
  --rule yalom-weekly-ingestion \
  --targets "Id=1,Arn=arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:yalom-ingestion"

# Grant permission
aws lambda add-permission \
  --function-name yalom-ingestion \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/yalom-weekly-ingestion
```

### 6. Create API Gateway

```bash
# Create HTTP API
aws apigatewayv2 create-api \
  --name yalom-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:yalom-query

# Note the API endpoint from output
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AWS DEPLOYMENT                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📅 WEEKLY INGESTION                                     │
│  EventBridge → Lambda (yalom-ingestion)                 │
│    ↓                                                     │
│  1. Fetch transcripts                                    │
│  2. Generate embeddings (HuggingFace - free!)           │
│  3. Store in S3 (backup)                                 │
│  4. Upload to Pinecone                                   │
│                                                          │
│  💬 QUERY API                                            │
│  API Gateway → Lambda (yalom-query)                     │
│    ↓                                                     │
│  1. Query Pinecone                                       │
│  2. Call Groq API                                        │
│  3. Return response                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 💰 Cost Estimate

- **Lambda:** $0.00 (free tier)
- **S3:** $0.01/month
- **API Gateway:** $0.00 (free tier year 1)
- **EventBridge:** $0.00 (free tier)
- **Pinecone:** $0.00 (free tier)
- **Groq:** $0.00 (free tier)
- **Total:** ~$0.02/month 🎉

## 🔧 Development

### Update Lambda code

```bash
# After editing handler.py files:
cd aws
./deploy.sh
```

### Test Locally

Before deploying, test Lambda handlers on your machine:

```bash
# Test query Lambda (uses Pinecone + Groq)
make aws-test-query QUERY="What is sleep optimization?"

# Or with custom query
poetry run python aws/test_query_local.py "Tell me about dopamine"

# Test ingestion Lambda (requires Pinecone + valid video IDs)
make aws-test-ingestion

# Or directly
poetry run python aws/test_ingestion_local.py
```

**Requirements for local testing:**
- `PINECONE_API_KEY` environment variable
- `GROQ_API_KEY` or `GROQ_YALOM_API_KEY` environment variable
- Pinecone index created: `yalom-transcripts` (384 dimensions)

**What gets tested:**
- ✅ Handler imports from `src/` correctly
- ✅ Embeddings generation works
- ✅ Pinecone connection succeeds
- ✅ Groq API calls work
- ✅ Response format is valid

### View logs

```bash
# Ingestion logs
aws logs tail /aws/lambda/yalom-ingestion --follow

# Query logs
aws logs tail /aws/lambda/yalom-query --follow
```

### Test ingestion manually

```bash
aws lambda invoke \
  --function-name yalom-ingestion \
  --payload '{"video_ids":["VIDEO_ID_HERE"]}' \
  response.json

cat response.json
```

## 🧹 Cleanup

To destroy all resources:

```bash
cd aws/terraform
terraform destroy
```

## 📝 Notes

- Lambda packages include sentence-transformers (~80MB)
- Cold start time: 4-6 seconds
- Warm Lambda stays active for 5-15 minutes
- Pinecone free tier: 1M vectors, 100K queries/month
- Groq free tier: 14,400 requests/day

## 🐛 Troubleshooting

**Lambda timeout:**
- Increase timeout in `terraform/main.tf`
- Default: 900s (ingestion), 30s (query)

**Out of memory:**
- Increase `memory_size` in `terraform/main.tf`
- Current: 1024MB (minimum for sentence-transformers)

**API Gateway 502:**
- Check Lambda logs: `aws logs tail /aws/lambda/yalom-query`
- Verify environment variables are set

**Pinecone connection error:**
- Verify API key in `terraform.tfvars`
- Check index name matches: `yalom-transcripts`
- Verify dimensions: 384

## 📚 References

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Groq API Documentation](https://console.groq.com/docs)
