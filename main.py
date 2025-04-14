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
        hourly_velocity_data = await velocity_tracker.track_velocity()
        
        # Get the most recent velocity data point (first hour)
        velocity_data = hourly_velocity_data[0] if hourly_velocity_data else {}
        
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
                    'dai_supply_change': latest_data['dai_supply_change'],
                    'eurc_supply': latest_data['eurc_supply'],
                    'eurc_price': latest_data['eurc_price'],
                    'eurc_supply_change': latest_data['eurc_supply_change'],
                    'usde_supply': latest_data['usde_supply'],
                    'usde_price': latest_data['usde_price'],
                    'usde_supply_change': latest_data['usde_supply_change']
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

                # EURC Supply Analysis
                f.write("EURC Supply Metrics:\n")
                f.write(f"  - Current Supply: {supply_data['eurc_supply']:,.2f}\n")
                f.write(f"  - Current Price: ${supply_data['eurc_price']:.4f}\n")
                f.write(f"  - 24h Supply Change: {supply_data['eurc_supply_change']:+.2f}%\n\n")

                # USDe Supply Analysis
                f.write("USDe Supply Metrics:\n")
                f.write(f"  - Current Supply: {supply_data['usde_supply']:,.2f}\n")
                f.write(f"  - Current Price: ${supply_data['usde_price']:.4f}\n")
                f.write(f"  - 24h Supply Change: {supply_data['usde_supply_change']:+.2f}%\n\n")
            else:
                f.write("Supply data not available yet\n\n")
            
            # Velocity Analysis Section - Split by Token
            f.write("=== Velocity Analysis ===\n")
            
            if velocity_data:
                # FRAX Velocity Metrics
                f.write("FRAX Velocity Metrics:\n")
                if 'FRAX_velocity_ratio' in velocity_data:
                    f.write(f"  - Velocity Ratio: {velocity_data.get('FRAX_velocity_ratio', 0):.4f}\n")
                    f.write(f"  - Transaction Count: {velocity_data.get('FRAX_transaction_count', 0)}\n")
                    f.write(f"  - Unique Wallets: {velocity_data.get('FRAX_unique_wallets', 0)}\n")
                    f.write(f"  - Volume: {velocity_data.get('FRAX_volume_formatted', '0')}\n")
                    f.write(f"  - Token Supply: {velocity_data.get('FRAX_token_supply_formatted', '0')}\n")
                    f.write(f"  - Duplicate Transactions: {velocity_data.get('FRAX_duplicate_txs', 0)}\n\n")
                else:
                    f.write("  Data not available\n\n")
                
                # DAI Velocity Metrics
                f.write("DAI Velocity Metrics:\n")
                if 'DAI_velocity_ratio' in velocity_data:
                    f.write(f"  - Velocity Ratio: {velocity_data.get('DAI_velocity_ratio', 0):.4f}\n")
                    f.write(f"  - Transaction Count: {velocity_data.get('DAI_transaction_count', 0)}\n")
                    f.write(f"  - Unique Wallets: {velocity_data.get('DAI_unique_wallets', 0)}\n")
                    f.write(f"  - Volume: {velocity_data.get('DAI_volume_formatted', '0')}\n")
                    f.write(f"  - Token Supply: {velocity_data.get('DAI_token_supply_formatted', '0')}\n")
                    f.write(f"  - Duplicate Transactions: {velocity_data.get('DAI_duplicate_txs', 0)}\n\n")
                else:
                    f.write("  Data not available\n\n")

                # EURC Velocity Metrics
                f.write("EURC Velocity Metrics:\n")
                if 'EURC_velocity_ratio' in velocity_data:
                    f.write(f"  - Velocity Ratio: {velocity_data.get('EURC_velocity_ratio', 0):.4f}\n")
                    f.write(f"  - Transaction Count: {velocity_data.get('EURC_transaction_count', 0)}\n")
                    f.write(f"  - Unique Wallets: {velocity_data.get('EURC_unique_wallets', 0)}\n")
                    f.write(f"  - Volume: {velocity_data.get('EURC_volume_formatted', '0')}\n")
                    f.write(f"  - Token Supply: {velocity_data.get('EURC_token_supply_formatted', '0')}\n")
                    f.write(f"  - Duplicate Transactions: {velocity_data.get('EURC_duplicate_txs', 0)}\n\n")
                else:
                    f.write("  Data not available\n\n")

                # USDe Velocity Metrics
                f.write("USDe Velocity Metrics:\n")
                if 'USDe_velocity_ratio' in velocity_data:
                    f.write(f"  - Velocity Ratio: {velocity_data.get('USDe_velocity_ratio', 0):.4f}\n")
                    f.write(f"  - Transaction Count: {velocity_data.get('USDe_transaction_count', 0)}\n")
                    f.write(f"  - Unique Wallets: {velocity_data.get('USDe_unique_wallets', 0)}\n")
                    f.write(f"  - Volume: {velocity_data.get('USDe_volume_formatted', '0')}\n")
                    f.write(f"  - Token Supply: {velocity_data.get('USDe_token_supply_formatted', '0')}\n")
                    f.write(f"  - Duplicate Transactions: {velocity_data.get('USDe_duplicate_txs', 0)}\n")
                else:
                    f.write("  Data not available\n")
            else:
                f.write("Velocity data not available\n")
        
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