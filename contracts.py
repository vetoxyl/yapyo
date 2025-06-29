from web3 import Web3
from eth_abi import encode

class PresaleContracts:
    """Common presale contract ABIs and functions"""
    
    # Standard ERC20 ABI
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    # Common Presale ABI (PinkSale, DxSale, etc.)
    PRESALE_ABI = [
        {
            "inputs": [],
            "name": "buy",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [{"name": "amount", "type": "uint256"}],
            "name": "buy",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "getTokenPrice",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "getTokensForEth",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "presaleEndTime",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "presaleStartTime",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "softCap",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "hardCap",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "totalRaised",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "token",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "isPresaleActive",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Uniswap V2 Router ABI (for post-presale swaps)
    UNISWAP_V2_ROUTER_ABI = [
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    @staticmethod
    def get_presale_info(web3, contract_address):
        """Get presale contract information"""
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=PresaleContracts.PRESALE_ABI
        )
        
        try:
            info = {
                'token_address': contract.functions.token().call(),
                'presale_start': contract.functions.presaleStartTime().call(),
                'presale_end': contract.functions.presaleEndTime().call(),
                'soft_cap': contract.functions.softCap().call(),
                'hard_cap': contract.functions.hardCap().call(),
                'total_raised': contract.functions.totalRaised().call(),
                'is_active': contract.functions.isPresaleActive().call(),
                'token_price': contract.functions.getTokenPrice().call()
            }
            return info
        except Exception as e:
            raise Exception(f"Failed to get presale info: {str(e)}")
    
    @staticmethod
    def calculate_tokens_for_eth(web3, contract_address, eth_amount):
        """Calculate tokens received for ETH amount"""
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=PresaleContracts.PRESALE_ABI
        )
        
        try:
            # Try to get tokens for 1 ETH first
            tokens_per_eth = contract.functions.getTokensForEth().call()
            return tokens_per_eth * eth_amount
        except Exception as e:
            # Fallback to price calculation
            try:
                token_price = contract.functions.getTokenPrice().call()
                return (eth_amount * 10**18) // token_price
            except Exception as e2:
                raise Exception(f"Failed to calculate tokens: {str(e2)}")
    
    @staticmethod
    def build_buy_transaction(web3, contract_address, eth_amount, gas_price, gas_limit):
        """Build presale buy transaction"""
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=PresaleContracts.PRESALE_ABI
        )
        
        # Build transaction
        transaction = contract.functions.buy().build_transaction({
            'from': web3.eth.default_account,
            'value': web3.to_wei(eth_amount, 'ether'),
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(web3.eth.default_account)
        })
        
        return transaction 