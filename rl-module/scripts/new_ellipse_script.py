import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import numpy as np
import re
import sys

# -------------------------------
# Parsing Input File
# -------------------------------
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


# -------------------------------
# Covariance Ellipse (RAW DATA)
# -------------------------------
def covariance_ellipse_raw(x, y, ax, n_std=1.0, facecolor='none', **kwargs):
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    # Covariance matrix
    cov = np.cov(x, y)

    # Eigenvalues & eigenvectors
    vals, vecs = np.linalg.eigh(cov)

    # Sort in descending order
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]

    # Ellipse orientation (degrees)
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))

    # Ellipse radii (semi-axis lengths)
    width = 2 * n_std * np.sqrt(vals[0])
    height = 2 * n_std * np.sqrt(vals[1])

    # Center at raw mean
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    ell = Ellipse((mean_x, mean_y), width, height,
                  angle=angle, facecolor=facecolor, **kwargs)

    ax.add_patch(ell)
    return ell


# -------------------------------
# Main Plot
# -------------------------------
def main():

    if len(sys.argv) < 3:
        print("Usage: python3 plot_ellipses.py [file1 label1] [file2 label2] ...")
        sys.exit(1)

    args = sys.argv[1:]
    files_labels = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]

    # Baseline (first file)
    base_file, base_label = files_labels[0]
    base_delays_raw, base_thr_raw = parse_file(base_file)

    norm_delay = np.mean(base_delays_raw)
    norm_thr = np.mean(base_thr_raw)

    print(f"Normalizing relative to {base_label}:")
    print(f"  Baseline Delay Mean:      {norm_delay:.2f} ms")
    print(f"  Baseline Throughput Mean: {norm_thr:.2f} Mbps")

    fig, ax = plt.subplots(figsize=(10, 7))

    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    markers = ['o', 's', '^', 'D', 'v']

    for i, (filepath, label) in enumerate(files_labels):

        raw_delays, raw_thr = parse_file(filepath)
        if len(raw_delays) == 0:
            continue

        # -----------------------------
        # Normalized points
        # -----------------------------
        n_delays = raw_delays / norm_delay
        n_thr = raw_thr / norm_thr

        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        # Mean (normalized)
        mean_dx = np.mean(n_delays)
        mean_ty = np.mean(n_thr)

        ax.scatter(mean_dx, mean_ty, s=140, c=color, marker=marker,
                   edgecolors='black', label=label)

        # -----------------------------
        # Draw ellipse in RAW space but transform it into normalized space
        # -----------------------------
        if len(raw_delays) > 1:
            ellipse = covariance_ellipse_raw(raw_delays, raw_thr, ax,
                                             n_std=1.0,
                                             edgecolor=color,
                                             facecolor=color,
                                             alpha=0.20)

            # Transform raw ellipse → normalized space
            transform_norm = transforms.Affine2D().scale(1 / norm_delay, 1 / norm_thr)
            ellipse.set_transform(transform_norm + ax.transData)

    # -----------------------------
    # Plot formatting
    # -----------------------------
    ax.axvline(1.0, linestyle="--", color="gray", alpha=0.5)
    ax.axhline(1.0, linestyle="--", color="gray", alpha=0.5)

    ax.set_xlabel("Normalized Delay (Lower is Better)")
    ax.set_ylabel("Normalized Throughput (Higher is Better)")
    ax.set_title(f"Performance Normalized to {base_label} (1.0 = Baseline)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()

    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.savefig("normalized_ellipse.png", dpi=300)
    print("Saved to normalized_ellipse.png")


if __name__ == "__main__":
    main()

