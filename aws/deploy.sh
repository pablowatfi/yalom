#!/bin/bash
set -e

echo "🚀 Yalom AWS Deployment Script"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Install with: brew install awscli${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Install with: brew install terraform${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Build Lambda packages (includes src/ code)
echo -e "\n${YELLOW}📦 Building Lambda packages...${NC}"
./build.sh
echo -e "${GREEN}✅ Lambda packages built${NC}"

# Check Terraform variables
echo -e "\n${YELLOW}Checking Terraform configuration...${NC}"
if [ ! -f terraform/terraform.tfvars ]; then
    echo -e "${RED}❌ terraform.tfvars not found${NC}"
    echo "Create it from terraform.tfvars.example and fill in your API keys"
    exit 1
fi

# Deploy with Terraform
echo -e "\n${YELLOW}🏗️  Deploying infrastructure with Terraform...${NC}"
cd terraform

terraform init
terraform plan
echo -e "\n${YELLOW}Review the plan above. Continue? (yes/no)${NC}"
read -r REPLY
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

terraform apply -auto-approve

# Get outputs
API_ENDPOINT=$(terraform output -raw api_endpoint)

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo -e "\n${GREEN}API Endpoint:${NC} ${API_ENDPOINT}/query"
echo -e "\n${YELLOW}Test with:${NC}"
echo "curl -X POST ${API_ENDPOINT}/query \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\":\"What is neuroplasticity?\"}'"

cd ..
