import pandas as pd
import matplotlib.pyplot as plt
import sys

if len(sys.argv) != 2:
    print("Usage: python visualization.py <path_to_csv>")
    sys.exit(1)
if not sys.argv[1].endswith('.csv'):
    print("Error: The provided file is not a CSV.")
    sys.exit(1)

# Load CSV
try:
    df = pd.read_csv(sys.argv[1])
except FileNotFoundError:
    print(f"Error: The file {sys.argv[1]} was not found.")
    sys.exit(1)
except pd.errors.EmptyDataError:
    print("Error: The CSV file is empty.")
    sys.exit(1)

df.fillna(0, inplace=True)

# Time axis: 1 unit per entry
time = list(range(len(df)))

# Drop Action column if it exists
if 'Action' in df.columns:
    df = df.drop(columns=['Action'])

# Group columns by base name (e.g., 'Swap Volume A' and 'Swap Volume B' -> 'Swap Volume')
from collections import defaultdict

grouped = defaultdict(dict)
for col in df.columns:
    if col.startswith('LP') or col == 'Trade Lot Fraction':
        continue
    if col.endswith(' A'):
        base = col[:-2]
        grouped[base]['A'] = df[col]
    elif col.endswith(' B'):
        base = col[:-2]
        grouped[base]['B'] = df[col]
    else:
        # Not suffixed with A or B — plot as standalone
        grouped[col]['solo'] = df[col]

# Plotting
for base, versions in grouped.items():
    plt.figure(figsize=(10, 5))
    
    if 'A' in versions:
        plt.plot(time, versions['A'], label=f'{base} A', color='blue')
    if 'B' in versions:
        plt.plot(time, versions['B'], label=f'{base} B', color='red')
    if 'solo' in versions:
        if base == 'Slippage':
            # Only plot non-zero points
            for i, (t, val) in enumerate(zip(time, versions['solo'])):
                if val != 0:
                    plt.bar(t, abs(val), label=f"|{base}|" if i == 0 else "", color='green', width=0.8)
            base = '|Slippage|'
        else:
            plt.plot(time, versions['solo'], label=base, color='green')
    
    plt.title(f"{base} vs Time")
    plt.xlabel("Time (unit steps)")
    plt.ylabel(base)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{base}_vs_time.png")


filtered_df = df[df['Trade Lot Fraction'] != 0]
slippage = filtered_df['Slippage'].abs()  # Absolute slippage for visualization
trade_fraction = filtered_df['Trade Lot Fraction']

plt.figure(figsize=(8, 5))
plt.scatter(trade_fraction, slippage, color='teal', alpha=0.7, edgecolors='k')
plt.title("Slippage vs Trade Lot Fraction")
plt.xlabel("Trade Lot Fraction (X_deposit / X_reserve)")
plt.ylabel("Slippage (absolute)")
plt.grid(True)
plt.tight_layout()
plt.savefig("Slippage_vs_TradeLotFraction.png")





lp_columns = ["LP1", "LP2", "LP3", "LP4", "LP5"]

plt.figure(figsize=(10, 5))
colors = ['blue', 'red', 'green', 'orange', 'purple']
for i, col in enumerate(lp_columns):
    plt.plot(time, df[col], label=col, color=colors[i % len(colors)])

plt.title("LP Token Values Over Time")
plt.xlabel("Time (unit steps)")
plt.ylabel("LP Tokens")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("LP_Tokens_vs_time.png")


lp_df = df[lp_columns]
total = lp_df.sum(axis=1).replace(0, 1)  # Avoid division by zero
percent_df = lp_df.div(total, axis=0) * 100

# Transpose for stacked plotting
bottom = [0] * len(percent_df)
plt.figure(figsize=(10, 5))
colors = ['blue', 'red', 'green', 'orange', 'purple']

for i, col in enumerate(lp_columns):
    plt.bar(time, percent_df[col], bottom=bottom, label=col, color=colors[i % len(colors)], width=0.85)
    bottom = [b + p for b, p in zip(bottom, percent_df[col])]

plt.title("LP Token Holdings Percent Over Time")
plt.xlabel("Time (unit steps)")
plt.ylabel("Percent Holding")
plt.ylim(0, 100)
plt.legend()
plt.grid(True, axis='y')
plt.tight_layout()
plt.savefig("LP_Tokens_Distribution.png")