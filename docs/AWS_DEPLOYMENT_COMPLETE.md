# Complete AWS Deployment Guide - Yalom with Groq

**Comprehensive guide to deploy your Huberman Lab AI Assistant on AWS with minimal cost.**

---

## 📊 Your Requirements Analysis

Based on your use case:
- **Weekly ingestion**: Automated podcast transcript ingestion (1x/week, ~5-10 minutes)
- **On-demand queries**: 2 hours/week for interviews/demos (~100 queries/month)
- **Vector DB runtime**: Only needed when serving queries (not for ingestion)
- **LLM**: Groq API (FREE - already configured)
- **Embeddings**: OpenAI text-embedding-3-small (~$0.01/month for 100 queries)

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     AWS DEPLOYMENT                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📅 WEEKLY INGESTION PIPELINE                           │
│  ┌──────────────────────────────────────────────┐      │
│  │ EventBridge (cron) → Lambda (15 min)         │      │
│  │    ↓                                          │      │
│  │ 1. Fetch new transcripts                      │      │
│  │ 2. Generate embeddings (HuggingFace)          │      │
│  │ 3. Store in S3 (backup)                       │      │
│  │ 4. Upload to Pinecone (serverless vector DB)  │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
│  💬 ON-DEMAND RAG APP                                   │
│  ┌──────────────────────────────────────────────┐      │
│  │ API Gateway → Lambda (query handler)          │      │
│  │    ↓                                          │      │
│  │ 1. Query Pinecone (always available)          │      │
│  │ 2. Call Groq API (free)                       │      │
│  │ 3. Return response                            │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Comparison - 3 Options

### Option 1: Lambda + S3 + Pinecone (Serverless) ✅ **RECOMMENDED**

**Architecture:**
- Lambda for ingestion and queries
- S3 for transcript storage
- Pinecone free tier (serverless vector DB)
- Groq for LLM (free)
- OpenAI for embeddings

**Monthly Cost Breakdown:**
```
EventBridge (weekly trigger):    $0.00 (1M free/month)
Lambda (ingestion):              $0.00 (1M free requests, 400K GB-sec free)
  - 4 invocations/month × 5 min each = well under free tier
  - Using 1024 MB memory for embeddings
Lambda (queries):                $0.00 (100 queries × 3 sec = 300 sec)
  - 100 requests = 0.0001% of 1M free tier
  - Using 1024 MB memory for embeddings model (~80MB package)
API Gateway:                     $0.00 (1M free requests first year, then $0.0004)
  - After year 1: 100 × $0.0000035 = $0.00035
S3 Storage:                      $0.023/GB × 0.5 GB = $0.01
S3 Requests:                     $0.00 (negligible)
Pinecone (free tier):            $0.00 (1M vectors, 100K queries/month)
OpenAI Embeddings:               ~$0.01/month
  - text-embedding-3-small: 384 dimensions
Groq API:                        $0.00 (free tier: 14,400 req/day)
CloudWatch Logs:                 $0.01 (5 GB free ingestion)
────────────────────────────────────────────────
TOTAL (Year 1):                  ~$0.03/month 💰
TOTAL (Year 2+):                 ~$0.03/month 💰
```

**Pros:**
- ✅ Essentially FREE (~$0.03/month)
- ✅ No cold starts for vector DB (Pinecone always available)
- ✅ Zero maintenance
- ✅ Auto-scales infinitely
- ✅ Perfect for demos (fast, reliable)
- ✅ Simple managed embeddings (OpenAI)

**Cons:**
- ⚠️ Lambda cold starts (2-4 seconds first request)
- ⚠️ Pinecone free tier limits (1M vectors max)
- ⚠️ Requires internet access to Pinecone

---

### Option 2: Lambda + S3 + ECS Fargate On-Demand (Qdrant)

**Architecture:**
- Lambda for queries triggers ECS Fargate task
- ECS runs Qdrant in container on-demand
- Auto-shutdown after inactivity

**Monthly Cost Breakdown:**
```
Lambda (ingestion):              $0.00 (free tier)
Lambda (query handler):          $0.00 (free tier)
API Gateway:                     $0.00 (free tier)
S3 Storage:                      $0.01
ECS Fargate (on-demand):
  - 0.25 vCPU, 0.5 GB RAM
  - $0.01245/hour (vCPU) + $0.00136/hour (memory)
  - 2 hours/week × 4 weeks = 8 hours/month
  - 8 × $0.01381 = $0.11
ECR (image storage):             $0.00 (0.5 GB free)
CloudWatch Logs:                 $0.01
HuggingFace Embeddings:          $0.00 (local, free)
Groq API:                        $0.00
────────────────────────────────────────────────
TOTAL:                           ~$0.13/month
```

**Pros:**
- ✅ Still very cheap (~$0.13/month)
- ✅ Full control over Qdrant
- ✅ Can use larger models
- ✅ Data stays in your VPC

**Cons:**
- ⚠️ Cold start ~30-60 seconds (ECS task startup)
- ⚠️ More complex setup
- ⚠️ Need to implement auto-shutdown logic
- ⚠️ Vector data persistence requires EFS ($0.30/GB/month)

---

### Option 3: ECS Fargate Always-On (Streamlit App)

**Architecture:**
- ECS Fargate running 24/7
- Streamlit web UI
- Qdrant in same container or separate

**Monthly Cost Breakdown:**
```
ECS Fargate (24/7):
  - 0.25 vCPU, 1 GB RAM
  - $0.01245/hour (vCPU) + $0.00273/hour (memory)
  - 720 hours/month × $0.01518 = $10.93
Application Load Balancer:       $16.20 (not needed if using ALB)
  - OR CloudFront + API Gateway: $0.00 (free tier)
S3 Storage:                      $0.01
CloudWatch Logs:                 $0.05
HuggingFace Embeddings:          $0.00 (local, free)
Groq API:                        $0.00
────────────────────────────────────────────────
TOTAL (with ALB):                ~$27.29/month
TOTAL (without ALB):             ~$11.09/month
```

**Pros:**
- ✅ No cold starts
- ✅ Streamlit UI available 24/7
- ✅ Consistent performance

**Cons:**
- ❌ Expensive for 2 hrs/week usage
- ❌ Wasted resources 99% of the time
- ❌ Not cost-effective for your use case

---

## 🏆 RECOMMENDED: Option 1 - Serverless with Pinecone

**Why this is best for you:**
1. **Cost**: ~$0.02/month (essentially free)
2. **Reliability**: No vector DB cold starts
3. **Simplicity**: Minimal moving parts
4. **Scalability**: Handles traffic spikes automatically
5. **Maintenance**: Zero ongoing management

---

## 📦 Complete Implementation Guide

### ✅ Recommended (IaC): One-Command Deployment

For **minimum cost and zero manual steps**, use the Infrastructure-as-Code setup in the repo:

- [aws/README.md](../aws/README.md)
- [aws/terraform/main.tf](../aws/terraform/main.tf)

**Deploy with one command:**

```bash
make aws-deploy
```

This runs the full pipeline:
1. Builds Lambda packages
2. Provisions S3, IAM, Lambda, EventBridge, API Gateway
3. Outputs your API endpoint

---

### (Optional) Manual Steps via AWS CLI

### Step 1: Setup AWS Account & CLI

```bash
# Install AWS CLI
brew install awscli

# Configure credentials
aws configure
# Enter: Access Key ID, Secret Key, Region (us-east-1)
```

### Step 2: Setup Pinecone (Free Tier)

1. **Sign up**: https://www.pinecone.io/
2. **Create Index**:
   - Name: `yalom-transcripts`
  - Dimensions: `384` (OpenAI text-embedding-3-small)
   - Metric: `cosine`
   - Plan: Starter (free)
  - ⚠️ Note: Same 384 dimensions as OpenAI text-embedding-3-small, but FREE!

3. **Get API Key**: Copy from dashboard

### Step 3: Create S3 Bucket

```bash
# Create bucket for transcript storage
aws s3 mb s3://yalom-transcripts-backup

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket yalom-transcripts-backup \
  --versioning-configuration Status=Enabled
```

### Step 4: Create IAM Role for Lambda

```bash
# Create trust policy
cat > lambda-trust-policy.json << 'EOF'
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
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name YalomLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name YalomLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Step 5: Create Lambda Functions

#### A. Ingestion Lambda

**File in repo:** [aws/lambda_ingestion/handler.py](../aws/lambda_ingestion/handler.py)

✅ This handler is a **thin wrapper** that imports shared logic from `src/`.

**Important:** The handler expects `event.video_ids` (list of YouTube IDs). The default EventBridge schedule sends an empty event, so you must either:

1. **Pass video IDs manually** (for testing), or
2. **Implement a fetcher** to generate video IDs inside the handler.

**Requirements file:** [aws/lambda_ingestion/requirements.txt](../aws/lambda_ingestion/requirements.txt)

**File: `lambda_ingestion/requirements.txt`**

```txt
pinecone-client==5.0.1
openai==1.59.9
youtube-transcript-api==0.6.2
boto3==1.35.0
```

**Build package (recommended):**

```bash
cd aws
./build.sh
```

**Create Lambda function (manual fallback):**

```bash
aws lambda create-function \
  --function-name yalom-ingestion \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YalomLambdaRole \
  --handler handler.lambda_handler \
  --zip-file fileb://aws/builds/ingestion.zip \
  --timeout 900 \
  --memory-size 1024 \
  --environment Variables="{PINECONE_API_KEY=your_pinecone_key,OPENAI_API_KEY=your_openai_key,S3_BUCKET=yalom-transcripts-backup}"

# IMPORTANT: attach the shared layer to avoid oversized zip errors
# Layer file: aws/builds/yalom_layer.zip (built by ./build.sh)
```

#### B. Query Lambda (RAG)

**File in repo:** [aws/lambda_query/handler.py](../aws/lambda_query/handler.py)

✅ Thin wrapper that imports prompts and embeddings from `src/`.

**Requirements file:** [aws/lambda_query/requirements.txt](../aws/lambda_query/requirements.txt)

**File: `lambda_query/requirements.txt`**

```txt
pinecone-client==5.0.1
openai==1.59.9
groq==0.37.1
```

**Build package (recommended):**

```bash
cd aws
./build.sh
```

**Create Lambda function (manual fallback):**

```bash
aws lambda create-function \
  --function-name yalom-query \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YalomLambdaRole \
  --handler handler.lambda_handler \
  --zip-file fileb://aws/builds/query.zip \
  --timeout 30 \
  --memory-size 1024 \
  --environment Variables="{PINECONE_API_KEY=your_pinecone_key,GROQ_API_KEY=gsk_your_key,OPENAI_API_KEY=your_openai_key}"
```

### Step 6: Setup EventBridge (Cron)

```bash
# Create rule for weekly execution
aws events put-rule \
  --name yalom-weekly-ingestion \
  --schedule-expression "cron(0 10 ? * MON *)" \
  --description "Weekly Huberman Lab transcript ingestion"

# Add Lambda as target
aws events put-targets \
  --rule yalom-weekly-ingestion \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:yalom-ingestion"

# Grant permission
aws lambda add-permission \
  --function-name yalom-ingestion \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:rule/yalom-weekly-ingestion
```

### Step 7: Setup API Gateway

```bash
# Create REST API
aws apigatewayv2 create-api \
  --name yalom-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:yalom-query

# This creates HTTP API with automatic integration
# Get the API endpoint from output
```

**Or use Console:**
1. Go to API Gateway
2. Create HTTP API
3. Add integration: Lambda → `yalom-query`
4. Add route: `POST /query`
5. Deploy to stage: `prod`
6. Copy API endpoint

### Step 8: Test Deployment

```bash
# Test ingestion (manual trigger)
aws lambda invoke \
  --function-name yalom-ingestion \
  --payload '{"video_ids":["dQw4w9WgXcQ"]}' \
  response.json

cat response.json

# Test query
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is neuroplasticity?"}'
```

---

## 📈 Cost Analysis with Cold Starts

### Lambda Cold Start Impact

**First Request (Cold Start):**
- Lambda initialization: 2-3 seconds
- OpenAI embeddings call: ~0.2-0.5 seconds
- Pinecone connection: 0.5 seconds
- **Total first query**: ~4-6 seconds

**Subsequent Requests (Warm):**
- Lambda reuse: 0.1 seconds
- Query execution: 0.5 seconds
- Groq response: 1-2 seconds
- **Total warm query**: ~2 seconds

**Note:** HuggingFace embeddings add 1-2s to cold starts but eliminate $0.10/month OpenAI costs!

**Cold Start Frequency:**
- Lambda stays warm for 5-15 minutes after last invocation
- For 2 hrs/week usage (demos), likely 3-5 cold starts per week
- **User experience**: First query takes 3s, rest take 2s

### Cost with 100 Queries/Month

```
Scenario: Interview/Demo Session
- 10 sessions/month
- 10 queries per session
- First query: cold start (3s)
- Next 9 queries: warm (2s each)

Lambda Costs:
  Requests: 100 × $0.0000002 = $0.00002
  Duration: (10 × 3s) + (90 × 2s) = 210 seconds
  GB-seconds: 210s × 1.0 GB = 210 GB-s
  Cost: 210 × $0.0000166667 = $0.0035

Total Lambda: $0.0035 (well under free tier)
```

### Peak Cost Estimate (Heavy Usage)

**If you use 1,000 queries/month:**
```
Lambda:                          $0.02
API Gateway:                     $0.00 (under free tier)
S3:                              $0.01
Pinecone:                        $0.00 (100K queries free)
OpenAI Embeddings:               $0.10 (1K queries × 5K tokens)
Groq:                            $0.00 (free)
────────────────────────────────────────────
TOTAL:                           ~$0.13/month
```

Even with 10x usage, still under $1.10/month!

---

## 🚀 Optional Enhancements

### 0. Low-Cost Public UI (On/Off)

This repo includes a **static UI** hosted on S3 + CloudFront with on/off scripts.

**Deploy UI:**

```bash
make ui-deploy
```

**Turn UI ON:**

```bash
make ui-on
```

**Turn UI OFF:**

```bash
make ui-off
```

**Get UI URL:**

```bash
cd aws/terraform
terraform output -raw ui_url
```

### 1. CloudFront for Caching

Add CloudFront in front of API Gateway:
- Cache responses for common queries
- Reduce Lambda invocations
- **Cost**: $0.085 per 10K requests = $0.01/month for 100 queries
- **Benefit**: Faster responses, lower costs

### 2. DynamoDB for Query Cache

Cache frequent queries:
- Store query + answer
- Check cache before Lambda
- **Cost**: $0.00 (25 GB free storage, 25 WCU/RCU)
- **Benefit**: Instant responses for repeated queries

### 3. Lambda@Edge for Global Distribution

Deploy Lambda to CloudFront edge locations:
- Lower latency worldwide
- **Cost**: $0.60 per 1M requests (higher than regular Lambda)
- **Use case**: International demos

### 4. Provisioned Concurrency (Eliminate Cold Starts)

Keep Lambda warm 24/7:
- **Cost**: $0.015 per GB-hour × 0.512 GB × 720 hours = $5.53/month
- **Use case**: Production with strict SLA (<100ms)
- **Not recommended for your use case**

---

## 📊 Final Cost Comparison Summary

| Option | Monthly Cost | Cold Starts | Setup | Best For |
|--------|-------------|-------------|-------|----------|
| **Lambda + Pinecone** | **$0.03** | 2-4s (rare) | Easy | ✅ **Your use case** |
| Lambda + ECS Qdrant | $0.13 | 30-60s | Medium | Self-hosted data |
| ECS Always-On | $11-27 | None | Medium | 24/7 availability |
| EC2 t3.micro | $8.50 | None | Hard | Full control |

---

## ✅ Deployment Checklist

- [ ] AWS account created and CLI configured
- [ ] Pinecone account created, index set up
- [ ] S3 bucket created
- [ ] IAM role created with permissions
- [ ] Ingestion Lambda deployed and tested
- [ ] Query Lambda deployed and tested
- [ ] EventBridge cron configured
- [ ] API Gateway endpoint created
- [ ] Environment variables set (API keys)
- [ ] Test end-to-end: ingestion → query
- [ ] Document API endpoint for interviews

---

## 🎯 Recommended: Lambda + Pinecone

**Total Monthly Cost: $0.03**

**Why this wins:**
1. ✅ Nearly free ($0.03/month)
2. ✅ Zero maintenance
3. ✅ Auto-scales
4. ✅ No vector DB cold starts
5. ✅ Perfect for demos (reliable)
6. ✅ Simple architecture
7. ✅ Easy to show in interviews

**Cold start reality:**
- First query: 3 seconds (acceptable for demos)
- Subsequent: 2 seconds (excellent)
- Frequency: 3-5 times per month

This is the optimal solution for your use case! 🚀

---

## 📞 Support & References

- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Pinecone**: https://docs.pinecone.io/
- **Groq API**: https://console.groq.com/docs
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **AWS Pricing Calculator**: https://calculator.aws/

---

**Ready to deploy?** Follow the step-by-step guide above! 🎉
