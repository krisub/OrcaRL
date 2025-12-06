import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import re
import sys
import numpy as np

# Usage: python3 plot_ellipses.py [file1] [label1] [file2] [label2] ...
DEBUG = False   # Set to True to enable debug prints

def debug(*args):
    if DEBUG:
        print("[DEBUG]", *args)

def parse_file(filepath):
    throughputs = []
    delays = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        blocks = content.split('------------------------------')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            thr_match = re.search(r"Average throughput:\s+([\d\.]+)\s+Mbits/s", block)
            del_match = re.search(r"95th percentile per-packet queueing delay:\s+([\d\.]+)\s+ms", block)
            
            if thr_match and del_match:
                throughputs.append(float(thr_match.group(1)))
                delays.append(float(del_match.group(1)))
                
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        sys.exit(1)

    return np.array(delays), np.array(throughputs)

# ----------------------------------------------------------------------
# CONFIDENCE ELLIPSE FUNCTION WITH SCALE FACTOR
# ----------------------------------------------------------------------
def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', scale=1.5, **kwargs):
    """
    Draw a confidence ellipse using covariance eigen-decomposition.
    scale: optional factor to make ellipse visually bigger.
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    mean_x = np.mean(x)
    mean_y = np.mean(y)
    cov = np.cov(x, y)
    eigenvals, eigenvecs = np.linalg.eigh(cov)
    order = np.argsort(eigenvals)[::-1]
    eigenvals = eigenvals[order]
    eigenvecs = eigenvecs[:, order]

    width = 2 * n_std * np.sqrt(eigenvals[0]) * scale
    height = 2 * n_std * np.sqrt(eigenvals[1]) * scale
    angle = np.degrees(np.arctan2(eigenvecs[1,0], eigenvecs[0,0]))

    ellipse = Ellipse(
        (mean_x, mean_y), width, height, angle,
        facecolor=facecolor, **kwargs
    )
    ax.add_patch(ellipse)
    return ellipse

# ----------------------------------------------------------------------
# MAIN PLOTTING FUNCTION
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 3 or len(sys.argv) % 2 == 0:
        print("Usage: python3 plot_ellipses.py [file1] [label1] [file2] [label2] ...")
        sys.exit(1)

    args = sys.argv[1:]
    files_labels = [(args[i], args[i+1]) for i in range(0, len(args), 2)]

    fig, ax = plt.subplots(figsize=(10, 7))
    
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    markers = ['o', 's', '^', 'D', 'v', 'P']

    for i, (filepath, label) in enumerate(files_labels):
        delays, throughputs = parse_file(filepath)

        if len(delays) == 0:
            print(f"Warning: No data found in {filepath}")
            continue

        debug(f"\nParsed {len(delays)} points for {label}")
        debug("Delays:", delays)
        debug("Throughputs:", throughputs)

        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        mean_delay = np.mean(delays)
        mean_thr = np.mean(throughputs)

        debug(f"{label}: mean delay={mean_delay:.3f}, mean throughput={mean_thr:.3f}")

        # Plot raw points
        ax.scatter(
            delays, throughputs,
            c=color, s=30, alpha=0.5,
            label=f"{label} raw points" if len(files_labels) > 1 else None
        )

        # Plot mean point
        ax.scatter(
            mean_delay, mean_thr,
            c=color, marker=marker, s=150,
            edgecolors="black", zorder=10,
            label=f"{label} mean"
        )

        # Plot 1-sigma ellipse (scaled for visibility)
        if len(delays) > 1:
            confidence_ellipse(
                delays, throughputs, ax, n_std=1.0,
                edgecolor=color, facecolor=color, alpha=0.25, linewidth=2,
                scale=2.0
            )
        else:
            debug(f"Not enough points to draw ellipse for {label}")

    # Axis labels & formatting
    ax.set_title("Throughput vs. 95th Percentile Latency\nMean + 1σ Covariance Ellipses", fontsize=14)
    ax.set_xlabel("95th Percentile Delay (ms) [Lower is Better]", fontsize=12)
    ax.set_ylabel("Throughput (Mbps) [Higher is Better]", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='best', fontsize=9)

    # Axis padding
    ax.autoscale(enable=True, axis='both', tight=False)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.set_xlim(left=0, right=xlim[1]*1.1)
    ax.set_ylim(bottom=0, top=ylim[1]*1.1)

    output_file = "ellipses_scaled.png"
    plt.savefig(output_file, dpi=300)
    print(f"\nGraph saved to {output_file}")

if __name__ == "__main__":
    main()

