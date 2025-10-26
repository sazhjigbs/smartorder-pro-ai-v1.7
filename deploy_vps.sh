#!/bin/bash
# SmartOrder PRO - VPS Deployment Script
# by MAIGA ABOUBACAR
#
# Usage: ./deploy_vps.sh

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "========================================"
echo "  🚀 SmartOrder PRO Deployment"
echo "  by MAIGA ABOUBACAR"
echo "  v2.0 Ultra-Pro"
echo "========================================"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Not recommended to run as root!${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Check prerequisites
echo -e "${CYAN}📋 Step 1/7: Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found!${NC}"
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker found${NC}"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found!${NC}"
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose found${NC}"
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git not found, installing...${NC}"
    sudo apt-get update && sudo apt-get install -y git
fi

# Step 2: Clone/Update repository
echo -e "${CYAN}📦 Step 2/7: Getting latest code...${NC}"

if [ -d ".git" ]; then
    echo "Updating existing repository..."
    git pull origin main
else
    echo "Repository already present"
fi

# Step 3: Configure environment
echo -e "${CYAN}⚙️  Step 3/7: Configuring environment...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo "Creating .env from template..."
    
    cat > .env << 'EOF'
# SmartOrder PRO - Environment Configuration
# by MAIGA ABOUBACAR

# Bybit
BYBIT_ENABLED=true
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=false

# Binance
BINANCE_ENABLED=false
BINANCE_API_KEY=
BINANCE_API_SECRET=

# OKX
OKX_ENABLED=false
OKX_API_KEY=
OKX_API_SECRET=

# KuCoin
KUCOIN_ENABLED=false
KUCOIN_API_KEY=
KUCOIN_API_SECRET=

# Telegram
TG_TOKEN=your_telegram_token
TG_CHAT_ID=your_chat_id

# Security
MASTER_PASSWORD=ChangeThisPassword123!
ADMIN_PASSWORD=admin123
FLASK_SECRET_KEY=change_this_secret_key

# Trading
MODE=live
REAL_MODE=True
EOF

    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your API keys!${NC}"
    read -p "Press enter to continue after editing .env..."
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Step 4: Create necessary directories
echo -e "${CYAN}📁 Step 4/7: Creating directories...${NC}"

mkdir -p logs
mkdir -p security
mkdir -p data
mkdir -p monitoring

echo -e "${GREEN}✅ Directories created${NC}"

# Step 5: Build Docker images
echo -e "${CYAN}🐳 Step 5/7: Building Docker images...${NC}"

docker-compose build --no-cache

echo -e "${GREEN}✅ Docker images built${NC}"

# Step 6: Start services
echo -e "${CYAN}🚀 Step 6/7: Starting services...${NC}"

docker-compose down
docker-compose up -d

echo -e "${GREEN}✅ Services started${NC}"

# Step 7: Verify deployment
echo -e "${CYAN}✅ Step 7/7: Verifying deployment...${NC}"

sleep 10

if docker ps | grep -q "smartorder-pro"; then
    echo -e "${GREEN}✅ SmartOrder PRO is running!${NC}"
    
    # Show logs
    echo -e "\n${CYAN}📋 Container logs:${NC}"
    docker-compose logs --tail=20
    
    # Show status
    echo -e "\n${CYAN}📊 Container status:${NC}"
    docker-compose ps
    
    # Get IP
    SERVER_IP=$(curl -s ifconfig.me)
    
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\n${CYAN}🌐 Access URLs:${NC}"
    echo -e "   Dashboard: ${GREEN}http://${SERVER_IP}:5000${NC}"
    echo -e "   Portal:    ${GREEN}http://${SERVER_IP}:8555${NC}"
    echo -e "\n${CYAN}📱 Useful commands:${NC}"
    echo -e "   View logs:    ${YELLOW}docker-compose logs -f${NC}"
    echo -e "   Stop:         ${YELLOW}docker-compose stop${NC}"
    echo -e "   Restart:      ${YELLOW}docker-compose restart${NC}"
    echo -e "   Status:       ${YELLOW}docker-compose ps${NC}"
    echo -e "\n${CYAN}💎 Developed by MAIGA ABOUBACAR${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo -e "Check logs with: docker-compose logs"
    exit 1
fi
