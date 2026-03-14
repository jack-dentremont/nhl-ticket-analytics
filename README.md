# NHL Arena Event & Ticket Pricing Analytics

A data analytics project that generates and analyzes event data across five comparable NHL arena markets. The analysis focuses on pricing trends, demand patterns, consumer segmentation, and price tier (price code) structures.

**Markets Analyzed** (comparable-size NHL markets):
| Arena | City | Team |
|---|---|---|
| Nationwide Arena | Columbus | Blue Jackets |
| SAP Center | San Jose | Sharks |
| Bridgestone Arena | Nashville | Predators |
| Lenovo Center | Raleigh | Hurricanes |
| Keybank Center | Buffalo | Sabres |

## Key Analyses

### 1. Price Tier Distribution (Price Code Analysis)
Events are bucketed into pricing tiers (Value → Platinum) — simulating how **Archtics**, Ticketmaster's CRM platform, segments inventory. The analysis reveals how tier mix varies across event segments (Sports, Music, Arts & Theatre), directly informing dynamic pricing.

### 2. Genre × Day-of-Week Pricing Heatmap
Identifies which genre/day combinations command premium pricing at Bridgestone Arena.

### 3. Market Comparison — NHL Games
Compares average entry price and price spread across six NHL markets. Wider spreads indicate more aggressive tiered pricing strategies.

### 4. Day-of-Week Demand Patterns
Shows how event scheduling and pricing correlate with day of week at Bridgestone Arena, informing scheduling strategy and promotional pricing windows.

### 5. Monthly Event Mix
Tracks the seasonal composition of events by segment, revealing how arena programming balances NHL schedule constraints with concert and entertainment bookings.

### 6. Price Distribution by Segment
Box plot comparison of entry-level and premium pricing across event segments at Bridgestone Arena.

## Technical Stack

| Tool | Usage |
|---|---|
| **Python** | Data generation, transformation, and analysis |
| **SQLite** | Local data warehouse for structured queries |
| **pandas** | Data manipulation and aggregation |
| **matplotlib** | Visualization |

### Run with Sample Data
```bash
python src/generate_sample_data.py
python src/analyze.py
```
