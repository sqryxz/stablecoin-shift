# Stablecoin Supply Shift Aggregator

A Python-based tool to monitor supply changes in major stablecoins (FRAX and DAI) using public APIs.

## Features

- Real-time monitoring of FRAX and DAI stablecoin supplies
- Calculation of supply changes over time
- Monitoring of FRAX collateralization ratio
- Asynchronous API calls for efficient data fetching
- Detailed logging of supply changes and errors

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd stablecoin-supply-shift
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the monitor:
```bash
python3 src/stablecoin_monitor.py
```

The script will:
- Fetch supply data for FRAX and DAI every 5 minutes
- Calculate and display supply changes
- Show FRAX collateralization ratio
- Log all information to the console

To stop monitoring, press Ctrl+C.

## Output Format

The monitor displays:
- Current supply for each stablecoin
- Percentage change since last check
- FRAX collateralization ratio
- Timestamp for each update

Example output:
```
2024-XX-XX XX:XX:XX - INFO - FRAX Supply: 1,234,567.89
2024-XX-XX XX:XX:XX - INFO - FRAX Collateral Ratio: 85.50%
2024-XX-XX XX:XX:XX - INFO - FRAX Supply Change: +0.25%
2024-XX-XX XX:XX:XX - INFO - DAI Supply: 5,678,901.23
2024-XX-XX XX:XX:XX - INFO - DAI Supply Change: -0.15%
```

## Error Handling

The script includes robust error handling for:
- API connection issues
- Data parsing errors
- Invalid responses

All errors are logged with appropriate error messages.

## Dependencies

- aiohttp: For async HTTP requests
- pandas: For data manipulation
- python-dotenv: For environment variable management
- requests: For HTTP requests 