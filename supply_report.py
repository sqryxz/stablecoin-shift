import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_data(file_path='data/stablecoin_data.csv'):
    """Load and prepare the stablecoin data."""
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Fill NaN values with 0 for supply changes
    df['frax_supply_change'] = df['frax_supply_change'].fillna(0)
    df['dai_supply_change'] = df['dai_supply_change'].fillna(0)
    df['eurc_supply_change'] = df['eurc_supply_change'].fillna(0)
    df['esde_supply_change'] = df['esde_supply_change'].fillna(0)
    
    # Forward fill prices and supply values
    df['frax_price'] = df['frax_price'].fillna(method='ffill')
    df['dai_price'] = df['dai_price'].fillna(method='ffill')
    df['eurc_price'] = df['eurc_price'].fillna(method='ffill')
    df['esde_price'] = df['esde_price'].fillna(method='ffill')
    df['frax_supply'] = df['frax_supply'].fillna(method='ffill')
    df['dai_supply'] = df['dai_supply'].fillna(method='ffill')
    df['eurc_supply'] = df['eurc_supply'].fillna(method='ffill')
    df['esde_supply'] = df['esde_supply'].fillna(method='ffill')
    
    return df

def analyze_supply_changes(df, window_hours=2):
    """Analyze supply changes over specified time windows."""
    changes = []
    
    # Group data into time windows
    df['time_window'] = df['timestamp'].dt.floor(f'{window_hours}H')
    
    for window_start in df['time_window'].unique():
        window_data = df[df['time_window'] == window_start]
        
        # Check for any non-zero supply changes
        frax_changes = window_data[np.abs(window_data['frax_supply_change']) > 0.0001]
        dai_changes = window_data[np.abs(window_data['dai_supply_change']) > 0.0001]
        eurc_changes = window_data[np.abs(window_data['eurc_supply_change']) > 0.0001]
        esde_changes = window_data[np.abs(window_data['esde_supply_change']) > 0.0001]
        
        if not frax_changes.empty:
            for _, row in frax_changes.iterrows():
                changes.append({
                    'timestamp': row['timestamp'],
                    'token': 'FRAX',
                    'supply_change_pct': row['frax_supply_change'],
                    'price': row['frax_price'],
                    'supply': row['frax_supply']
                })
                
        if not dai_changes.empty:
            for _, row in dai_changes.iterrows():
                changes.append({
                    'timestamp': row['timestamp'],
                    'token': 'DAI',
                    'supply_change_pct': row['dai_supply_change'],
                    'price': row['dai_price'],
                    'supply': row['dai_supply']
                })

        if not eurc_changes.empty:
            for _, row in eurc_changes.iterrows():
                changes.append({
                    'timestamp': row['timestamp'],
                    'token': 'EURC',
                    'supply_change_pct': row['eurc_supply_change'],
                    'price': row['eurc_price'],
                    'supply': row['eurc_supply']
                })

        if not esde_changes.empty:
            for _, row in esde_changes.iterrows():
                changes.append({
                    'timestamp': row['timestamp'],
                    'token': 'ESDe',
                    'supply_change_pct': row['esde_supply_change'],
                    'price': row['esde_price'],
                    'supply': row['esde_supply']
                })
    
    return changes

def generate_report(changes):
    """Generate a formatted report from the changes."""
    if not changes:
        return "No significant supply changes detected in the analyzed period."
    
    report = "Stablecoin Supply Change Report\n"
    report += "=" * 50 + "\n\n"
    
    for change in changes:
        report += f"Time: {change['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Token: {change['token']}\n"
        report += f"Supply Change: {change['supply_change_pct']:.4f}%\n"
        report += f"Current Supply: {change['supply']:,.2f}\n"
        report += f"Token Price: ${change['price']:.4f}\n"
        report += "-" * 30 + "\n"
    
    return report

def main():
    """Main function to run the report generation."""
    try:
        # Load data
        df = load_data()
        
        # Analyze changes
        changes = analyze_supply_changes(df)
        
        # Generate and print report
        report = generate_report(changes)
        print(report)
        
        # Optionally save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/supply_report_{timestamp}.txt"
        
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_path}")
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    main() 