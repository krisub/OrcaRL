import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import re
import sys
import numpy as np

DEBUG = True

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
# CORRECT CONFIDENCE ELLIPSE (unchanged)
# ----------------------------------------------------------------------
def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    mean_x, mean_y = np.mean(x), np.mean(y)
    cov = np.cov(x, y)

    eigenvals, eigenvecs = np.linalg.eigh(cov)
    order = np.argsort(eigenvals)[::-1]
    eigenvals = eigenvals[order]
    eigenvecs = eigenvecs[:, order]

    width = 2 * n_std * np.sqrt(eigenvals[0])
    height = 2 * n_std * np.sqrt(eigenvals[1])

    angle = np.degrees(np.arctan2(eigenvecs[1, 0], eigenvecs[0, 0]))

    ellipse = Ellipse(
        (mean_x, mean_y),
        width=width,
        height=height,
        angle=angle,
        facecolor=facecolor,
        **kwargs
    )

    ax.add_patch(ellipse)
    return ellipse


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

        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        # Compute means & std for normalization
        delay_mean  = np.mean(delays)
        delay_std   = np.std(delays)
        thr_mean    = np.mean(throughputs)
        thr_std     = np.std(throughputs)

        debug(f"\nParsed {len(delays)} points for {label}")
        debug("Mean delay:", delay_mean, "Std delay:", delay_std)
        debug("Mean thr:", thr_mean, "Std thr:", thr_std)

        # ------------------------------------------------------------------
        # NORMALIZE THE DATA (z-scores)
        # ------------------------------------------------------------------
        z_delay = (delays - delay_mean) / delay_std
        z_throughput = (throughputs - thr_mean) / thr_std

        debug("z-delay:", z_delay)
        debug("z-throughput:", z_throughput)

        # Plot raw normalized points
        ax.scatter(
            z_delay, z_throughput,
            c=color, s=30, alpha=0.5,
            label=f"{label} raw points"
        )

        # Mean is ALWAYS at (0,0) after normalization
        ax.scatter(
            0, 0,
            c=color, marker=marker, s=160,
            edgecolors='black', zorder=10,
            label=f"{label} mean"
        )

        # 1-sigma ellipse in normalized space
        if len(delays) > 1:
            confidence_ellipse(
                z_delay, z_throughput, ax, n_std=1.0,
                edgecolor=color, facecolor=color, alpha=0.25, linewidth=2
            )

    # Axis labels clearly showing normalized units
    ax.set_title("Normalized Covariance Ellipses (1σ) for Delay vs Throughput", fontsize=14)
    ax.set_xlabel("Normalized Delay (z-score)", fontsize=12)
    ax.set_ylabel("Normalized Throughput (z-score)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='best', fontsize=9)

    # Keep normalized scale symmetric
    lim = 3
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    output_file = "ellipse_normalized.png"
    plt.savefig(output_file, dpi=300)
    print(f"\nGraph saved to {output_file}")


if __name__ == "__main__":
    main()

