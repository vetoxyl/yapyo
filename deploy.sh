#!/bin/bash

# Arbitrum Presale Bot Deployment Script for Ubuntu
# This script sets up the bot on a fresh Ubuntu server

set -e  # Exit on any error

echo "🚀 Starting Arbitrum Presale Bot Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. Use a regular user."
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
print_status "Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install git
print_status "Installing git..."
sudo apt install -y git

# Create project directory
PROJECT_DIR="$HOME/arbitrum-presale-bot"
print_status "Creating project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_status "Creating log directory..."
mkdir -p logs

# Set up environment file
if [ ! -f .env ]; then
    print_status "Creating .env file template..."
    cat > .env << 'EOF'
# Arbitrum Network
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Wallet
PRIVATE_KEY=your_private_key_here
WALLET_ADDRESS=your_wallet_address_here

# Presale
PRESALE_CONTRACT_ADDRESS=0xPresaleContractAddressHere
TOKEN_AMOUNT=0.1
MIN_LIQUIDITY=0.5

# Gas
MAX_GAS_PRICE=100000000
GAS_LIMIT=500000
PRIORITY_FEE=1000000000

# Bot
MAX_RETRIES=3
RETRY_DELAY=2
MONITOR_INTERVAL=5

# Safety
MAX_SLIPPAGE=0.05
MIN_BLOCK_CONFIRMATIONS=1

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/arbitrum_bot.log

# Telegram (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    print_warning "Please edit .env file with your configuration before running the bot"
else
    print_status ".env file already exists"
fi

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/arbitrum-presale-bot.service > /dev/null << EOF
[Unit]
Description=Arbitrum Presale Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
print_status "Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable arbitrum-presale-bot.service

# Create management scripts
print_status "Creating management scripts..."

# Start script
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF
chmod +x start_bot.sh

# Stop script
cat > stop_bot.sh << 'EOF'
#!/bin/bash
sudo systemctl stop arbitrum-presale-bot.service
echo "Bot stopped"
EOF
chmod +x stop_bot.sh

# Status script
cat > status.sh << 'EOF'
#!/bin/bash
sudo systemctl status arbitrum-presale-bot.service
EOF
chmod +x status.sh

# Logs script
cat > logs.sh << 'EOF'
#!/bin/bash
sudo journalctl -u arbitrum-presale-bot.service -f
EOF
chmod +x logs.sh

# Create README for the deployment
cat > DEPLOYMENT_README.md << 'EOF'
# Arbitrum Presale Bot - Deployment Guide

## Quick Start

1. **Configure your bot:**
   ```bash
   nano .env
   ```
   Fill in your wallet details, presale contract address, and Telegram settings.

2. **Start the bot:**
   ```bash
   ./start_bot.sh
   ```

3. **Check status:**
   ```bash
   ./status.sh
   ```

4. **View logs:**
   ```bash
   ./logs.sh
   ```

5. **Stop the bot:**
   ```bash
   ./stop_bot.sh
   ```

## Systemd Service

The bot is installed as a systemd service that will:
- Start automatically on boot
- Restart automatically if it crashes
- Log to system journal

### Service Commands:
```bash
# Start the service
sudo systemctl start arbitrum-presale-bot.service

# Stop the service
sudo systemctl stop arbitrum-presale-bot.service

# Restart the service
sudo systemctl restart arbitrum-presale-bot.service

# Check status
sudo systemctl status arbitrum-presale-bot.service

# View logs
sudo journalctl -u arbitrum-presale-bot.service -f

# Disable auto-start
sudo systemctl disable arbitrum-presale-bot.service
```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Regularly update your system and Python packages
- Monitor the bot logs for any issues
- Consider using a dedicated user account for the bot

## Troubleshooting

### Bot won't start:
1. Check the logs: `./logs.sh`
2. Verify your `.env` configuration
3. Check network connectivity
4. Ensure you have sufficient ETH balance

### Service issues:
1. Check service status: `sudo systemctl status arbitrum-presale-bot.service`
2. Restart the service: `sudo systemctl restart arbitrum-presale-bot.service`
3. Check system logs: `sudo journalctl -u arbitrum-presale-bot.service`

### Telegram notifications not working:
1. Follow the setup guide in `telegram_setup.md`
2. Verify your bot token and chat ID
3. Make sure you've started a conversation with your bot
EOF

print_status "Deployment completed successfully!"
echo ""
print_status "Next steps:"
echo "1. Edit .env file with your configuration: nano .env"
echo "2. Start the bot: ./start_bot.sh"
echo "3. Check status: ./status.sh"
echo "4. View logs: ./logs.sh"
echo ""
print_status "For Telegram setup, see: telegram_setup.md"
print_status "For deployment details, see: DEPLOYMENT_README.md"
echo ""
print_warning "IMPORTANT: Configure your .env file before starting the bot!" 