import subprocess
import time
import os
import signal
import sys

# Usage: python3 measure_cpu.py [experiment_name] [command_to_run_experiment]
# Example: python3 measure_cpu.py "baseline_cubic" "./2_run_ose.sh mlp_backup_train_dir"

if len(sys.argv) < 3:
    print("Usage: python3 measure_cpu.py [Label] [Command]")
    sys.exit(1)

label = sys.argv[1]
cmd = sys.argv[2]
duration = 60  # Duration of measurement in seconds

print(f"--- Starting Experiment: {label} ---")

# Start the Experiment in the background
# setsid to create a new process group so we can kill everything later
proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)

# Wait a few seconds for processes (Python/C++) to initialize
print("Waiting 5s for warmup...")
time.sleep(5)

# Start pidstat to monitor Python, Orca Server, and Client
# -C: Filter by command name
# -u: Measure CPU
# -G: Filter by process name (catches python, orca-server, client)
# 1: Interval (1 second)
# duration: How many samples
print("Starting CPU measurement...")
pidstat_cmd = f"pidstat -C 'python|orca|client|iperf3' -u 1 {duration} > cpu_{label}.log"
subprocess.run(pidstat_cmd, shell=True)

# Cleanup
print("Experiment finished. Cleaning up...")
os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
time.sleep(2)
# Force kill ensuring nothing remains
subprocess.run("sudo killall -s9 python orca-server-mahimahi client iperf3", shell=True)

# Analyze and Print Results
print(f"\n--- Results for {label} ---")
try:
    with open(f"cpu_{label}.log", 'r') as f:
        lines = f.readlines()
        
    usr_sum = 0.0
    sys_sum = 0.0
    samples = 0
    
    # pidstat output format (roughly):
    # Time   UID   PID    %usr %system  %guest   %wait    %CPU   Command
    
    for line in lines:
        parts = line.split()
        # Skip headers and averages
        if len(parts) < 8 or not parts[0][0].isdigit():
            continue
            
        try:
            # Indices might vary slightly by version, usually %usr is index 3, %sys is index 4
            # We assume standard output. 
            # Note: pidstat usually prints one line per process per interval.
            
            # We sum up ALL usages found in the file to get total "CPU-Seconds" roughly, 
            # then divide by duration to get Avg Core Usage.
            
            # Use negative indices to be safe against time format variations
            # ... %usr %system %guest %wait %CPU Command
            
            p_usr = float(parts[-6])
            p_sys = float(parts[-5])
            
            usr_sum += p_usr
            sys_sum += p_sys
            samples += 1
        except ValueError:
            continue

    # Since pidstat outputs one block per second containing multiple processes:
    # Average CPU Load = (Total Sum of %CPU) / (Duration)
    avg_total_cpu = (usr_sum + sys_sum) / duration
    avg_usr = usr_sum / duration
    avg_sys = sys_sum / duration

    print(f"Average Total CPU Usage: {avg_total_cpu:.2f}% (of one core)")
    print(f"  - User Space (Agent/Server): {avg_usr:.2f}%")
    print(f"  - Kernel Space (TCP Stack):  {avg_sys:.2f}%")
    print(f"Log saved to cpu_{label}.log")

except FileNotFoundError:
    print("Error: Log file not found.")
