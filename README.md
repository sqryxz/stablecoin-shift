# Stablecoin Supply Shift Monitor

A Python-based tool for monitoring and analyzing supply changes in major stablecoins (FRAX, DAI, EURC, and ESDe). This tool generates periodic reports highlighting significant changes in stablecoin supply, helping track market movements and potential de-pegging events.

## Features

- Monitors supply changes for FRAX, DAI, EURC, and ESDe stablecoins
- Generates detailed reports every 2 hours
- Tracks supply changes, current supply levels, and token prices
- Saves historical reports with timestamps
- Handles missing data through forward-filling
- Configurable thresholds for significant changes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stablecoin-supply-shift.git
cd stablecoin-supply-shift
```

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running a Single Report

To generate a one-time report:

```bash
python3 supply_report.py
```

This will:
- Analyze the current data
- Print the report to console
- Save the report to the `reports` directory

### Automated Monitoring

To set up automated monitoring (on Unix-like systems):

1. Open your crontab:
```bash
crontab -e
```

2. Add the following line to run every 2 hours:
```
0 */2 * * * cd /path/to/stablecoin-supply-shift && /path/to/venv/bin/python3 supply_report.py
```

## Data Format

The tool expects data in CSV format with the following columns:
- timestamp: Datetime of the observation
- frax_supply: Total FRAX supply
- frax_price: Current FRAX price
- frax_supply_change: Percentage change in FRAX supply
- dai_supply: Total DAI supply
- dai_price: Current DAI price
- dai_supply_change: Percentage change in DAI supply
- eurc_supply: Total EURC supply
- eurc_price: Current EURC price in USD
- eurc_supply_change: Percentage change in EURC supply
- esde_supply: Total ESDe supply
- esde_price: Current ESDe price
- esde_supply_change: Percentage change in ESDe supply

## Configuration

Key parameters can be adjusted in `supply_report.py`:
- `window_hours`: Time window for grouping changes (default: 2)
- Change threshold: Minimum change percentage to report (default: 0.0001%)

## Output Example

```
Stablecoin Supply Change Report
==================================================
Time: 2025-04-03 03:39:47
Token: FRAX
Supply Change: -0.1434%
Current Supply: 348,156,596.48
Token Price: $0.9994
------------------------------
```

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy
- python-dateutil >= 2.8.2

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Velocity Tracker Module

The Velocity Tracker module monitors transaction patterns for FRAX and DAI stablecoins, providing insights into:
- Daily transaction counts
- Unique wallet activity
- Token velocity ratios (transaction volume relative to total supply)
- Visualization of velocity trends

### Running the Velocity Tracker

To generate a velocity report:

```bash
python3 src/velocity_tracker.py
```

This will:
- Track transactions over the past 24 hours
- Generate an HTML report with interactive charts
- Save daily velocity data in CSV format
- Create a JSON summary of key metrics

### Velocity Metrics

The tracker monitors several key metrics:
- Transaction count: Total number of transfers
- Unique wallets: Number of distinct addresses involved
- Volume: Total amount of tokens transferred
- Velocity ratio: Transaction volume relative to token supply

### Environment Setup

1. Copy `.env.example` to `.env`
2. Add your Ethereum node URL (Infura/Alchemy)

### Output Files

- `data/velocity_data.csv`: Historical velocity metrics
- `reports/velocity_report_YYYY-MM-DD.html`: Daily interactive charts
- `reports/velocity_summary_YYYY-MM-DD.json`: Daily metrics summary 