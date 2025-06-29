import time
import asyncio
from web3 import Web3
from eth_account import Account
import requests

class ArbitrumGasOptimizer:
    """Gas optimization for Arbitrum network"""
    
    def __init__(self, web3, config):
        self.web3 = web3
        self.config = config
        self.account = Account.from_key(config.PRIVATE_KEY)
        
    def get_current_gas_price(self):
        """Get current gas price from network"""
        try:
            gas_price = self.web3.eth.gas_price
            return gas_price
        except Exception as e:
            print(f"Error getting gas price: {e}")
            return self.config.MAX_GAS_PRICE
    
    def get_arbitrum_gas_estimate(self):
        """Get gas estimate optimized for Arbitrum"""
        try:
            # Arbitrum specific gas estimation
            base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = self.config.PRIORITY_FEE
            
            # Calculate max fee per gas (base fee + priority fee)
            max_fee_per_gas = base_fee + priority_fee
            
            # Ensure we don't exceed our maximum
            max_fee_per_gas = min(max_fee_per_gas, self.config.MAX_GAS_PRICE)
            
            return {
                'maxFeePerGas': max_fee_per_gas,
                'maxPriorityFeePerGas': priority_fee
            }
        except Exception as e:
            print(f"Error estimating Arbitrum gas: {e}")
            return {
                'maxFeePerGas': self.config.MAX_GAS_PRICE,
                'maxPriorityFeePerGas': self.config.PRIORITY_FEE
            }
    
    def optimize_gas_for_transaction(self, transaction_data):
        """Optimize gas parameters for a specific transaction"""
        try:
            # Estimate gas limit for the transaction
            estimated_gas = self.web3.eth.estimate_gas(transaction_data)
            
            # Add buffer for safety (20% buffer)
            gas_limit = int(estimated_gas * 1.2)
            
            # Get optimized gas price
            gas_params = self.get_arbitrum_gas_estimate()
            
            return {
                'gas': gas_limit,
                'maxFeePerGas': gas_params['maxFeePerGas'],
                'maxPriorityFeePerGas': gas_params['maxPriorityFeePerGas']
            }
        except Exception as e:
            print(f"Error optimizing gas: {e}")
            return {
                'gas': self.config.GAS_LIMIT,
                'maxFeePerGas': self.config.MAX_GAS_PRICE,
                'maxPriorityFeePerGas': self.config.PRIORITY_FEE
            }
    
    def wait_for_optimal_gas(self, max_wait_time=300):
        """Wait for optimal gas conditions"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            current_gas = self.get_current_gas_price()
            
            # If gas is below our threshold, proceed
            if current_gas <= self.config.MAX_GAS_PRICE:
                print(f"Gas price optimal: {self.web3.from_wei(current_gas, 'gwei')} gwei")
                return True
            
            print(f"Gas price too high: {self.web3.from_wei(current_gas, 'gwei')} gwei, waiting...")
            time.sleep(10)
        
        print("Timeout waiting for optimal gas price")
        return False
    
    def get_gas_stats(self):
        """Get current gas statistics"""
        try:
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']
            gas_used = latest_block['gasUsed']
            gas_limit = latest_block['gasLimit']
            
            return {
                'base_fee_gwei': self.web3.from_wei(base_fee, 'gwei'),
                'gas_used': gas_used,
                'gas_limit': gas_limit,
                'utilization': gas_used / gas_limit * 100
            }
        except Exception as e:
            print(f"Error getting gas stats: {e}")
            return None
    
    def calculate_transaction_cost(self, gas_limit, gas_price):
        """Calculate transaction cost in ETH"""
        total_cost = gas_limit * gas_price
        return self.web3.from_wei(total_cost, 'ether')
    
    def is_gas_acceptable(self, gas_price):
        """Check if gas price is acceptable"""
        return gas_price <= self.config.MAX_GAS_PRICE
    
    async def monitor_gas_conditions(self, callback=None):
        """Monitor gas conditions and execute callback when optimal"""
        while True:
            try:
                gas_stats = self.get_gas_stats()
                if gas_stats:
                    print(f"Gas Stats: Base Fee: {gas_stats['base_fee_gwei']:.2f} gwei, "
                          f"Utilization: {gas_stats['utilization']:.1f}%")
                    
                    # Check if conditions are optimal
                    if (gas_stats['base_fee_gwei'] <= self.config.MAX_GAS_PRICE / 1e9 and 
                        gas_stats['utilization'] < 80):
                        if callback:
                            await callback()
                        break
                
                await asyncio.sleep(self.config.MONITOR_INTERVAL)
                
            except Exception as e:
                print(f"Error monitoring gas: {e}")
                await asyncio.sleep(10) 