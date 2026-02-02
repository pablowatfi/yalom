#!/bin/bash
set -e

echo "🚀 Oracle Cloud Deployment Setup Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Ubuntu
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release; then
    echo -e "${RED}❌ This script is designed for Ubuntu. Please adjust for your OS.${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Step 1: Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${BLUE}🐳 Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

echo -e "${BLUE}🔧 Step 3: Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

echo -e "${BLUE}📝 Step 4: Installing Git...${NC}"
if ! command -v git &> /dev/null; then
    sudo apt install -y git
    echo -e "${GREEN}✅ Git installed${NC}"
else
    echo -e "${GREEN}✅ Git already installed${NC}"
fi

echo -e "${BLUE}🔥 Step 5: Configuring firewall...${NC}"
# Open Streamlit port
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8501 -j ACCEPT

# Install persistence tool if not present
if ! command -v netfilter-persistent &> /dev/null; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
fi

sudo netfilter-persistent save
echo -e "${GREEN}✅ Firewall configured (port 8501 open)${NC}"

echo -e "${BLUE}💾 Step 6: Setting up swap (optional but recommended)...${NC}"
if [ ! -f /swapfile ]; then
    sudo fallocate -l 8G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo -e "${GREEN}✅ 8GB swap created${NC}"
else
    echo -e "${GREEN}✅ Swap already exists${NC}"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Clone your repository:"
echo "   ${BLUE}git clone https://github.com/YOUR_USERNAME/yalom.git${NC}"
echo ""
echo "2. Deploy the application:"
echo "   ${BLUE}cd yalom${NC}"
echo "   ${BLUE}docker-compose -f docker-compose.oracle.yml up -d${NC}"
echo ""
echo "3. Download Ollama model:"
echo "   ${BLUE}docker exec yalom-ollama ollama pull llama3.2${NC}"
echo ""
echo "4. Access your app at:"
echo "   ${BLUE}http://$(curl -s ifconfig.me):8501${NC}"
echo ""
echo -e "${RED}⚠️  Note: You may need to log out and back in for Docker group changes to take effect.${NC}"
