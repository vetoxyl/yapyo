import asyncio
import time
import logging
from datetime import datetime
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
import json

from config import Config
from contracts import PresaleContracts
from gas_optimizer import ArbitrumGasOptimizer
from telegram_notifier import TelegramNotifier

class ArbitrumPresaleBot:
    """Main presale bot for Arbitrum network"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Setup Web3
        self.web3 = Web3(Web3.HTTPProvider(self.config.ARBITRUM_RPC_URL))
        self.web3.eth.default_account = self.config.WALLET_ADDRESS
        
        # Setup account
        self.account: LocalAccount = Account.from_key(self.config.PRIVATE_KEY)
        
        # Setup gas optimizer
        self.gas_optimizer = ArbitrumGasOptimizer(self.web3, self.config)
        
        # Setup Telegram notifier
        self.telegram = TelegramNotifier(self.config)
        
        # Setup logging
        self.setup_logging()
        
        # Bot state
        self.is_running = False
        self.last_transaction = None
        self.transaction_history = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_network_connection(self):
        """Check if connected to Arbitrum network"""
        try:
            if not self.web3.is_connected():
                raise Exception("Not connected to Arbitrum network")
            
            chain_id = self.web3.eth.chain_id
            if chain_id != self.config.ARBITRUM_CHAIN_ID:
                raise Exception(f"Wrong network. Expected Arbitrum (42161), got {chain_id}")
            
            self.logger.info("Successfully connected to Arbitrum network")
            return True
            
        except Exception as e:
            self.logger.error(f"Network connection error: {e}")
            asyncio.create_task(self.telegram.send_error_notification(str(e), "Network connection check"))
            return False
    
    def check_wallet_balance(self):
        """Check wallet ETH balance"""
        try:
            balance = self.web3.eth.get_balance(self.config.WALLET_ADDRESS)
            balance_eth = self.web3.from_wei(balance, 'ether')
            
            self.logger.info(f"Wallet balance: {balance_eth:.4f} ETH")
            
            # Check if we have enough for the transaction
            required_amount = self.config.TOKEN_AMOUNT + 0.01  # Add buffer for gas
            if balance_eth < required_amount:
                self.logger.error(f"Insufficient balance. Need {required_amount} ETH, have {balance_eth} ETH")
                asyncio.create_task(self.telegram.send_balance_warning_notification(balance_eth, required_amount))
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking balance: {e}")
            asyncio.create_task(self.telegram.send_error_notification(str(e), "Balance check"))
            return False
    
    def validate_presale_contract(self):
        """Validate presale contract and get information"""
        try:
            presale_info = PresaleContracts.get_presale_info(
                self.web3, 
                self.config.PRESALE_CONTRACT_ADDRESS
            )
            
            self.logger.info("Presale Contract Information:")
            self.logger.info(f"Token Address: {presale_info['token_address']}")
            self.logger.info(f"Start Time: {datetime.fromtimestamp(presale_info['presale_start'])}")
            self.logger.info(f"End Time: {datetime.fromtimestamp(presale_info['presale_end'])}")
            self.logger.info(f"Soft Cap: {self.web3.from_wei(presale_info['soft_cap'], 'ether')} ETH")
            self.logger.info(f"Hard Cap: {self.web3.from_wei(presale_info['hard_cap'], 'ether')} ETH")
            self.logger.info(f"Total Raised: {self.web3.from_wei(presale_info['total_raised'], 'ether')} ETH")
            self.logger.info(f"Is Active: {presale_info['is_active']}")
            
            # Check if presale is active
            if not presale_info['is_active']:
                self.logger.error("Presale is not active")
                asyncio.create_task(self.telegram.send_error_notification("Presale is not active", "Contract validation"))
                return False
            
            # Check if presale hasn't ended
            current_time = int(time.time())
            if current_time > presale_info['presale_end']:
                self.logger.error("Presale has ended")
                asyncio.create_task(self.telegram.send_presale_ended_notification(
                    self.web3.from_wei(presale_info['total_raised'], 'ether'),
                    self.web3.from_wei(presale_info['hard_cap'], 'ether')
                ))
                return False
            
            # Check if hard cap reached
            if presale_info['total_raised'] >= presale_info['hard_cap']:
                self.logger.error("Hard cap reached")
                asyncio.create_task(self.telegram.send_error_notification("Hard cap reached", "Contract validation"))
                return False
            
            return presale_info
            
        except Exception as e:
            self.logger.error(f"Error validating presale contract: {e}")
            asyncio.create_task(self.telegram.send_error_notification(str(e), "Contract validation"))
            return False
    
    def calculate_optimal_buy_amount(self, presale_info):
        """Calculate optimal buy amount based on presale conditions"""
        try:
            hard_cap = presale_info['hard_cap']
            total_raised = presale_info['total_raised']
            remaining = hard_cap - total_raised
            
            # Calculate what we can buy
            max_buy = min(self.config.TOKEN_AMOUNT, self.web3.to_wei(remaining, 'ether'))
            
            if max_buy <= 0:
                self.logger.error("No remaining allocation in presale")
                return 0
            
            return self.web3.from_wei(max_buy, 'ether')
            
        except Exception as e:
            self.logger.error(f"Error calculating buy amount: {e}")
            return 0
    
    async def execute_buy_transaction(self, buy_amount):
        """Execute the buy transaction"""
        try:
            self.logger.info(f"Executing buy transaction for {buy_amount} ETH")
            
            # Get current gas price for notification
            current_gas = self.gas_optimizer.get_current_gas_price()
            await self.telegram.send_buy_attempt_notification(buy_amount, current_gas)
            
            # Build transaction
            transaction = PresaleContracts.build_buy_transaction(
                self.web3,
                self.config.PRESALE_CONTRACT_ADDRESS,
                buy_amount,
                self.config.MAX_GAS_PRICE,
                self.config.GAS_LIMIT
            )
            
            # Optimize gas parameters
            gas_params = self.gas_optimizer.optimize_gas_for_transaction(transaction)
            transaction.update(gas_params)
            
            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.config.PRIVATE_KEY)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=300,
                poll_latency=2
            )
            
            if receipt.status == 1:
                self.logger.info(f"Transaction successful! Block: {receipt.blockNumber}")
                
                # Calculate tokens received
                tokens_received = PresaleContracts.calculate_tokens_for_eth(
                    self.web3,
                    self.config.PRESALE_CONTRACT_ADDRESS,
                    buy_amount
                )
                
                self.logger.info(f"Tokens received: {tokens_received}")
                
                # Send success notification
                await self.telegram.send_buy_success_notification(
                    tx_hash.hex(),
                    buy_amount,
                    tokens_received,
                    receipt.gasUsed
                )
                
                # Store transaction info
                self.last_transaction = {
                    'tx_hash': tx_hash.hex(),
                    'block_number': receipt.blockNumber,
                    'gas_used': receipt.gasUsed,
                    'eth_amount': buy_amount,
                    'tokens_received': tokens_received,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.transaction_history.append(self.last_transaction)
                
                return True
            else:
                self.logger.error("Transaction failed")
                await self.telegram.send_buy_failure_notification("Transaction reverted")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing buy transaction: {e}")
            await self.telegram.send_buy_failure_notification(str(e))
            return False
    
    async def monitor_presale_conditions(self):
        """Monitor presale conditions and execute when optimal"""
        while self.is_running:
            try:
                # Check presale status
                presale_info = self.validate_presale_contract()
                if not presale_info:
                    self.logger.warning("Presale validation failed, retrying...")
                    await asyncio.sleep(self.config.MONITOR_INTERVAL)
                    continue
                
                # Check if presale is about to start
                current_time = int(time.time())
                time_until_start = presale_info['presale_start'] - current_time
                
                if time_until_start > 0:
                    self.logger.info(f"Presale starts in {time_until_start} seconds")
                    if time_until_start <= 60:  # 1 minute before start
                        self.logger.info("Preparing for presale start...")
                        await self.prepare_for_presale()
                        # Send presale start notification
                        await self.telegram.send_presale_start_notification(presale_info)
                    await asyncio.sleep(min(time_until_start, 10))
                    continue
                
                # Presale is active, check conditions
                if presale_info['is_active']:
                    # Calculate optimal buy amount
                    buy_amount = self.calculate_optimal_buy_amount(presale_info)
                    
                    if buy_amount > 0:
                        # Check gas conditions
                        current_gas = self.gas_optimizer.get_current_gas_price()
                        if self.gas_optimizer.is_gas_acceptable(current_gas):
                            success = await self.execute_buy_transaction(buy_amount)
                            if success:
                                self.logger.info("Buy transaction completed successfully!")
                                break
                        else:
                            self.logger.info("Waiting for better gas conditions...")
                            await self.telegram.send_gas_warning_notification(current_gas, self.config.MAX_GAS_PRICE)
                            await asyncio.sleep(5)
                    else:
                        self.logger.warning("No allocation available")
                        await asyncio.sleep(10)
                
                await asyncio.sleep(self.config.MONITOR_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await self.telegram.send_error_notification(str(e), "Monitoring loop")
                await asyncio.sleep(10)
    
    async def prepare_for_presale(self):
        """Prepare for presale start"""
        try:
            self.logger.info("Preparing for presale start...")
            
            # Check wallet balance
            if not self.check_wallet_balance():
                return False
            
            # Pre-approve transaction (if needed)
            # Some presales require pre-approval
            
            # Optimize gas settings
            gas_stats = self.gas_optimizer.get_gas_stats()
            if gas_stats:
                self.logger.info(f"Current gas conditions: {gas_stats['base_fee_gwei']:.2f} gwei")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing for presale: {e}")
            await self.telegram.send_error_notification(str(e), "Presale preparation")
            return False
    
    async def run(self):
        """Main bot run method"""
        try:
            self.logger.info("Starting Arbitrum Presale Bot...")
            
            # Send startup notification
            await self.telegram.send_startup_notification()
            
            # Initial checks
            if not self.check_network_connection():
                return False
            
            if not self.check_wallet_balance():
                return False
            
            # Validate presale contract
            presale_info = self.validate_presale_contract()
            if not presale_info:
                return False
            
            self.is_running = True
            
            # Send status update
            await self.telegram.send_bot_status_notification(self.get_status())
            
            # Start monitoring
            await self.monitor_presale_conditions()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error running bot: {e}")
            await self.telegram.send_error_notification(str(e), "Main bot execution")
            return False
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the bot"""
        self.logger.info("Stopping bot...")
        self.is_running = False
        # Send shutdown notification
        asyncio.create_task(self.telegram.send_shutdown_notification())
    
    def get_status(self):
        """Get bot status"""
        return {
            'is_running': self.is_running,
            'wallet_address': self.config.WALLET_ADDRESS,
            'presale_address': self.config.PRESALE_CONTRACT_ADDRESS,
            'last_transaction': self.last_transaction,
            'transaction_count': len(self.transaction_history)
        } 