import glob
import sys

def parse_pidstat_line(line):
    # Split by whitespace
    parts = line.split()
    
    # Time  AM/PM  UID  PID  %usr %system %guest %wait %CPU CPU Command
    try:
        if parts[-1] == "Command": return None # Skip Header
        
        # Valid line check: PID must be an integer
        # parts[-9] or parts[-8] depending on columns. 
        # Easier check: look for the float values near the end.
        
        # 
        # -1: Command (e.g. python)
        # -2: CPU (e.g. 10)
        # -3: %CPU
        # -4: %wait
        # -5: %guest  
        # -6: %system <-- This is Kernel
        # -7: %usr    <-- This is User
        
        p_usr = float(parts[-7])
        p_sys = float(parts[-6])
        
        return p_usr, p_sys
    except (ValueError, IndexError):
        return None

def analyze_file(filename):
    print(f"--- Re-analyzing {filename} ---")
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        usr_sum = 0.0
        sys_sum = 0.0
        count = 0

        DURATION = 60.0 
        
        for line in lines:
            # Skip summary headers added by previous script
            if line.startswith("---") or line.startswith("Average") or line.startswith("Log"):
                continue
                
            data = parse_pidstat_line(line)
            if data:
                usr_sum += data[0]
                sys_sum += data[1]
                count += 1
                
        if count == 0:
            print("No valid data found.")
            return

        # Calculate Averages
        avg_usr = usr_sum / DURATION
        avg_sys = sys_sum / DURATION
        avg_total = avg_usr + avg_sys
        
        print(f"Corrected Averages (over {int(DURATION)}s):")
        print(f"  - Total CPU:   {avg_total:.2f}%")
        print(f"  - User Space:  {avg_usr:.2f}%")
        print(f"  - Kernel Space:{avg_sys:.2f}%")
        print("")
        
    except FileNotFoundError:
        print(f"File {filename} not found.")

def main():
    # Find all cpu_*.log files
    files = glob.glob("cpu_*.log")
    files.sort()
    
    if not files:
        print("No cpu_*.log files found!")
        return

    for fname in files:
        analyze_file(fname)

if __name__ == "__main__":
    main()
