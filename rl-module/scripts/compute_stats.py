import re
import sys
import numpy as np

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

def main():
    if len(sys.argv) < 3 or len(sys.argv) % 2 == 0:
        print("Usage: python3 print_stats.py [file1] [label1] [file2] [label2] ...")
        sys.exit(1)

    args = sys.argv[1:]
    files_labels = [(args[i], args[i+1]) for i in range(0, len(args), 2)]

    for filepath, label in files_labels:
        delays, throughputs = parse_file(filepath)

        if len(delays) == 0:
            print(f"Warning: No data found in {filepath}")
            continue

        # Compute statistics
        stats = {
            'delay_min': np.min(delays),
            'delay_max': np.max(delays),
            'delay_mean': np.mean(delays),
            'delay_var': np.var(delays),
            'thr_min': np.min(throughputs),
            'thr_max': np.max(throughputs),
            'thr_mean': np.mean(throughputs),
            'thr_var': np.var(throughputs),
        }

        # Print statistics with variance in scientific notation
        print(f"\nStatistics for {label}:")
        print(f"Delay (ms) -> min: {stats['delay_min']:.3f}, max: {stats['delay_max']:.3f}, "
              f"mean: {stats['delay_mean']:.3f}, variance: {stats['delay_var']:.3e}")
        print(f"Throughput (Mbps) -> min: {stats['thr_min']:.3f}, max: {stats['thr_max']:.3f}, "
              f"mean: {stats['thr_mean']:.3f}, variance: {stats['thr_var']:.3e}")

if __name__ == "__main__":
    main()

