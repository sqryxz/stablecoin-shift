import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from web3 import Web3
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import aiohttp
from typing import Dict, List, Tuple
from dotenv import load_dotenv, find_dotenv
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
logger.info(f"Loading .env file from: {env_path}")

# Force reload of environment variables
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        env_content = f.read()
        logger.info(f"Environment file contents: {env_content}")
    
    load_dotenv(env_path, override=True)
    eth_node_url = os.getenv('ETH_NODE_URL')
    logger.info(f"Loaded ETH_NODE_URL: {eth_node_url}")
else:
    logger.error(f".env file not found at {env_path}")
    sys.exit(1)

class StablecoinVelocityTracker:
    def __init__(self):
        self.eth_node_url = eth_node_url
        logger.info(f"Using Ethereum node URL: {self.eth_node_url}")
        
        if not self.eth_node_url:
            raise ValueError("ETH_NODE_URL environment variable is not set")
            
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
            
        self.w3 = Web3()  # Only used for helper functions, not for connections
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.velocity_data_file = os.path.join(self.data_dir, 'velocity_data.csv')
        self.summary_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        
        # Token contract addresses (Ethereum mainnet)
        self.tokens = {
            'FRAX': '0x853d955acef822db058eb8505911ed77f175b99e',
            'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f'
        }
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)
        
        logger.info("Initialized StablecoinVelocityTracker")

    async def get_current_block(self) -> int:
        """Get the current block number."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.eth_node_url,
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1
                    },
                    timeout=30
                ) as response:
                    result = await response.json()
                    if 'error' in result:
                        logger.error(f"Error getting block number: {result['error']}")
                        return 0
                    return int(result['result'], 16)
        except Exception as e:
            logger.error(f"Error getting current block: {str(e)}")
            return 0

    async def fetch_token_transactions(self, token_address: str, start_block: int, end_block: int) -> List[dict]:
        """Fetch token transfer events for a given token address."""
        try:
            transfer_event_signature = self.w3.keccak(text="Transfer(address,address,uint256)").hex()
            
            params = {
                "fromBlock": hex(start_block),
                "toBlock": hex(end_block),
                "address": token_address,
                "topics": [transfer_event_signature]
            }
            
            logger.info(f"Fetching transactions for token {token_address} from block {start_block} to {end_block}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.eth_node_url,
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_getLogs",
                        "params": [params]
                    },
                    timeout=30
                ) as response:
                    result = await response.json()
                    if 'error' in result:
                        logger.error(f"Error fetching transactions: {result['error']}")
                        return []
                    transactions = result.get('result', [])
                    logger.info(f"Found {len(transactions)} transactions")
                    return transactions
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            return []

    def calculate_velocity_metrics(self, transactions: List[dict], token_supply: float) -> Dict:
        """Calculate velocity metrics from transaction data."""
        try:
            tx_count = len(transactions)
            unique_wallets = set()
            volume = 0
            processed_txs = set()  # Track unique transaction hashes
            
            # Log the first few transactions for debugging
            for i, tx in enumerate(transactions):
                # Skip if we've seen this transaction before
                tx_hash = tx.get('transactionHash', '')
                if tx_hash in processed_txs:
                    logger.warning(f"Duplicate transaction found: {tx_hash}")
                    continue
                processed_txs.add(tx_hash)
                
                from_addr = '0x' + tx['topics'][1][-40:]
                to_addr = '0x' + tx['topics'][2][-40:]
                
                # Convert value from hex and adjust for decimals
                value = int(tx['data'], 16) / (10 ** 18)  # Assuming 18 decimals
                
                # Skip zero-value transfers
                if value == 0:
                    logger.debug(f"Skipping zero-value transfer: {tx_hash}")
                    continue
                
                unique_wallets.add(from_addr)
                unique_wallets.add(to_addr)
                volume += value
                
                # Log details of first 5 non-zero transactions
                if i < 5:
                    logger.info(f"Transaction {i+1}:")
                    logger.info(f"  Hash: {tx_hash}")
                    logger.info(f"  From: {from_addr}")
                    logger.info(f"  To: {to_addr}")
                    logger.info(f"  Value: {value:,.2f}")
            
            # Calculate metrics
            actual_tx_count = len(processed_txs)
            metrics = {
                'transaction_count': actual_tx_count,
                'unique_wallets': len(unique_wallets),
                'volume': volume,
                'volume_formatted': f"{volume:,.2f}",
                'token_supply': token_supply,
                'token_supply_formatted': f"{token_supply:,.2f}",
                'velocity_ratio': (volume / token_supply) if token_supply > 0 else 0,
                'duplicate_txs': tx_count - actual_tx_count
            }
            
            logger.info(f"Detailed metrics: {json.dumps(metrics, indent=2)}")
            
            # Log warning if velocity ratio seems unusually high
            if metrics['velocity_ratio'] > 1.0:
                logger.warning(f"High velocity ratio detected: {metrics['velocity_ratio']:.2f}")
                logger.warning(f"Volume: {metrics['volume_formatted']}")
                logger.warning(f"Token Supply: {metrics['token_supply_formatted']}")
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {
                'transaction_count': 0,
                'unique_wallets': 0,
                'volume': 0,
                'volume_formatted': "0.00",
                'token_supply': 0,
                'token_supply_formatted': "0.00",
                'velocity_ratio': 0,
                'duplicate_txs': 0
            }

    async def get_token_supply(self, token_address: str) -> float:
        """Get current token supply."""
        try:
            total_supply_sig = self.w3.keccak(text="totalSupply()").hex()[:10]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.eth_node_url,
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_call",
                        "params": [{"to": token_address, "data": total_supply_sig}, "latest"]
                    },
                    timeout=30
                ) as response:
                    result = await response.json()
                    if 'error' in result:
                        logger.error(f"Error fetching token supply: {result['error']}")
                        return 0
                    supply = int(result['result'], 16) / (10 ** 18)  # Assuming 18 decimals
                    logger.info(f"Token {token_address} supply: {supply}")
                    return supply
        except Exception as e:
            logger.error(f"Error getting token supply: {str(e)}")
            return 0

    def generate_daily_report(self, data: pd.DataFrame) -> None:
        """Generate daily velocity report with visualizations."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            report_file = os.path.join(self.summary_dir, f'velocity_report_{today}.html')
            
            logger.info("Generating daily report...")
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Daily Transaction Count', 'Velocity Ratio'),
                vertical_spacing=0.2
            )
            
            # Add transaction count traces
            for token in ['FRAX', 'DAI']:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[f'{token}_transaction_count'],
                        name=f'{token} Transactions',
                        mode='lines'
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[f'{token}_velocity_ratio'],
                        name=f'{token} Velocity',
                        mode='lines'
                    ),
                    row=2, col=1
                )
            
            fig.update_layout(
                title='Stablecoin Velocity Analysis',
                height=800,
                showlegend=True
            )
            
            # Save the plot
            fig.write_html(report_file)
            logger.info(f"Saved velocity report to {report_file}")
            
            # Generate summary statistics
            summary = data.tail(1).to_dict('records')[0]
            summary_file = os.path.join(self.summary_dir, f'velocity_summary_{today}.json')
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=4)
            logger.info(f"Saved velocity summary to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")

    async def track_velocity(self):
        """Main function to track velocity metrics."""
        try:
            logger.info("Starting velocity tracking...")
            
            # Get current block number
            current_block = await self.get_current_block()
            if current_block == 0:
                raise ValueError("Failed to get current block number")
            
            # Calculate start block (approximately 24 hours ago)
            # Ethereum averages ~15 seconds per block, so 24 hours ≈ 5760 blocks
            start_block = current_block - 5760
            
            logger.info(f"Analyzing blocks from {start_block} to {current_block}")
            logger.info(f"Block range: {current_block - start_block} blocks")
            
            # Verify block range is reasonable
            if current_block - start_block > 6500:  # Allow some margin for block time variations
                logger.warning(f"Block range seems too large: {current_block - start_block} blocks")
            elif current_block - start_block < 5000:  # Allow some margin for block time variations
                logger.warning(f"Block range seems too small: {current_block - start_block} blocks")
            
            velocity_data = {}
            
            # Fetch data for each token
            for token_name, token_address in self.tokens.items():
                logger.info(f"Processing {token_name}...")
                transactions = await self.fetch_token_transactions(token_address, start_block, current_block)
                token_supply = await self.get_token_supply(token_address)
                metrics = self.calculate_velocity_metrics(transactions, token_supply)
                
                for key, value in metrics.items():
                    velocity_data[f'{token_name}_{key}'] = value
            
            # Save to CSV
            df = pd.DataFrame([velocity_data], index=[datetime.now()])
            
            if os.path.exists(self.velocity_data_file):
                existing_df = pd.read_csv(self.velocity_data_file, index_col=0, parse_dates=True)
                df = pd.concat([existing_df, df])
            
            df.to_csv(self.velocity_data_file)
            logger.info(f"Saved velocity data to {self.velocity_data_file}")
            
            # Generate daily report
            self.generate_daily_report(df)
            logger.info("Completed velocity tracking")
            
        except Exception as e:
            logger.error(f"Error in track_velocity: {str(e)}")
            raise

async def main():
    try:
        tracker = StablecoinVelocityTracker()
        await tracker.track_velocity()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 