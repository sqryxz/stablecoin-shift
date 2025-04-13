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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StablecoinMonitor:
    def __init__(self):
        # Using CoinGecko API with rate limiting
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        self.previous_supplies = {
            'FRAX': None,
            'DAI': None,
            'EURC': None,
            'ESDe': None
        }
        
        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 6.0  # Minimum 6 seconds between requests
        self.max_retries = 3
        self.retry_delay = 10  # Seconds to wait between retries
        
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

    async def get_stablecoin_data(self, session, coin_id):
        """Get stablecoin data with simple API endpoint."""
        url = f"{self.coingecko_api_url}/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=true&precision=4"
        data = await self.fetch_data(session, url)
        
        if data and coin_id in data:
            try:
                coin_data = data[coin_id]
                # For supply, we'll make a separate request
                supply_url = f"{self.coingecko_api_url}/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
                supply_data = await self.fetch_data(session, supply_url)
                
                if supply_data and 'market_data' in supply_data:
                    supply = float(supply_data['market_data'].get('total_supply', 0))
                    current_price = float(coin_data.get('usd', 1))
                    return {
                        'supply': supply,
                        'price': current_price
                    }
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing {coin_id} data: {str(e)}")
        return None

    def calculate_supply_change(self, current, previous):
        if previous is None:
            return 0
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
                    'esde_supply': None,
                    'esde_price': None,
                    'esde_supply_change': None
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

                # Add ESDe monitoring
                esde_data = await self.get_stablecoin_data(session, 'ethena-esde')
                if esde_data:
                    current_esde_supply = esde_data['supply']
                    esde_change = self.calculate_supply_change(
                        current_esde_supply,
                        self.previous_supplies['ESDe']
                    )
                    logger.info(f"ESDe Supply: {current_esde_supply:,.2f}")
                    logger.info(f"ESDe Price: ${esde_data['price']:.4f}")
                    logger.info(f"ESDe Supply Change: {esde_change:+.2f}%")
                    self.previous_supplies['ESDe'] = current_esde_supply
                    
                    data_entry.update({
                        'esde_supply': current_esde_supply,
                        'esde_price': esde_data['price'],
                        'esde_supply_change': esde_change
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