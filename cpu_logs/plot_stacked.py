import matplotlib.pyplot as plt
import numpy as np


# Order: Baseline Cubic, Baseline Orca, Mod Reward, All Mod, LSTM
labels = [
    'Baseline\nCubic', 
    'Baseline\nOrca', 
    'Modified\nReward', 
    'Mod Reward\n+ MTP + Switch', 
    'Mod Reward\n+ LSTM'
]

# Data from logs
user_space   = [5.80, 6.43, 6.02, 5.67, 8.53]
kernel_space = [3.07, 3.28, 3.43, 3.15, 2.58]

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(10, 7))
width = 0.6  # Width of bars

# Plot User Space (Bottom Layer)
p1 = ax.bar(labels, user_space, width, label='User Space', 
            color='#4c72b0', edgecolor='black')

# Plot Kernel Space (Top Layer)
p2 = ax.bar(labels, kernel_space, width, bottom=user_space, label='Kernel Space', 
            color='#dd8452', edgecolor='black')

ax.set_ylabel('Avg CPU Utilization (% of 1 Core)', fontsize=12, fontweight='bold')
ax.set_title('CPU Overhead Breakdown by Component', fontsize=14)
ax.legend(loc='upper left', fontsize=11)

ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.5)
ax.set_axisbelow(True)


ax.set_ylim(0, 14)

def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        # Don't label tiny bars
        if height < 0.5: continue
        
        # Calculate center position
        x_pos = bar.get_x() + bar.get_width() / 2
        y_pos = bar.get_y() + height / 2
        
        ax.text(x_pos, y_pos, f'{height:.1f}%', 
                ha='center', va='center', color='white', fontsize=10, fontweight='bold')


add_labels(p1)
add_labels(p2)

for i in range(len(labels)):
    total = user_space[i] + kernel_space[i]
    ax.text(i, total + 0.2, f'{total:.2f}%', 
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='black')

plt.tight_layout()
output_file = "cpu_stacked_comparison.png"
plt.savefig(output_file, dpi=300)
print(f"Graph saved to {output_file}")
