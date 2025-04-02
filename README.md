# Stablecoin Supply Shift Aggregator

A Python-based tool to monitor supply changes in major stablecoins (FRAX and DAI) using public APIs.

## Features

- Monitors FRAX and DAI stablecoin supplies and prices
- Uses CoinGecko API for reliable data retrieval
- Implements rate limiting and error handling
- Saves data to both JSON and CSV formats
- Calculates supply changes over time

## Requirements

- Python 3.x
- Required packages:
  - requests
  - pytz
  - python-dateutil

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stablecoin-supply-shift.git
cd stablecoin-supply-shift
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the monitor script:
```bash
python3 src/stablecoin_monitor.py
```

The script will:
- Fetch current supply and price data for FRAX and DAI
- Calculate supply changes
- Save data to:
  - `data/stablecoin_data.json`
  - `data/stablecoin_data.csv`
- Log updates and next check times

## Data Format

The CSV file contains the following columns:
- timestamp
- FRAX supply
- FRAX price
- FRAX supply change
- DAI supply
- DAI price
- DAI supply change

## Rate Limiting

The script implements rate limiting to comply with API restrictions:
- Minimum 6 seconds between requests
- Automatic retry on rate limit responses (429)
- Maximum 3 retries with 10-second delays

## Error Handling

The script includes robust error handling for:
- API connection issues
- Rate limiting responses
- Invalid data responses
- File I/O operations

## License

MIT License - see LICENSE file for details 