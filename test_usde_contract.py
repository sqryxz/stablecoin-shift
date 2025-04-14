from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Web3
eth_node_url = os.getenv('ETH_NODE_URL')
w3 = Web3(Web3.HTTPProvider(eth_node_url))

# Contract details
USDE_ADDRESS = '0x4c9EDD5852cd905f086C759E8383e09bff1E68B3'
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    print(f"Connected to Ethereum node: {w3.is_connected()}")
    
    # Create contract instance
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(USDE_ADDRESS),
        abi=ERC20_ABI
    )
    
    try:
        # Get token symbol
        symbol = contract.functions.symbol().call()
        print(f"\nToken Symbol: {symbol}")
    except Exception as e:
        print(f"Error getting symbol: {str(e)}")
    
    try:
        # Get decimals
        decimals = contract.functions.decimals().call()
        print(f"Decimals: {decimals}")
    except Exception as e:
        print(f"Error getting decimals: {str(e)}")
    
    try:
        # Get total supply
        total_supply = contract.functions.totalSupply().call()
        print(f"Raw total supply: {total_supply}")
        
        # Convert to proper decimal places
        if decimals > 0:
            supply = total_supply / (10 ** decimals)
            print(f"Formatted supply: {supply:,.2f}")
    except Exception as e:
        print(f"Error getting total supply: {str(e)}")

if __name__ == "__main__":
    main() 