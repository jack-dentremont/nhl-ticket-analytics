"""
NHL Arena Event Analytics - Analysis Pipeline
Analyzes simulated Ticketmaster event data for pricing trends, demand patterns,
and consumer behavior insights across comparable NHL markets.

Outputs:
- Console summary statistics
- Visualization PNGs
- CSV exports

Author: Jack d'Entremont
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# Consistent styling
plt.rcParams.update({
    'figure.facecolor': '#FAFAFA',
    'axes.facecolor': '#FAFAFA',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
    'figure.dpi': 150,
})

PREDATORS_GOLD = '#FFB81C'
PREDATORS_NAVY = '#041E42'
ACCENT_COLORS = ['#FFB81C', '#041E42', '#C8102E', '#006847', '#5B6770', '#A2AAAD']

OUTPUT_DIR = "output"


def load_data(db_path="data/events.db"):
    """Load event data from SQLite into pandas DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM events", conn)
    conn.close()
    df['event_date'] = pd.to_datetime(df['event_date'])
    df['month'] = df['event_date'].dt.month
    df['month_name'] = df['event_date'].dt.strftime('%b')
    df['season'] = df['event_date'].apply(
        lambda x: f"{x.year}-{(x.year+1)%100:02d}" if x.month >= 10 else f"{x.year-1}-{x.year%100:02d}"
    )
    df['is_nashville'] = df['venue_city'] == 'Nashville'
    return df


def print_summary(df):
    """Print high-level summary statistics."""
    print("=" * 70)
    print("NHL ARENA EVENT ANALYTICS - SUMMARY")
    print("=" * 70)
    print(f"\nTotal Events: {len(df):,}")
    print(f"Venues: {df['venue_name'].nunique()}")
    print(f"Date Range: {df['event_date'].min().date()} to {df['event_date'].max().date()}")
    print(f"\n{'Venue':<25} {'Events':>8} {'Avg Min $':>10} {'Avg Max $':>10} {'Avg Spread':>12}")
    print("-" * 70)
    for venue in sorted(df['venue_name'].unique()):
        v = df[df['venue_name'] == venue]
        marker = " ◄" if "Bridgestone" in venue else ""
        print(f"{venue:<25} {len(v):>8} {v['min_price'].mean():>10.2f} {v['max_price'].mean():>10.2f} {v['price_spread'].mean():>12.2f}{marker}")

    print(f"\n{'Segment':<25} {'Events':>8} {'Avg Min $':>10} {'Avg Max $':>10}")
    print("-" * 55)
    for seg in df['segment'].value_counts().index:
        s = df[df['segment'] == seg]
        print(f"{seg:<25} {len(s):>8} {s['min_price'].mean():>10.2f} {s['max_price'].mean():>10.2f}")


def plot_price_distribution_by_segment(df):
    """Compare price distributions by event segment across all venues."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Nashville only
    nash = df[df['is_nashville']]
    segments = nash['segment'].value_counts().index
    data_min = [nash[nash['segment'] == s]['min_price'].dropna() for s in segments]
    data_max = [nash[nash['segment'] == s]['max_price'].dropna() for s in segments]

    bp1 = axes[0].boxplot(data_min, labels=segments, patch_artist=True, widths=0.6)
    for i, box in enumerate(bp1['boxes']):
        box.set_facecolor(ACCENT_COLORS[i % len(ACCENT_COLORS)])
        box.set_alpha(0.7)
    axes[0].set_title('Bridgestone Arena - Entry Price by Segment')
    axes[0].set_ylabel('Minimum Ticket Price ($)')
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    bp2 = axes[1].boxplot(data_max, labels=segments, patch_artist=True, widths=0.6)
    for i, box in enumerate(bp2['boxes']):
        box.set_facecolor(ACCENT_COLORS[i % len(ACCENT_COLORS)])
        box.set_alpha(0.7)
    axes[1].set_title('Bridgestone Arena - Premium Price by Segment')
    axes[1].set_ylabel('Maximum Ticket Price ($)')
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/price_distribution_by_segment.png", bbox_inches='tight')
    plt.close()
    print("  ✓ price_distribution_by_segment.png")


def plot_day_of_week_demand(df):
    """Analyze event scheduling patterns by day of week."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Event count by day of week - Nashville
    nash = df[df['is_nashville']]
    dow_counts = nash.groupby('day_of_week').size().reindex(dow_order)
    colors = [PREDATORS_GOLD if d in ('Friday', 'Saturday') else PREDATORS_NAVY for d in dow_order]
    axes[0].bar(range(7), dow_counts.values, color=colors, edgecolor='white', linewidth=0.5)
    axes[0].set_xticks(range(7))
    axes[0].set_xticklabels([d[:3] for d in dow_order])
    axes[0].set_title('Bridgestone Arena - Events by Day of Week')
    axes[0].set_ylabel('Number of Events')

    # Average pricing by day of week
    dow_prices = nash.groupby('day_of_week')['min_price'].mean().reindex(dow_order)
    axes[1].bar(range(7), dow_prices.values, color=colors, edgecolor='white', linewidth=0.5)
    axes[1].set_xticks(range(7))
    axes[1].set_xticklabels([d[:3] for d in dow_order])
    axes[1].set_title('Bridgestone Arena - Avg Entry Price by Day')
    axes[1].set_ylabel('Average Minimum Price ($)')
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/day_of_week_demand.png", bbox_inches='tight')
    plt.close()
    print("  ✓ day_of_week_demand.png")


def plot_market_comparison(df):
    """Compare pricing across comparable NHL markets."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # NHL games only
    nhl = df[df['genre'] == 'Hockey']
    venue_stats = nhl.groupby('venue_city').agg(
        avg_min=('min_price', 'mean'),
        avg_max=('max_price', 'mean'),
        count=('event_id', 'count')
    ).sort_values('avg_min', ascending=True)

    colors = [PREDATORS_GOLD if c == 'Nashville' else PREDATORS_NAVY for c in venue_stats.index]
    axes[0].barh(venue_stats.index, venue_stats['avg_min'], color=colors, edgecolor='white')
    axes[0].set_title('NHL Games - Avg Entry Price by Market')
    axes[0].set_xlabel('Average Minimum Price ($)')
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Price spread comparison (indicates pricing tier depth)
    nhl_spread = nhl.groupby('venue_city')['price_spread'].mean().sort_values()
    colors2 = [PREDATORS_GOLD if c == 'Nashville' else PREDATORS_NAVY for c in nhl_spread.index]
    axes[1].barh(nhl_spread.index, nhl_spread.values, color=colors2, edgecolor='white')
    axes[1].set_title('NHL Games - Avg Price Spread by Market')
    axes[1].set_xlabel('Average Price Spread (Max - Min) ($)')
    axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/market_comparison.png", bbox_inches='tight')
    plt.close()
    print("  ✓ market_comparison.png")


def plot_monthly_event_mix(df):
    """Show event segment mix by month for Nashville."""
    fig, ax = plt.subplots(figsize=(14, 6))
    nash = df[df['is_nashville']]
    month_order = [10, 11, 12, 1, 2, 3, 4]
    month_labels = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']

    segments = nash['segment'].value_counts().index.tolist()
    bottom = np.zeros(len(month_order))

    for i, seg in enumerate(segments):
        seg_data = nash[nash['segment'] == seg]
        counts = [len(seg_data[seg_data['month'] == m]) for m in month_order]
        ax.bar(range(len(month_order)), counts, bottom=bottom,
               label=seg, color=ACCENT_COLORS[i % len(ACCENT_COLORS)],
               edgecolor='white', linewidth=0.5)
        bottom += counts

    ax.set_xticks(range(len(month_order)))
    ax.set_xticklabels(month_labels)
    ax.set_title('Bridgestone Arena - Monthly Event Mix by Segment')
    ax.set_ylabel('Number of Events')
    ax.legend(loc='upper right', framealpha=0.9)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/monthly_event_mix.png", bbox_inches='tight')
    plt.close()
    print("  ✓ monthly_event_mix.png")


def plot_genre_pricing_heatmap(df):
    """Heatmap of average pricing by genre and day of week."""
    fig, ax = plt.subplots(figsize=(12, 7))
    nash = df[df['is_nashville']]
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    pivot = nash.pivot_table(
        values='min_price', index='genre', columns='day_of_week', aggfunc='mean'
    ).reindex(columns=dow_order)

    # Only keep genres with enough data
    pivot = pivot.dropna(thresh=3)

    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(dow_order)))
    ax.set_xticklabels([d[:3] for d in dow_order])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    # Add text annotations
    for i in range(len(pivot.index)):
        for j in range(len(dow_order)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'${val:.0f}', ha='center', va='center',
                        color='white' if val > pivot.values[~np.isnan(pivot.values)].mean() else 'black',
                        fontsize=9, fontweight='bold')

    ax.set_title('Bridgestone Arena - Avg Entry Price: Genre × Day of Week')
    plt.colorbar(im, ax=ax, label='Avg Min Price ($)', shrink=0.8)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/genre_pricing_heatmap.png", bbox_inches='tight')
    plt.close()
    print("  ✓ genre_pricing_heatmap.png")


def plot_price_tier_analysis(df):
    """Analyze price code / tier distribution"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    nash = df[df['is_nashville']]
    # Create price tiers based on min_price (simulating price code buckets)
    bins = [0, 30, 50, 75, 100, 150, 1000]
    labels = ['Value\n(<$30)', 'Standard\n($30-50)', 'Select\n($50-75)',
              'Premium\n($75-100)', 'VIP\n($100-150)', 'Platinum\n($150+)']
    nash = nash.copy()
    nash['price_tier'] = pd.cut(nash['min_price'], bins=bins, labels=labels)

    # Tier distribution
    tier_counts = nash['price_tier'].value_counts().reindex(labels)
    axes[0].bar(range(len(labels)), tier_counts.values,
                color=[PREDATORS_NAVY, '#1a4478', '#2d68ae', PREDATORS_GOLD, '#e6a600', '#cc9200'],
                edgecolor='white')
    axes[0].set_xticks(range(len(labels)))
    axes[0].set_xticklabels(labels, fontsize=9)
    axes[0].set_title('Price Tier Distribution (All Events)')
    axes[0].set_ylabel('Number of Events')

    # Tier distribution by segment
    tier_by_segment = nash.groupby(['segment', 'price_tier']).size().unstack(fill_value=0)
    tier_by_segment = tier_by_segment.reindex(columns=labels)
    tier_by_segment.plot(kind='bar', stacked=True, ax=axes[1],
                         color=[PREDATORS_NAVY, '#1a4478', '#2d68ae', PREDATORS_GOLD, '#e6a600', '#cc9200'],
                         edgecolor='white', linewidth=0.5)
    axes[1].set_title('Price Tier Mix by Event Segment')
    axes[1].set_ylabel('Number of Events')
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)
    axes[1].legend(title='Price Tier', fontsize=8, title_fontsize=9, loc='upper right')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/price_tier_analysis.png", bbox_inches='tight')
    plt.close()
    print("  ✓ price_tier_analysis.png")


def export_csvs(df):
    """Export analysis-ready CSVs"""
    # Full dataset
    df.to_csv(f"{OUTPUT_DIR}/all_events.csv", index=False)

    # Nashville-specific
    nash = df[df['is_nashville']]
    nash.to_csv(f"{OUTPUT_DIR}/nashville_events.csv", index=False)

    # Market comparison summary
    market_summary = df.groupby(['venue_city', 'segment', 'season']).agg(
        event_count=('event_id', 'count'),
        avg_min_price=('min_price', 'mean'),
        avg_max_price=('max_price', 'mean'),
        avg_price_spread=('price_spread', 'mean'),
        median_min_price=('min_price', 'median'),
    ).reset_index()
    market_summary.to_csv(f"{OUTPUT_DIR}/market_comparison_summary.csv", index=False)

    # Day-of-week pricing summary
    dow_summary = nash.groupby(['day_of_week', 'segment']).agg(
        event_count=('event_id', 'count'),
        avg_min_price=('min_price', 'mean'),
        avg_max_price=('max_price', 'mean'),
    ).reset_index()
    dow_summary.to_csv(f"{OUTPUT_DIR}/dow_pricing_summary.csv", index=False)

    print("  ✓ CSVs exported (all_events, nashville_events, market_comparison, dow_pricing)")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    df = load_data()
    print_summary(df)

    print("\nGenerating visualizations...")
    plot_price_distribution_by_segment(df)
    plot_day_of_week_demand(df)
    plot_market_comparison(df)
    plot_monthly_event_mix(df)
    plot_genre_pricing_heatmap(df)
    plot_price_tier_analysis(df)

    print("\nExporting CSVs...")
    export_csvs(df)

    print("\n" + "=" * 70)
    print("Analysis complete! Check the output/ directory for all deliverables.")
    print("=" * 70)

if __name__ == "__main__":
    main()
