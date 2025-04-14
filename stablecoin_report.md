# Stablecoin Supply Analysis Report
Generated on: 2025-04-14

## Current Supply Levels
- FRAX: 319.91M (stable)
- DAI: 3.14B (slight fluctuations)
- EURC: 173.05M (stable)
- USDe: 4.99B (gradual decrease)

## Price Stability
All stablecoins have maintained good price stability:
- FRAX: $0.999 ± 0.001
- DAI: $1.000 ± 0.001
- EURC: $1.134 ± 0.002 (Note: EURC is pegged to EUR, not USD)
- USDe: $1.000 (consistent)

## Supply Changes

### USDe
- Starting supply: 4.998B
- Current supply: 4.992B
- Net change: -0.12% over the monitoring period
- Pattern: Small, gradual decreases in supply
- Notable changes:
  - -0.014% at 2025-04-13T21:13
  - -0.020% at 2025-04-13T23:55
  - -0.011% at 2025-04-14T04:01

### Other Stablecoins
- FRAX: Supply has remained stable at 319.91M
- DAI: Shows small fluctuations between 3.13B and 3.16B
- EURC: Very stable at 173.05M

## Velocity Analysis
### USDe
- Transaction Count (24h): ${metrics['USDe']['total_transactions']}
- Unique Wallets (24h avg): ${metrics['USDe']['avg_unique_wallets']:.0f}
- Total Volume (24h): ${metrics['USDe']['total_volume']:,.2f}
- Average Velocity Ratio: ${metrics['USDe']['avg_velocity']:.4f}
- Max Velocity Ratio: ${metrics['USDe']['max_velocity']:.4f}

### FRAX
- Transaction Count (24h): ${metrics['FRAX']['total_transactions']}
- Unique Wallets (24h avg): ${metrics['FRAX']['avg_unique_wallets']:.0f}
- Total Volume (24h): ${metrics['FRAX']['total_volume']:,.2f}
- Average Velocity Ratio: ${metrics['FRAX']['avg_velocity']:.4f}
- Max Velocity Ratio: ${metrics['FRAX']['max_velocity']:.4f}

### DAI
- Transaction Count (24h): ${metrics['DAI']['total_transactions']}
- Unique Wallets (24h avg): ${metrics['DAI']['avg_unique_wallets']:.0f}
- Total Volume (24h): ${metrics['DAI']['total_volume']:,.2f}
- Average Velocity Ratio: ${metrics['DAI']['avg_velocity']:.4f}
- Max Velocity Ratio: ${metrics['DAI']['max_velocity']:.4f}

### EURC
- Transaction Count (24h): ${metrics['EURC']['total_transactions']}
- Unique Wallets (24h avg): ${metrics['EURC']['avg_unique_wallets']:.0f}
- Total Volume (24h): ${metrics['EURC']['total_volume']:,.2f}
- Average Velocity Ratio: ${metrics['EURC']['avg_velocity']:.4f}
- Max Velocity Ratio: ${metrics['EURC']['max_velocity']:.4f}

## Market Dynamics
1. USDe shows a pattern of controlled supply reduction
2. All stablecoins maintain excellent price stability
3. DAI shows the most frequent supply adjustments
4. FRAX and EURC demonstrate high supply stability

## Technical Notes
- Data collection is functioning properly for all stablecoins
- USDe contract (0x4c9EDD5852cd905f086C759E8383e09bff1E68B3) is responding correctly
- All price feeds are stable and reliable

## Recommendations
1. Continue monitoring USDe supply changes to identify patterns
2. Consider adding volume data to better understand market dynamics
3. Implement alerts for sudden supply changes exceeding 0.05% per hour
4. Monitor velocity ratios above 0.8 for potential market stress
5. Track wallet concentration when unique wallet count drops significantly 