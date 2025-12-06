import sys
import collections
import numpy as np
import os

DURATION_LIMIT = 60.0  # stop analysis exactly at 60s
WINDOW_SIZE = 10.0  # for step


def parse_mahimahi_log(filename, bin_size_ms):
    bin_size_sec = bin_size_ms / 1000.0
    ingress_bits = collections.defaultdict(int)
    capacity_bits = collections.defaultdict(int)
    base_timestamp = None
    first_timestamp = None

    limit_bin = int(DURATION_LIMIT / bin_size_sec)

    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return None, None, None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# base timestamp:"):
                try:
                    base_timestamp = int(line.split(":")[1].strip())
                except ValueError:
                    pass
                continue
            if line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                ts = int(parts[0])
                event_type = parts[1]
                size_bytes = int(parts[2])
            except ValueError:
                continue

            if base_timestamp:
                ts -= base_timestamp
            else:
                if first_timestamp is None:
                    first_timestamp = ts
                ts -= first_timestamp

            if ts < 0:
                continue

            current_time_sec = ts / 1000.0
            if current_time_sec > DURATION_LIMIT:
                continue

            bin_idx = int(ts / bin_size_ms)
            if bin_idx > limit_bin:
                continue

            num_bits = size_bytes * 8

            if event_type == "+":
                ingress_bits[bin_idx] += num_bits
            elif event_type == "#":
                capacity_bits[bin_idx] += num_bits

    times = []
    ingress_mbps = []
    capacity_mbps = []

    for i in range(limit_bin + 1):
        t = i * bin_size_sec
        if t >= DURATION_LIMIT:
            break
        times.append(t)
        ingress_mbps.append(ingress_bits[i] / bin_size_sec / 1e6)
        capacity_mbps.append(capacity_bits[i] / bin_size_sec / 1e6)

    return np.array(times), np.array(ingress_mbps), np.array(capacity_mbps)


def calculate_metrics(times, rates, capacity_rates):
    if len(times) == 0:
        return None

    auc_data = np.trapz(rates, times)
    auc_capacity = np.trapz(capacity_rates, times)
    utilization = (auc_data / auc_capacity * 100) if auc_capacity > 0 else 0.0
    mean_rate = np.mean(rates)
    avg_link_speed = np.mean(capacity_rates)

    num_windows = int(DURATION_LIMIT / WINDOW_SIZE)
    window_rel_jitters = []

    for w in range(num_windows):
        t_start = w * WINDOW_SIZE
        t_end = (w + 1) * WINDOW_SIZE

        mask = (times >= t_start) & (times < t_end)
        if not np.any(mask):
            continue

        w_rates = rates[mask]

        diffs = np.abs(np.diff(w_rates))
        prev_rates = w_rates[:-1]

        valid_mask = prev_rates > 0.001
        if np.sum(valid_mask) > 0:
            w_jitter = np.mean((diffs[valid_mask] / prev_rates[valid_mask]) * 100)
            window_rel_jitters.append(w_jitter)

    avg_windowed_jitter = np.mean(window_rel_jitters) if window_rel_jitters else 0.0

    return {
        "avg_link_speed": avg_link_speed,
        "auc_data": auc_data,
        "auc_capacity": auc_capacity,
        "utilization": utilization,
        "mean_rate": mean_rate,
        "avg_windowed_jitter": avg_windowed_jitter,
    }


def main():
    if len(sys.argv) < 4 or len(sys.argv) % 2 != 0:
        print("bad")
        sys.exit(1)

    bin_size = int(sys.argv[1])
    args = sys.argv[2:]

    label_width = 20

    print(
        f"{'Label':<{label_width}} | {'LinkSpd':<8} | {'Cap(Mb)':<8} | {'Util%':<6} | {'AvgRate':<8} | {'Windowed Jitter (%)':<14}"
    )
    print("-" * (label_width + 65))

    for i in range(0, len(args), 2):
        filename = args[i]
        label = args[i + 1]

        times, ing_mbps, cap_mbps = parse_mahimahi_log(filename, bin_size)
        if times is None:
            continue

        metrics = calculate_metrics(times, ing_mbps, cap_mbps)

        if metrics:
            print(
                f"{label:<{label_width}} | "
                f"{metrics['avg_link_speed']:<8.2f} | "
                f"{metrics['auc_capacity']:<8.2f} | "
                f"{metrics['utilization']:<6.2f} | "
                f"{metrics['mean_rate']:<8.2f} | "
                f"{metrics['avg_windowed_jitter']:<14.4f}"
            )


if __name__ == "__main__":
    main()
