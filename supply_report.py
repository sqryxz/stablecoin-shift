import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_data(file_path='data/stablecoin_data.csv'):
    """Load and prepare the stablecoin data."""
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Fill NaN values with 0 for supply changes
    for token in ['frax', 'dai', 'eurc', 'usde']:
        df[f'{token}_supply_change'] = df[f'{token}_supply_change'].fillna(0)
        # Use ffill() instead of deprecated fillna(method='ffill')
        df[f'{token}_price'] = df[f'{token}_price'].fillna(1.0).ffill()  # Default price to 1.0
        df[f'{token}_supply'] = df[f'{token}_supply'].fillna(0).ffill()  # Default supply to 0
    
    return df

def analyze_supply_changes(df, window_hours=2):
    """Analyze supply changes over specified time windows."""
    changes = []
    
    # Group data into time windows
    df['time_window'] = df['timestamp'].dt.floor(f'{window_hours}H')
    
    # Different thresholds for different tokens
    thresholds = {
        'frax': 0.0001,
        'dai': 0.0001,
        'eurc': 0.00001,  # Much more sensitive threshold for EURC
        'usde': 0.00001   # Much more sensitive threshold for USDe
    }
    
    # Get the latest data point for each token
    latest_data = df.iloc[-1]
    for token in ['frax', 'dai', 'eurc', 'usde']:
        changes.append({
            'timestamp': latest_data['timestamp'],
            'token': token.upper(),
            'supply_change_pct': latest_data[f'{token}_supply_change'],
            'price': latest_data[f'{token}_price'],
            'supply': latest_data[f'{token}_supply']
        })
    
    # Also include historical changes that exceed thresholds
    for window_start in df['time_window'].unique():
        window_data = df[df['time_window'] == window_start]
        
        # Check for any non-zero supply changes
        for token in ['frax', 'dai', 'eurc', 'usde']:
            token_changes = window_data[
                np.abs(window_data[f'{token}_supply_change']) > thresholds[token]
            ]
            
            if not token_changes.empty:
                for _, row in token_changes.iterrows():
                    # Only add if it's not the latest data point
                    if row['timestamp'] != latest_data['timestamp']:
                        changes.append({
                            'timestamp': row['timestamp'],
                            'token': token.upper(),
                            'supply_change_pct': row[f'{token}_supply_change'],
                            'price': row[f'{token}_price'],
                            'supply': row[f'{token}_supply']
                        })
    
    # Sort changes by timestamp
    changes.sort(key=lambda x: x['timestamp'])
    return changes

def generate_report(changes):
    """Generate a formatted report from the changes."""
    report = "Stablecoin Supply Change Report\n"
    report += "=" * 50 + "\n\n"
    
    # Group changes by token for better organization
    token_changes = {}
    for change in changes:
        token = change['token']
        if token not in token_changes:
            token_changes[token] = []
        token_changes[token].append(change)
    
    # Report for each token
    for token in ['FRAX', 'DAI', 'EURC', 'USDe']:
        report += f"\n{token} Changes:\n"
        report += "-" * 30 + "\n"
        if token in token_changes:
            for change in token_changes[token]:
                report += f"Time: {change['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += f"Supply Change: {change['supply_change_pct']:.4f}%\n"
                report += f"Current Supply: {change['supply']:,.2f}\n"
                report += f"Token Price: ${change['price']:.4f}\n"
                report += "-" * 30 + "\n"
        else:
            report += "No data available\n"
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
        
        # Save report to file
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