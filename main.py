#!/usr/bin/env python3

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

from src.velocity_tracker import StablecoinVelocityTracker
from src.stablecoin_monitor import StablecoinMonitor

def setup_directories():
    """Create necessary directories if they don't exist."""
    Path("data").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

async def generate_consolidated_report():
    """Generate a consolidated report combining velocity and supply data."""
    # Initialize trackers
    velocity_tracker = StablecoinVelocityTracker()
    stablecoin_monitor = StablecoinMonitor()

    # Get current timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Run velocity tracking
        velocity_data = await velocity_tracker.track_velocity()
        
        # Run supply monitoring - this is a continuous monitoring task
        # We'll just get the initial data point
        supply_monitor_task = asyncio.create_task(stablecoin_monitor.monitor_supplies())
        try:
            # Wait for a short time to get initial data
            await asyncio.wait_for(supply_monitor_task, timeout=30.0)
        except asyncio.TimeoutError:
            # Cancel the continuous monitoring after getting initial data
            supply_monitor_task.cancel()
            try:
                await supply_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Load the most recent data from the CSV file
        supply_data = {}
        if os.path.exists('data/stablecoin_data.csv'):
            import pandas as pd
            df = pd.read_csv('data/stablecoin_data.csv')
            if not df.empty:
                latest_data = df.iloc[-1]
                supply_data = {
                    'frax_supply': latest_data['frax_supply'],
                    'frax_price': latest_data['frax_price'],
                    'frax_supply_change': latest_data['frax_supply_change'],
                    'dai_supply': latest_data['dai_supply'],
                    'dai_price': latest_data['dai_price'],
                    'dai_supply_change': latest_data['dai_supply_change']
                }
        
        # Generate consolidated report
        report_path = f"reports/consolidated_report_{timestamp}.txt"
        
        with open(report_path, 'w') as f:
            f.write("=== Stablecoin Analysis Consolidated Report ===\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Supply Analysis Section First
            f.write("=== Supply Analysis ===\n")
            if supply_data:
                # FRAX Supply Analysis
                f.write("FRAX Supply Metrics:\n")
                f.write(f"  - Current Supply: {supply_data['frax_supply']:,.2f}\n")
                f.write(f"  - Current Price: ${supply_data['frax_price']:.4f}\n")
                f.write(f"  - 24h Supply Change: {supply_data['frax_supply_change']:+.2f}%\n\n")
                
                # DAI Supply Analysis
                f.write("DAI Supply Metrics:\n")
                f.write(f"  - Current Supply: {supply_data['dai_supply']:,.2f}\n")
                f.write(f"  - Current Price: ${supply_data['dai_price']:.4f}\n")
                f.write(f"  - 24h Supply Change: {supply_data['dai_supply_change']:+.2f}%\n\n")
            else:
                f.write("Supply data not available yet\n\n")
            
            # Velocity Analysis Section - Split by Token
            f.write("=== Velocity Analysis ===\n")
            
            # FRAX Velocity Metrics
            f.write("FRAX Velocity Metrics:\n")
            f.write(f"  - Velocity Ratio: {velocity_data['FRAX_velocity_ratio']:.4f}\n")
            f.write(f"  - Transaction Count: {velocity_data['FRAX_transaction_count']}\n")
            f.write(f"  - Unique Wallets: {velocity_data['FRAX_unique_wallets']}\n")
            f.write(f"  - Volume: {velocity_data['FRAX_volume_formatted']}\n")
            f.write(f"  - Token Supply: {velocity_data['FRAX_token_supply_formatted']}\n")
            f.write(f"  - Duplicate Transactions: {velocity_data['FRAX_duplicate_txs']}\n\n")
            
            # DAI Velocity Metrics
            f.write("DAI Velocity Metrics:\n")
            f.write(f"  - Velocity Ratio: {velocity_data['DAI_velocity_ratio']:.4f}\n")
            f.write(f"  - Transaction Count: {velocity_data['DAI_transaction_count']}\n")
            f.write(f"  - Unique Wallets: {velocity_data['DAI_unique_wallets']}\n")
            f.write(f"  - Volume: {velocity_data['DAI_volume_formatted']}\n")
            f.write(f"  - Token Supply: {velocity_data['DAI_token_supply_formatted']}\n")
            f.write(f"  - Duplicate Transactions: {velocity_data['DAI_duplicate_txs']}\n")
        
        print(f"Consolidated report generated successfully: {report_path}")
        return True
        
    except Exception as e:
        print(f"Error generating consolidated report: {str(e)}")
        return False

async def main():
    """Main function to run the consolidated analysis."""
    print("Starting consolidated stablecoin analysis...")
    
    # Ensure required directories exist
    setup_directories()
    
    # Generate consolidated report
    success = await generate_consolidated_report()
    
    if success:
        print("Analysis completed successfully!")
    else:
        print("Analysis failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 