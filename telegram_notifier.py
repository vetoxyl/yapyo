import asyncio
import aiohttp
import logging
from datetime import datetime
from config import Config

class TelegramNotifier:
    """Telegram notification system for the presale bot"""
    
    def __init__(self, config: Config):
        self.config = config
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.logger = logging.getLogger(__name__)
        
        # Check if Telegram is configured
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            self.logger.info("Telegram notifications enabled")
        else:
            self.logger.warning("Telegram notifications disabled - missing bot token or chat ID")
    
    async def send_message(self, message: str, parse_mode: str = "HTML"):
        """Send a message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': parse_mode
                }
                
                async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_presale_start_notification(self, presale_info: dict):
        """Send notification when presale starts"""
        message = f"""
🚀 <b>Presale Started!</b>

📋 <b>Presale Details:</b>
• Token: <code>{presale_info['token_address']}</code>
• Start: {datetime.fromtimestamp(presale_info['presale_start'])}
• End: {datetime.fromtimestamp(presale_info['presale_end'])}
• Soft Cap: {presale_info['soft_cap']} ETH
• Hard Cap: {presale_info['hard_cap']} ETH

💰 <b>Bot Status:</b>
• Wallet: <code>{self.config.WALLET_ADDRESS[:10]}...</code>
• Investment: {self.config.TOKEN_AMOUNT} ETH
• Monitoring: ✅ Active
        """
        await self.send_message(message)
    
    async def send_buy_attempt_notification(self, eth_amount: float, gas_price: int):
        """Send notification when attempting to buy"""
        gas_price_gwei = gas_price / 1e9
        message = f"""
🔄 <b>Buy Attempt</b>

💰 <b>Transaction Details:</b>
• Amount: {eth_amount} ETH
• Gas Price: {gas_price_gwei:.2f} gwei
• Contract: <code>{self.config.PRESALE_CONTRACT_ADDRESS[:10]}...</code>

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(message)
    
    async def send_buy_success_notification(self, tx_hash: str, eth_amount: float, tokens_received: int, gas_used: int):
        """Send notification when buy is successful"""
        message = f"""
✅ <b>Buy Success!</b>

💰 <b>Transaction Details:</b>
• TX Hash: <code>{tx_hash}</code>
• ETH Spent: {eth_amount} ETH
• Tokens Received: {tokens_received:,}
• Gas Used: {gas_used:,}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎉 <b>Presale participation successful!</b>
        """
        await self.send_message(message)
    
    async def send_buy_failure_notification(self, error: str):
        """Send notification when buy fails"""
        message = f"""
❌ <b>Buy Failed</b>

🔍 <b>Error Details:</b>
• Error: {error}
• Contract: <code>{self.config.PRESALE_CONTRACT_ADDRESS[:10]}...</code>

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Bot will retry automatically
        """
        await self.send_message(message)
    
    async def send_gas_warning_notification(self, current_gas: int, max_gas: int):
        """Send notification when gas is too high"""
        current_gwei = current_gas / 1e9
        max_gwei = max_gas / 1e9
        message = f"""
⛽ <b>Gas Price Warning</b>

💰 <b>Gas Details:</b>
• Current: {current_gwei:.2f} gwei
• Max Allowed: {max_gwei:.2f} gwei
• Status: ⏳ Waiting for better conditions

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(message)
    
    async def send_presale_ended_notification(self, total_raised: int, hard_cap: int):
        """Send notification when presale ends"""
        message = f"""
🏁 <b>Presale Ended</b>

📊 <b>Final Stats:</b>
• Total Raised: {total_raised} ETH
• Hard Cap: {hard_cap} ETH
• Success: {'✅' if total_raised >= hard_cap else '❌'}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(message)
    
    async def send_balance_warning_notification(self, current_balance: float, required_amount: float):
        """Send notification when balance is low"""
        message = f"""
⚠️ <b>Low Balance Warning</b>

💰 <b>Balance Details:</b>
• Current: {current_balance:.4f} ETH
• Required: {required_amount:.4f} ETH
• Shortage: {required_amount - current_balance:.4f} ETH

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 Please add more ETH to your wallet
        """
        await self.send_message(message)
    
    async def send_bot_status_notification(self, status: dict):
        """Send bot status update"""
        message = f"""
🤖 <b>Bot Status Update</b>

📊 <b>Current Status:</b>
• Running: {'✅' if status['is_running'] else '❌'}
• Wallet: <code>{status['wallet_address'][:10]}...</code>
• Presale: <code>{status['presale_address'][:10]}...</code>
• Transactions: {status['transaction_count']}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(message)
    
    async def send_error_notification(self, error: str, context: str = ""):
        """Send error notification"""
        message = f"""
🚨 <b>Bot Error</b>

❌ <b>Error:</b> {error}
📝 <b>Context:</b> {context if context else "No additional context"}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔧 Bot will attempt to recover automatically
        """
        await self.send_message(message)
    
    async def send_startup_notification(self):
        """Send notification when bot starts"""
        message = f"""
🚀 <b>Arbitrum Presale Bot Started</b>

📋 <b>Configuration:</b>
• Network: Arbitrum
• Wallet: <code>{self.config.WALLET_ADDRESS[:10]}...</code>
• Investment: {self.config.TOKEN_AMOUNT} ETH
• Max Gas: {self.config.MAX_GAS_PRICE / 1e9:.2f} gwei

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Bot is now monitoring presale conditions
        """
        await self.send_message(message)
    
    async def send_shutdown_notification(self):
        """Send notification when bot stops"""
        message = f"""
🛑 <b>Arbitrum Presale Bot Stopped</b>

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

👋 Bot monitoring has been stopped
        """
        await self.send_message(message) 