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
            'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
            'EURC': '0x1aBaEA1f7C830bD89Acc67eC4af516284b1bC33c',
            'ESDe': '0x49Ec3e1335490d1c5C77A6aB77c1e3F6c19Fdf31'  # Ethena Labs ESDe
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
            high_value_txs = []  # Track high value transactions
            
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
                
                # Track high value transactions (>100k tokens)
                if value > 100000:
                    high_value_txs.append({
                        'hash': tx_hash,
                        'from': from_addr,
                        'to': to_addr,
                        'value': value
                    })
                
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
                logger.warning("High value transactions in this period:")
                # Sort high value transactions by value
                high_value_txs.sort(key=lambda x: x['value'], reverse=True)
                for tx in high_value_txs:
                    logger.warning(f"  Hash: {tx['hash']}")
                    logger.warning(f"  From: {tx['from']}")
                    logger.warning(f"  To: {tx['to']}")
                    logger.warning(f"  Value: {tx['value']:,.2f}")
                    logger.warning("  ---")
            
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
        """Generate daily velocity report with hourly visualizations."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            report_file = os.path.join(self.summary_dir, f'velocity_report_{today}.html')
            
            logger.info("Generating daily report with hourly data...")
            
            # Create subplots for each metric
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=(
                    'Hourly Transaction Count',
                    'Hourly Velocity Ratio',
                    'Hourly Trading Volume'
                ),
                vertical_spacing=0.15,
                row_heights=[0.33, 0.33, 0.33]
            )
            
            # Add traces for each token
            for token in ['FRAX', 'DAI', 'EURC', 'ESDe']:
                # Transaction count
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[f'{token}_transaction_count'],
                        name=f'{token} Transactions',
                        mode='lines+markers'
                    ),
                    row=1, col=1
                )
                
                # Velocity ratio
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[f'{token}_velocity_ratio'],
                        name=f'{token} Velocity',
                        mode='lines+markers'
                    ),
                    row=2, col=1
                )
                
                # Volume
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[f'{token}_volume'],
                        name=f'{token} Volume',
                        mode='lines+markers'
                    ),
                    row=3, col=1
                )
            
            # Update layout
            fig.update_layout(
                title='Stablecoin Velocity Analysis (24-Hour Hourly Breakdown)',
                height=1200,
                showlegend=True,
                hovermode='x unified'
            )
            
            # Update y-axes labels
            fig.update_yaxes(title_text="Transaction Count", row=1, col=1)
            fig.update_yaxes(title_text="Velocity Ratio", row=2, col=1)
            fig.update_yaxes(title_text="Volume", row=3, col=1)
            
            # Update x-axes to show time properly
            for i in range(1, 4):
                fig.update_xaxes(
                    title_text="Time",
                    tickformat="%H:%M",
                    row=i,
                    col=1
                )
            
            # Save the plot
            fig.write_html(report_file)
            logger.info(f"Saved velocity report to {report_file}")
            
            # Generate summary statistics for the last 24 hours
            summary = {
                'start_time': data.index.min().strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': data.index.max().strftime('%Y-%m-%d %H:%M:%S'),
                'FRAX': {
                    'avg_velocity': float(data['FRAX_velocity_ratio'].mean()),
                    'max_velocity': float(data['FRAX_velocity_ratio'].max()),
                    'total_transactions': int(data['FRAX_transaction_count'].sum()),
                    'total_volume': float(data['FRAX_volume'].sum()),
                    'avg_unique_wallets': float(data['FRAX_unique_wallets'].mean())
                },
                'DAI': {
                    'avg_velocity': float(data['DAI_velocity_ratio'].mean()),
                    'max_velocity': float(data['DAI_velocity_ratio'].max()),
                    'total_transactions': int(data['DAI_transaction_count'].sum()),
                    'total_volume': float(data['DAI_volume'].sum()),
                    'avg_unique_wallets': float(data['DAI_unique_wallets'].mean())
                },
                'EURC': {
                    'avg_velocity': float(data['EURC_velocity_ratio'].mean()),
                    'max_velocity': float(data['EURC_velocity_ratio'].max()),
                    'total_transactions': int(data['EURC_transaction_count'].sum()),
                    'total_volume': float(data['EURC_volume'].sum()),
                    'avg_unique_wallets': float(data['EURC_unique_wallets'].mean())
                },
                'ESDe': {
                    'avg_velocity': float(data['ESDe_velocity_ratio'].mean()),
                    'max_velocity': float(data['ESDe_velocity_ratio'].max()),
                    'total_transactions': int(data['ESDe_transaction_count'].sum()),
                    'total_volume': float(data['ESDe_volume'].sum()),
                    'avg_unique_wallets': float(data['ESDe_unique_wallets'].mean())
                }
            }
            
            summary_file = os.path.join(self.summary_dir, f'velocity_summary_{today}.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=4)
            logger.info(f"Saved velocity summary to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")

    async def track_velocity(self):
        """Main function to track velocity metrics for 24 hourly intervals."""
        try:
            logger.info("Starting hourly velocity tracking...")
            
            # Get current block number
            current_block = await self.get_current_block()
            if current_block == 0:
                raise ValueError("Failed to get current block number")
            
            # Calculate blocks for 24 hours with hourly intervals
            # Ethereum averages ~15 seconds per block
            # 1 hour ≈ 240 blocks (3600 seconds / 15 seconds)
            blocks_per_hour = 240
            total_hours = 24
            hourly_data = []
            
            for hour in range(total_hours):
                end_block = current_block - (hour * blocks_per_hour)
                start_block = end_block - blocks_per_hour
                
                logger.info(f"Processing hour {hour + 1}/{total_hours}")
                logger.info(f"Analyzing blocks from {start_block} to {end_block}")
                
                velocity_data = {}
                timestamp = datetime.now() - timedelta(hours=hour)
                
                # Fetch data for each token
                for token_name, token_address in self.tokens.items():
                    logger.info(f"Processing {token_name} for hour {hour + 1}...")
                    transactions = await self.fetch_token_transactions(token_address, start_block, end_block)
                    token_supply = await self.get_token_supply(token_address)
                    metrics = self.calculate_velocity_metrics(transactions, token_supply)
                    
                    for key, value in metrics.items():
                        velocity_data[f'{token_name}_{key}'] = value
                
                velocity_data['timestamp'] = timestamp
                velocity_data['hour'] = hour
                velocity_data['start_block'] = start_block
                velocity_data['end_block'] = end_block
                hourly_data.append(velocity_data)
            
            # Convert to DataFrame and sort by timestamp
            df = pd.DataFrame(hourly_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Save to CSV
            if os.path.exists(self.velocity_data_file):
                existing_df = pd.read_csv(self.velocity_data_file, index_col=0, parse_dates=True)
                # Remove any existing data for the time range we just collected
                existing_df = existing_df[~existing_df.index.isin(df.index)]
                df = pd.concat([existing_df, df])
            
            df.to_csv(self.velocity_data_file)
            logger.info(f"Saved hourly velocity data to {self.velocity_data_file}")
            
            # Generate daily report with hourly data
            self.generate_daily_report(df)
            logger.info("Completed hourly velocity tracking")
            
            # Return the hourly data
            return hourly_data
            
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