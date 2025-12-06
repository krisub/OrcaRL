import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import re
import sys
import numpy as np

# Usage: python3 plot_ellipses.py [baseline_file] [baseline_label] [file2] [label2] ...

def parse_file(filepath):
    throughputs = []
    delays = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        blocks = content.split('------------------------------')
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            thr_match = re.search(r"Average throughput:\s+([\d\.]+)\s+Mbits/s", block)
            del_match = re.search(r"95th percentile per-packet queueing delay:\s+([\d\.]+)\s+ms", block)
            
            if thr_match and del_match:
                throughputs.append(float(thr_match.group(1)))
                delays.append(float(del_match.group(1)))
                
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        sys.exit(1)

    return np.array(delays), np.array(throughputs)

def confidence_ellipse(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    if x.size != y.size: raise ValueError("x and y must be same size")
    
    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                      facecolor=facecolor, **kwargs)

    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = transforms.Affine2D().rotate_deg(45).scale(scale_x, scale_y).translate(mean_x, mean_y)
    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 plot_ellipses.py [baseline_file] [baseline_label] [file2] [label2] ...")
        sys.exit(1)

    args = sys.argv[1:]
    files_labels = [(args[i], args[i+1]) for i in range(0, len(args), 2)]

    # 1. Parse Baseline (First File)
    base_file, base_label = files_labels[0]
    base_delays, base_throughputs = parse_file(base_file)
    
    # Calculate Normalization Constants (using Means of Baseline)
    # The paper often normalizes to the *Best* observed value, but using 
    # Baseline Mean is standard for "Speedup/Improvement" graphs.
    # To match Figure 7 exactly, they usually normalize such that 
    # Max Throughput = 1.0 and Min Delay = 1.0.
    
    # Strategy: Normalize by the Baseline's Mean Performance
    norm_delay = np.mean(base_delays)
    norm_thr = np.mean(base_throughputs)
    
    print(f"Normalizing against {base_label}:")
    print(f"  - Base Delay: {norm_delay:.2f} ms")
    print(f"  - Base Throughput: {norm_thr:.2f} Mbps")

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    markers = ['o', 's', '^', 'D', 'v']

    for i, (filepath, label) in enumerate(files_labels):
        raw_delays, raw_thrs = parse_file(filepath)
        if len(raw_delays) == 0: continue

        # ----------------------------------------------------
        # NORMALIZE RELATIVE TO BASELINE
        # ----------------------------------------------------
        # Normalized Delay = (Delay / Base_Delay)
        # Normalized Throughput = (Throughput / Base_Throughput)
        
        # NOTE: The paper's Figure 7/8 uses "Normalized Delay" where 1.0 is the BEST.
        # But standard "Normalized to Baseline" usually implies:
        # > 1.0 Delay means WORSE than baseline
        # > 1.0 Throughput means BETTER than baseline
        
        n_delays = raw_delays / norm_delay
        n_thrs = raw_thrs / norm_thr
        
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        
        # Plot Mean Point
        mean_d = np.mean(n_delays)
        mean_t = np.mean(n_thrs)
        
        ax.scatter(mean_d, mean_t, c=color, label=label, s=150, marker=marker, edgecolors='black', zorder=10)
        
        # Plot Ellipse
        if len(n_delays) > 1:
            confidence_ellipse(n_delays, n_thrs, ax, n_std=1.0, 
                               edgecolor=color, facecolor=color, alpha=0.2)

    # Formatting to match "Normalized" style
    ax.set_title(f"Performance Normalized to {base_label} (1.0 = Baseline)", fontsize=14)
    ax.set_xlabel("Normalized Delay (Lower is Better)", fontsize=12)
    ax.set_ylabel("Normalized Throughput (Higher is Better)", fontsize=12)
    
    # Draw reference lines at 1.0
    ax.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='best', fontsize=10)
    
    # Invert X axis?
    # No, typically "Normalized Delay" of 0.5 means "Half the latency" (Good).
    # Normalized Delay of 2.0 means "Double the latency" (Bad).
    # So standard axis (0 -> Max) works fine.
    
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.savefig("global_normalized_ellipse.png", dpi=300)
    print("Saved normalized_ellipse.png")

if __name__ == "__main__":
    main()
