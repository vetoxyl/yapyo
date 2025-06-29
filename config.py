import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Network Configuration
    ARBITRUM_RPC_URL = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    ARBITRUM_CHAIN_ID = 42161
    
    # Wallet Configuration
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
    
    # Gas Configuration
    MAX_GAS_PRICE = int(os.getenv('MAX_GAS_PRICE', '100000000'))  # 0.1 gwei
    GAS_LIMIT = int(os.getenv('GAS_LIMIT', '500000'))
    PRIORITY_FEE = int(os.getenv('PRIORITY_FEE', '1000000000'))  # 1 gwei
    
    # Presale Configuration
    PRESALE_CONTRACT_ADDRESS = os.getenv('PRESALE_CONTRACT_ADDRESS')
    TOKEN_AMOUNT = float(os.getenv('TOKEN_AMOUNT', '0.1'))  # ETH amount to invest
    MIN_LIQUIDITY = float(os.getenv('MIN_LIQUIDITY', '0.5'))  # Minimum liquidity ratio
    
    # Bot Configuration
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))  # seconds
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '5'))  # seconds
    
    # Safety Configuration
    MAX_SLIPPAGE = float(os.getenv('MAX_SLIPPAGE', '0.05'))  # 5%
    MIN_BLOCK_CONFIRMATIONS = int(os.getenv('MIN_BLOCK_CONFIRMATIONS', '1'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'arbitrum_bot.log')
    
    # Telegram Notifications (Optional)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_fields = ['PRIVATE_KEY', 'WALLET_ADDRESS', 'PRESALE_CONTRACT_ADDRESS']
        missing_fields = [field for field in required_fields if not getattr(cls, field)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True 