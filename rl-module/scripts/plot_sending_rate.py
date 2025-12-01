import sys
import matplotlib.pyplot as plt
import collections
import numpy as np

# Usage: python3 plot_sending_rate.py [bin_size_ms] [log_file1] [label1] [log_file2] [label2] ...
# Example: python3 plot_sending_rate.py 500 log/down-run1 "Baseline" log/down-run2 "Orca"

def parse_mahimahi_log(filename, bin_size_ms):
    bin_size_sec = bin_size_ms / 1000.0
    
    # Dictionaries to store bits per bin
    ingress_bits = collections.defaultdict(int)
    capacity_bits = collections.defaultdict(int)
    
    base_timestamp = None
    first_timestamp = None
    max_bin = 0

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Check for base timestamp header
                if line.startswith("# base timestamp:"):
                    base_timestamp = int(line.split(":")[1].strip())
                    continue
                
                # Skip other comments
                if line.startswith("#"):
                    continue
                
                parts = line.split()
                if len(parts) < 3:
                    continue
                
                ts = int(parts[0])
                event_type = parts[1]
                size_bytes = int(parts[2])
                
                # Handle timestamp normalization
                if base_timestamp:
                    ts -= base_timestamp
                else:
                    # Fallback if no header: align relative to first packet
                    if first_timestamp is None:
                        first_timestamp = ts
                    ts -= first_timestamp
                
                if ts < 0: continue

                bin_idx = int(ts / bin_size_ms)
                max_bin = max(max_bin, bin_idx)
                
                num_bits = size_bytes * 8
                
                if event_type == '+':
                    ingress_bits[bin_idx] += num_bits
                elif event_type == '#':
                    capacity_bits[bin_idx] += num_bits

    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        sys.exit(1)

    # Convert bins to arrays for plotting
    times = []
    ingress_mbps = []
    capacity_mbps = []
    
    for i in range(max_bin + 1):
        t = i * bin_size_sec
        times.append(t)
        
        # Mbps = (bits in bin) / (seconds in bin) / 1,000,000
        ing = ingress_bits[i] / bin_size_sec / 1e6
        cap = capacity_bits[i] / bin_size_sec / 1e6
        
        ingress_mbps.append(ing)
        capacity_mbps.append(cap)
        
    return times, ingress_mbps, capacity_mbps

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 plot_sending_rate.py [bin_size_ms] [file1] [label1] [file2] [label2] ...")
        sys.exit(1)

    bin_size = int(sys.argv[1])
    args = sys.argv[2:]
    
    files = []
    labels = []
    
    # Parse pairs of (file, label)
    for i in range(0, len(args), 2):
        files.append(args[i])
        labels.append(args[i+1])

    plt.figure(figsize=(12, 6))
    
    # Plot Capacity (Background) using the first file
    # We assume capacity is roughly the same for all runs
    times, _, cap_mbps = parse_mahimahi_log(files[0], bin_size)
    plt.fill_between(times, 0, cap_mbps, color='#e0e0e0', label='Link Capacity')

    # Plot Sending Rate (Ingress) for each file
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    
    for i, (fname, label) in enumerate(zip(files, labels)):
        t, ing_mbps, _ = parse_mahimahi_log(fname, bin_size)
        
        # Use line plot
        color = colors[i % len(colors)]
        plt.plot(t, ing_mbps, label=label, linewidth=2, color=color)

    # Formatting
    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("Sending Rate (Mbps)", fontsize=12)
    plt.title(f"Sending Rate Comparison (Bin Size: {bin_size}ms)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    # upper left, bbox_to_anchor=(0.02,0.98),
    plt.legend(loc='upper right', fontsize=10)
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    
    output_filename = "comparison_sending_rate.png"
    plt.savefig(output_filename, dpi=300)
    print(f"Graph saved to {output_filename}")

if __name__ == "__main__":
    main()

