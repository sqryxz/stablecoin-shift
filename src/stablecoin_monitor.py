import asyncio
import aiohttp
import json
from datetime import datetime
import pandas as pd
import logging
import os
from pathlib import Path
import time
from typing import Optional, Dict, Any
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ERC20 ABI for totalSupply
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
    }
]

class StablecoinMonitor:
    def __init__(self):
        # Using CoinGecko API with rate limiting
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        self.previous_supplies = {
            'FRAX': None,
            'DAI': None,
            'EURC': None,
            'USDe': None
        }
        
        # Token IDs mapping
        self.token_ids = {
            'FRAX': 'frax',
            'DAI': 'dai',
            'EURC': 'euro-coin',
            'USDe': 'usde'
        }
        
        # Token contract addresses
        self.token_contracts = {
            'USDe': '0x4c9EDD5852cd905f086C759E8383e09bff1E68B3'  # USDe contract on Ethereum mainnet
        }
        
        # Initialize Web3
        self.eth_node_url = os.getenv('ETH_NODE_URL')
        if self.eth_node_url:
            self.w3 = Web3(Web3.HTTPProvider(self.eth_node_url))
            if self.w3.is_connected():
                logger.info("Connected to Ethereum node")
                # Initialize contract instances
                self.usde_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.token_contracts['USDe']),
                    abi=ERC20_ABI
                )
                logger.info("Initialized USDe contract")
            else:
                logger.warning("Failed to connect to Ethereum node")
                self.usde_contract = None
        else:
            logger.warning("ETH_NODE_URL not set, blockchain fallback won't be available")
            self.w3 = None
            self.usde_contract = None
        
        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 6.0  # Minimum 6 seconds between requests
        self.max_retries = 5  # Increased retries
        self.retry_delay = 15  # Increased delay between retries
        
        # Create data directory if it doesn't exist
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Define file paths
        self.json_file = self.data_dir / 'stablecoin_data.json'
        self.csv_file = self.data_dir / 'stablecoin_data.csv'
        
        # Load existing data if available
        self.historical_data = self.load_historical_data()

    def load_historical_data(self):
        """Load existing data from JSON file if it exists."""
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Error reading JSON file, starting with empty dataset")
        return []

    def save_to_json(self, new_data):
        """Save data to JSON file."""
        self.historical_data.append(new_data)
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    def save_to_csv(self):
        """Convert historical data to DataFrame and save as CSV."""
        try:
            df = pd.DataFrame(self.historical_data)
            df.to_csv(self.csv_file, index=False)
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    async def wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()

    async def fetch_data(self, session, url) -> Optional[Dict[str, Any]]:
        """Fetch data with retries and rate limiting."""
        for retry in range(self.max_retries):
            try:
                await self.wait_for_rate_limit()
                headers = {
                    'User-Agent': 'StablecoinMonitor/1.0',
                    'Accept': 'application/json'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limit exceeded
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.error(f"Error fetching data from {url}. Status: {response.status}")
                        if retry < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
            except Exception as e:
                logger.error(f"Exception while fetching data from {url}: {str(e)}")
                if retry < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        return None

    async def get_onchain_supply(self, token_address: str) -> Optional[Dict[str, float]]:
        """Get token supply directly from the blockchain."""
        if not self.w3 or not self.w3.is_connected():
            logger.error("Web3 not initialized or not connected")
            return None
            
        try:
            # Use pre-initialized contract for USDe
            if token_address == self.token_contracts['USDe'] and self.usde_contract:
                contract = self.usde_contract
            else:
                # Create contract instance with checksummed address
                checksummed_address = Web3.to_checksum_address(token_address)
                contract = self.w3.eth.contract(
                    address=checksummed_address,
                    abi=ERC20_ABI
                )
            
            # Create async tasks for both calls
            loop = asyncio.get_event_loop()
            
            # Make direct function calls
            total_supply_task = loop.run_in_executor(
                None,
                contract.functions.totalSupply().call
            )
            decimals_task = loop.run_in_executor(
                None,
                contract.functions.decimals().call
            )
            
            # Wait for both calls to complete
            total_supply, decimals = await asyncio.gather(total_supply_task, decimals_task)
            
            # Log raw values for debugging
            logger.info(f"Raw total supply: {total_supply}")
            logger.info(f"Raw decimals: {decimals}")
            
            # Ensure we have valid decimals
            if decimals == 0:
                decimals = 18  # Default to 18 decimals for ERC20 tokens
                logger.warning("Contract returned 0 for decimals, using default of 18")
            
            # Convert to proper decimal places
            supply = total_supply / (10 ** decimals)
            
            # Skip if supply is 0
            if total_supply == 0:
                logger.warning("Contract returned 0 for total supply")
                return {
                    'supply': 0,
                    'price': 1.0
                }
            
            logger.info(f"Successfully fetched on-chain supply for {token_address}")
            logger.info(f"Total Supply: {supply:,.2f}")
            logger.info(f"Decimals: {decimals}")
            
            return {
                'supply': supply,
                'price': 1.0  # Using 1.0 as default price for stablecoin
            }
        except Exception as e:
            logger.error(f"Error getting on-chain supply for {token_address}")
            logger.error(f"Exception details: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return None

    async def get_stablecoin_data(self, session, coin_id):
        """Get stablecoin data with enhanced error handling and retries."""
        # Special handling for USDe
        if coin_id == 'usde' and self.w3:
            logger.info("Using blockchain fallback for USDe data")
            onchain_data = await self.get_onchain_supply(self.token_contracts['USDe'])
            if onchain_data:
                logger.info(f"Successfully got USDe data from blockchain")
                return onchain_data
            else:
                logger.warning("Failed to get USDe data from blockchain, will try again next cycle")
                return {
                    'supply': 0,
                    'price': 1.0
                }
        
        url = f"{self.coingecko_api_url}/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=true&precision=4"
        data = await self.fetch_data(session, url)
        
        if not data or coin_id not in data:
            logger.warning(f"No price data available for {coin_id}, trying alternative endpoints...")
            # For USDe, try blockchain fallback if API fails
            if coin_id == 'usde' and self.w3:
                logger.info("Falling back to blockchain data for USDe")
                return await self.get_onchain_supply(self.token_contracts['USDe'])
            return None
        
        try:
            coin_data = data[coin_id]
            # For supply, we'll make a separate request with multiple retries
            for retry in range(self.max_retries):
                supply_url = f"{self.coingecko_api_url}/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
                supply_data = await self.fetch_data(session, supply_url)
                
                if supply_data and 'market_data' in supply_data:
                    supply = float(supply_data['market_data'].get('total_supply', 0))
                    if supply > 0:  # Validate supply data
                        current_price = float(coin_data.get('usd', 1))
                        return {
                            'supply': supply,
                            'price': current_price
                        }
                logger.warning(f"Retry {retry + 1}/{self.max_retries} for {coin_id} supply data")
                await asyncio.sleep(self.retry_delay)
            
            logger.error(f"Failed to get valid supply data for {coin_id} after {self.max_retries} retries")
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing {coin_id} data: {str(e)}")
        return None

    def calculate_supply_change(self, current, previous):
        """Calculate percentage change in supply with zero handling."""
        if previous is None or previous == 0:
            if current is None or current == 0:
                return 0.0  # No change if both values are 0/None
            return 100.0  # 100% increase if going from 0 to some value
        if current is None or current == 0:
            return -100.0  # 100% decrease if going from some value to 0
        return ((current - previous) / previous) * 100

    async def monitor_supplies(self):
        async with aiohttp.ClientSession() as session:
            while True:
                timestamp = datetime.now()
                logger.info(f"Fetching data at {timestamp}")
                
                # Prepare data entry
                data_entry = {
                    'timestamp': timestamp.isoformat(),
                    'frax_supply': None,
                    'frax_price': None,
                    'frax_supply_change': None,
                    'dai_supply': None,
                    'dai_price': None,
                    'dai_supply_change': None,
                    'eurc_supply': None,
                    'eurc_price': None,
                    'eurc_supply_change': None,
                    'usde_supply': None,
                    'usde_price': None,
                    'usde_supply_change': None
                }

                # Fetch data with delay between requests
                frax_data = await self.get_stablecoin_data(session, 'frax')
                if frax_data:
                    current_frax_supply = frax_data['supply']
                    frax_change = self.calculate_supply_change(
                        current_frax_supply,
                        self.previous_supplies['FRAX']
                    )
                    logger.info(f"FRAX Supply: {current_frax_supply:,.2f}")
                    logger.info(f"FRAX Price: ${frax_data['price']:.4f}")
                    logger.info(f"FRAX Supply Change: {frax_change:+.2f}%")
                    self.previous_supplies['FRAX'] = current_frax_supply
                    
                    data_entry.update({
                        'frax_supply': current_frax_supply,
                        'frax_price': frax_data['price'],
                        'frax_supply_change': frax_change
                    })

                await asyncio.sleep(2)  # Small delay between coins
                
                dai_data = await self.get_stablecoin_data(session, 'dai')
                if dai_data:
                    current_dai_supply = dai_data['supply']
                    dai_change = self.calculate_supply_change(
                        current_dai_supply,
                        self.previous_supplies['DAI']
                    )
                    logger.info(f"DAI Supply: {current_dai_supply:,.2f}")
                    logger.info(f"DAI Price: ${dai_data['price']:.4f}")
                    logger.info(f"DAI Supply Change: {dai_change:+.2f}%")
                    self.previous_supplies['DAI'] = current_dai_supply
                    
                    data_entry.update({
                        'dai_supply': current_dai_supply,
                        'dai_price': dai_data['price'],
                        'dai_supply_change': dai_change
                    })

                await asyncio.sleep(2)  # Small delay between coins

                # Add EURC monitoring
                eurc_data = await self.get_stablecoin_data(session, 'euro-coin')
                if eurc_data:
                    current_eurc_supply = eurc_data['supply']
                    eurc_change = self.calculate_supply_change(
                        current_eurc_supply,
                        self.previous_supplies['EURC']
                    )
                    logger.info(f"EURC Supply: {current_eurc_supply:,.2f}")
                    logger.info(f"EURC Price: ${eurc_data['price']:.4f}")
                    logger.info(f"EURC Supply Change: {eurc_change:+.2f}%")
                    self.previous_supplies['EURC'] = current_eurc_supply
                    
                    data_entry.update({
                        'eurc_supply': current_eurc_supply,
                        'eurc_price': eurc_data['price'],
                        'eurc_supply_change': eurc_change
                    })

                await asyncio.sleep(2)  # Small delay between coins

                # Add USDe monitoring
                usde_data = await self.get_stablecoin_data(session, 'usde')
                if usde_data:
                    current_usde_supply = usde_data['supply']
                    usde_change = self.calculate_supply_change(
                        current_usde_supply,
                        self.previous_supplies['USDe']
                    )
                    logger.info(f"USDe Supply: {current_usde_supply:,.2f}")
                    logger.info(f"USDe Price: ${usde_data['price']:.4f}")
                    logger.info(f"USDe Supply Change: {usde_change:+.2f}%")
                    self.previous_supplies['USDe'] = current_usde_supply
                    
                    data_entry.update({
                        'usde_supply': current_usde_supply,
                        'usde_price': usde_data['price'],
                        'usde_supply_change': usde_change
                    })

                # Save data to files
                self.save_to_json(data_entry)
                self.save_to_csv()

                logger.info("-" * 50)
                logger.info(f"Next update in 15 minutes at {(datetime.now() + pd.Timedelta(minutes=15)).strftime('%H:%M:%S')}")
                
                # Wait for 15 minutes before next check
                await asyncio.sleep(900)  # 15 minutes = 900 seconds

async def main():
    monitor = StablecoinMonitor()
    try:
        await monitor.monitor_supplies()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        # Save final data before exiting
        monitor.save_to_csv()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 