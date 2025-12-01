import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import re
import sys
import numpy as np

# Usage: python3 plot_ellipses.py [file1] [label1] [file2] [label2] ...

def parse_file(filepath):
    throughputs = []
    delays = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split by separator
        blocks = content.split('------------------------------')
        
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            # Extract Throughput
            thr_match = re.search(r"Average throughput:\s+([\d\.]+)\s+Mbits/s", block)
            # Extract Delay (Using 95th percentile, 
            # change to 'Average per packet delay' for mean delay)
            del_match = re.search(r"95th percentile per-packet queueing delay:\s+([\d\.]+)\s+ms", block)
            
            if thr_match and del_match:
                throughputs.append(float(thr_match.group(1)))
                delays.append(float(del_match.group(1)))
                
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        sys.exit(1)

    return np.array(delays), np.array(throughputs)

def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    
    # Using a special case to obtain the eigenvalues of this
    # two-dimension dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                      facecolor=facecolor, **kwargs)

    # Calculating the standard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the standard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mean_x, mean_y)

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

def main():
    if len(sys.argv) < 3 or len(sys.argv) % 2 == 0:
        print("Usage: python3 plot_ellipses.py [file1] [label1] [file2] [label2] ...")
        sys.exit(1)

    args = sys.argv[1:]
    files_labels = []
    for i in range(0, len(args), 2):
        files_labels.append((args[i], args[i+1]))

    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Colors and markers for different schemes
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    markers = ['o', 's', '^', 'D', 'v', 'P']

    for i, (filepath, label) in enumerate(files_labels):
        delays, throughputs = parse_file(filepath)
        
        if len(delays) == 0:
            print(f"Warning: No data found in {filepath}")
            continue
            
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        
        # Calculate Means
        mean_delay = np.mean(delays)
        mean_thr = np.mean(throughputs)
        
        # Plot the Mean Point
        ax.scatter(mean_delay, mean_thr, c=color, label=label, s=150, marker=marker, edgecolors='black', zorder=10)
        
        # Draw Ellipse (if we have > 1 point to calculate variance)
        if len(delays) > 1:
            # Draw the ellipse (1 Standard Deviation)
            confidence_ellipse(delays, throughputs, ax, n_std=1.0, 
                               edgecolor=color, facecolor=color, alpha=0.2)
            
            # Uncomment to see the raw runs as individual dots
            # ax.scatter(delays, throughputs, c=color, s=10, alpha=0.3)

    ax.set_title("Throughput vs. 95th % Latency (Mean + 1-SD)", fontsize=14)
    ax.set_xlabel("95th % Delay (ms) [Lower is Better]", fontsize=12)
    ax.set_ylabel("Throughput (Mbps) [Higher is Better]", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right', fontsize=10)
    
    ax.autoscale(enable=True, axis='both', tight=False)
    
    # Force axes to start near 0 if data allows, but don't clip data
    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    ax.set_ylim(bottom=0, top=ylim[1]*1.1)
    ax.set_xlim(left=0, right=xlim[1]*1.1)

    output_file = "ellipse_comparison.png"
    plt.savefig(output_file, dpi=300)
    print(f"Graph saved to {output_file}")

if __name__ == "__main__":
    main()

