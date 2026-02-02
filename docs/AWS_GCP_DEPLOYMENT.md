# AWS vs GCP vs Oracle Cloud Deployment Guide

Comparison and setup for deploying Yalom on AWS and GCP with minimal cost (30-40 calls/day, on-demand).

## Cost Comparison Table (Monthly)

| Platform | Service | Monthly Cost | Cold Starts | Setup | Ollama Support | Best For |
|----------|---------|-------------|-------------|-------|----------------|----------|
| **Oracle** | A1 (ARM) | **$0** 🎉 | None | Hard | ✅ Yes (12GB) | Truly free, max performance |
| **AWS** | Lambda + Supabase | **$2-5** | 2-5s | Medium | ❌ No (15min timeout) | Cheapest with database |
| **AWS** | App Runner + RDS | **$10-20** | 2s | Easy | ✅ Yes (1GB available) | Easy deployment, local LLM |
| **AWS** | Lightsail | **$3.50** | None | Easy | ✅ Yes (512MB available) | Fixed cost, light load |
| **GCP** | Cloud Run + Firestore | **$0-5** 🔥 | 1-2s | Medium | ❌ No (4GB timeout limit) | **Cheapest with database** |
| **GCP** | Cloud Run + Cloud SQL | **$10-15** | 1-2s | Medium | ❌ No (4GB timeout limit) | More traditional database |
| **GCP** | Compute Engine (e2-micro) | **$3.50** | None | Medium | ✅ Yes (512MB available) | Fixed cost, local LLM |

---

## Detailed Cost Breakdown

### AWS Lambda + Supabase
```
Lambda:        $0.20 per 1M requests → 1,200 calls = $0.00024
API Gateway:   $3.50 per 1M requests → 1,200 calls = $0.0042
Supabase DB:   FREE tier (5 GB, hosted PostgreSQL)
OpenAI API:    ~$2-5/month (depends on model)
────────────────────────────────────────────────
TOTAL:         ~$2-5/month
```

### AWS App Runner + RDS
```
App Runner:    $0.064/vCPU-hour + $0.016/GB-hour
               0.5 vCPU + 1 GB = $46/month (always billed even if idle)
RDS t3.micro:  $0.017/hour = ~$12/month
               + $0.23/GB storage = ~$5/month (20GB)
────────────────────────────────────────────────
TOTAL:         ~$60/month (ouch! because it's always billed)
```

### AWS Lightsail
```
Fixed cost:    $3.50/month for 512MB RAM, 1 vCPU, 20GB SSD
OpenAI API:    ~$2-5/month (optional, if using external LLM)
────────────────────────────────────────────────
TOTAL:         ~$3.50-8.50/month
```

### **GCP Cloud Run + Firestore** ✅ CHEAPEST WITH DATABASE
```
Cloud Run:     $0.40 per 1M requests → 1,200 calls = FREE (generous free tier)
               Free tier: 2M requests/month
Firestore:     $0.06 per 100K reads → 1,200 reads = FREE (50K free/day)
               Free tier: 50K reads + 20K writes/day
OpenAI API:    ~$2-5/month
────────────────────────────────────────────────
TOTAL:         ~$2-5/month 🔥 (database included!)
```

### GCP Cloud Run + Cloud SQL
```
Cloud Run:     FREE (within free tier)
Cloud SQL:     $6.50/month (db.f1-micro shared)
               + $0.17/GB storage = ~$3 (20GB)
OpenAI API:    ~$2-5/month
────────────────────────────────────────────────
TOTAL:         ~$11-14/month
```

### GCP Compute Engine (e2-micro)
```
e2-micro:      $3.50/month (always on, but very cheap)
               0.25-2 vCPU, 1 GB RAM (burstable)
Persistent disk: $0.10/GB/month = $2/month (20GB)
OpenAI API:    ~$2-5/month (optional)
────────────────────────────────────────────────
TOTAL:         ~$5.50/month
```

---

## 🔥 RECOMMENDATION: GCP Cloud Run + Firestore

**Why?**
- ✅ **Cheapest with database included** ($2-5/month)
- ✅ **Generous free tier** covers your use case
- ✅ Fast cold starts (1-2 seconds)
- ✅ Auto-scales from 0 to infinity
- ✅ Google's infrastructure (very reliable)
- ✅ No credit card needed (free tier actually free)

---

## AWS Lambda Setup

### Prerequisites
```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)
```

### Option 1: Deploy as Lambda Function

1. **Create Lambda Function**
   - Go to AWS Lambda console
   - Click "Create function"
   - Name: `yalom-api`
   - Runtime: `Python 3.11`
   - Click "Create function"

2. **Package Your Code**
   ```bash
   # Create handler function
   cat > lambda_handler.py << 'EOF'
   import json
   import os
   from src.rag.pipeline import RAGPipeline

   pipeline = RAGPipeline()

   def lambda_handler(event, context):
       try:
           body = json.loads(event.get('body', '{}'))
           query = body.get('query')

           result = pipeline.query(query)

           return {
               'statusCode': 200,
               'body': json.dumps({'response': result})
           }
       except Exception as e:
           return {
               'statusCode': 500,
               'body': json.dumps({'error': str(e)})
           }
   EOF
   ```

3. **Create Deployment Package**
   ```bash
   # Create deployment directory
   mkdir lambda_package
   cd lambda_package

   # Install dependencies
   pip install -r ../requirements.txt -t .

   # Copy source code
   cp -r ../src .
   cp ../lambda_handler.py .

   # Create ZIP
   zip -r lambda_function.zip .
   ```

4. **Upload to Lambda**
   - In Lambda console, click "Upload from" → ".zip file"
   - Select `lambda_function.zip`
   - Click "Deploy"

5. **Create API Gateway**
   - Go to API Gateway console
   - Click "Create API"
   - Name: `yalom-api`
   - Select "REST API"
   - Click "Create"
   - Create resource `/query`
   - Create POST method
   - Integration type: Lambda Function
   - Select your `yalom-api` function
   - Deploy

6. **Set Environment Variables**
   ```bash
   # In Lambda console, Configuration tab
   # Environment variables:
   OPENAI_API_KEY=sk-your-key
   DATABASE_URL=postgresql://...
   ```

### Option 2: Deploy with SAM (Simpler)

```bash
# Install AWS SAM CLI
brew install aws-sam-cli

# Create template.yaml
cat > template.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 900
    Runtime: python3.11
    Environment:
      Variables:
        OPENAI_API_KEY: !Ref OpenAIKey

Parameters:
  OpenAIKey:
    Type: String
    NoEcho: true

Resources:
  YalomFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_handler.lambda_handler
      CodeUri: .
      Events:
        QueryAPI:
          Type: Api
          Properties:
            Path: /query
            Method: post
            RestApiId: !Ref YalomAPI

  YalomAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod

Outputs:
  APIEndpoint:
    Value: !Sub 'https://${YalomAPI}.execute-api.${AWS::Region}.amazonaws.com/prod/query'
EOF

# Deploy
sam deploy --guided
```

---

## GCP Cloud Run Setup

### Prerequisites
```bash
# Install Google Cloud SDK
brew install --cask google-cloud-sdk

# Initialize
gcloud init

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required services
gcloud services enable run.googleapis.com firestore.googleapis.com containerregistry.googleapis.com
```

### Option 1: Deploy with Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY pyproject.toml poetry.lock ./
   COPY src/ ./src/
   COPY app/ ./app/

   RUN pip install poetry && \
       poetry config virtualenvs.create false && \
       poetry install --no-interaction --no-ansi --no-root --only main

   ENV PORT=8080
   EXPOSE 8080

   # API mode: minimal Flask/FastAPI wrapper
   COPY main.py .
   CMD ["python", "main.py"]
   ```

2. **Create API Wrapper** (`main.py`)
   ```python
   from flask import Flask, request, jsonify
   from src.rag.pipeline import RAGPipeline
   import os

   app = Flask(__name__)
   pipeline = RAGPipeline()

   @app.route('/query', methods=['POST'])
   def query():
       try:
           data = request.get_json()
           query_text = data.get('query')

           result = pipeline.query(query_text)

           return jsonify({'response': result})
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   @app.route('/health', methods=['GET'])
   def health():
       return jsonify({'status': 'ok'})

   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 8080))
       app.run(host='0.0.0.0', port=port)
   ```

3. **Deploy to Cloud Run**
   ```bash
   # Build and push to Container Registry
   gcloud run deploy yalom-api \
     --source . \
     --platform managed \
     --region us-central1 \
     --memory 512Mi \
     --cpu 1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=sk-your-key

   # Output will show your API URL
   # https://yalom-api-XXXXX.run.app/query
   ```

⚠️ **Ollama NOT Supported on Cloud Run:**
- Cloud Run has 4GB memory limit (max)
- Ollama models typically need 2-7GB
- Cloud Run has 15-minute request timeout
- Ollama inference takes longer than 15 minutes for large models
- **Solution**: Use OpenAI/Claude API instead, or switch to Compute Engine

### Option 2: Deploy with Firestore (Recommended)

1. **Enable Firestore**
   ```bash
   gcloud firestore databases create --location us-central1
   ```

2. **Update Code to Use Firestore**
   ```python
   from google.cloud import firestore

   db = firestore.Client()

   def store_transcript(episode_id, content):
       db.collection('transcripts').document(episode_id).set({
           'content': content,
           'timestamp': firestore.SERVER_TIMESTAMP
       })

   def query_transcripts(query_text):
       docs = db.collection('transcripts').stream()
       results = [doc.to_dict() for doc in docs]
       return results
   ```

3. **Deploy Same Way**
   ```bash
   gcloud run deploy yalom-api --source .
   ```

⚠️ **About Ollama and Cloud Run + Cloud SQL:**
- Same Cloud Run limitations apply (4GB memory, 15min timeout)
- Cannot run Ollama locally
- Must use OpenAI, Claude, or other external LLM APIs
- Cloud SQL adds cost ($6.50+/month) for traditional SQL database

### Cost Optimization Tips

**GCP Cloud Run Auto-scaling:**
```bash
gcloud run deploy yalom-api \
  --source . \
  --min-instances 0 \      # Scale to 0 when not in use
  --max-instances 10 \     # Max 10 concurrent
  --memory 512Mi \
  --cpu 1
```

**GCP Firestore Cost Control:**
```python
# Batch writes to reduce write costs
batch = db.batch()
for transcript in transcripts:
    batch.set(
        db.collection('transcripts').document(transcript['id']),
        transcript
    )
batch.commit()  # One write operation instead of N
```

---

## GCP Compute Engine Setup (With Ollama Support)

**✅ Only GCP Option for Running Ollama Locally**

### Create Compute Engine Instance

```bash
# Create instance with gcloud CLI
gcloud compute instances create yalom-app \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --scopes=default,cloud-platform
```

Or via Google Cloud Console:
1. Go to **Compute Engine** → **VM Instances**
2. Click **Create Instance**
3. Name: `yalom-app`
4. Machine type: **e2-micro** (0.25-2 vCPUs, 1GB RAM) - $3.50/month
5. Boot disk: **Ubuntu 22.04 LTS**, 50GB
6. Allow HTTP and HTTPS traffic
7. Click **Create**

### Install Dependencies

```bash
# SSH into instance
gcloud compute ssh yalom-app --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install -y docker-compose

# Clone repository
git clone https://github.com/YOUR_USERNAME/yalom.git
cd yalom
```

### Deploy with Docker Compose

```bash
# Use the same docker-compose setup from your local development
docker-compose up -d

# Download Ollama model
docker exec yalom-ollama ollama pull llama3.2

# Check status
docker ps
```

### Access Application

Get your instance's external IP:
```bash
gcloud compute instances describe yalom-app --zone=us-central1-a | grep natIP
```

Then access at: `http://EXTERNAL_IP:8501`

### ✅ Ollama Support on Compute Engine
- **Memory**: 1GB RAM (e2-micro) - limited but works
- **Models**: Use smaller models like `phi3:mini` (2.3GB)
- **Cost**: Fixed $3.50/month regardless of usage
- **Always-on**: Yes (you're paying even when idle)
- **Performance**: Good for 30-40 calls/day

---

## Calling Your API

### AWS Lambda
```bash
curl -X POST https://YOUR_API_GATEWAY_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is neuroplasticity?"}'
```

### GCP Cloud Run
```bash
curl -X POST https://yalom-api-XXXXX.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is neuroplasticity?"}'
```

---

## Monitoring & Logs

### AWS Lambda
```bash
# View logs
aws logs tail /aws/lambda/yalom-api --follow

# Check invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 86400 \
  --statistics Sum
```

### GCP Cloud Run
```bash
# View logs
gcloud run logs read yalom-api --follow

# Check metrics
gcloud run metrics RESOURCE_NAME
```

---

## Database Options Comparison

| Database | GCP Cost | AWS Cost | Setup | Notes |
|----------|----------|----------|-------|-------|
| **Firestore** | FREE tier (50K reads/day) | N/A | Simple (NoSQL) | Best for serverless |
| **Cloud SQL** | $6.50-15/month | N/A | Medium (SQL) | Traditional database |
| **Supabase** | N/A | FREE tier (5GB) | Very easy | Best for Lambda |
| **RDS** | N/A | $12+/month | Medium | Traditional database |

---

## Final Recommendation

**For your use case (30-40 calls/day, on-demand):**

### 🥇 Best Overall: **Oracle Cloud A1** ($0/month)
- Truly free forever
- Can run Ollama locally
- Hardest to set up (capacity issues)

### 🥈 Best Serverless: **GCP Cloud Run + Firestore** ($2-5/month)
- Cheapest with database
- Auto-scales
- Cold starts OK
- Google's free tier is generous

### 🥉 Best Traditional: **AWS Lightsail** ($3.50/month)
- Fixed, predictable cost
- Can run Ollama
- Simpler than Lambda
- Always on (slight waste)

---

## Support & References

- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **AWS API Gateway**: https://docs.aws.amazon.com/apigateway/
- **GCP Cloud Run**: https://cloud.google.com/run/docs
- **GCP Firestore**: https://cloud.google.com/firestore/docs
- **Pricing Calculator**: https://calculator.aws/ or https://cloud.google.com/products/calculator

---

**Ready to deploy?** Choose your platform and follow the detailed setup instructions above!
