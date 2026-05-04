


# %%
''' 
Preliminary control program for modulating the surface temperature
of the eight heaters. Note that one of them are currently disabled due to short on one 
of the thermistors.

Author: Andrew Lehmann




'''


import serial
import time
import csv
import math
from datetime import datetime

############################
# Configuration
############################

PORT = "/dev/cu.usbmodem1301"  # on windows, this may be assigned to COM ports    
BAUD = 9600

NUM_HEATERS = 7
NUM_TEMPS = 9              # 7 heater thermistors + 2 external monitors (mon1, mon2)
COMMAND_INTERVAL = 1.0     # seconds between setpoint updates
LOGFILE = "0.1s_40s.csv"


MAX_SAFE_TEMP = 93.0

############################
# Experiment Generators
############################

def generate_temp_sweep(target_heater, start_temp, end_temp, step, hold_time_s):
    """
    Experiment 1: Power vs. Instability
    Gradually steps up the temperature on a single heater to find the transition height (hc).
    """
    schedule = []
    current_time = 0
    current_temp = start_temp

    while current_temp <= end_temp:
        schedule.append((current_time, current_time + hold_time_s, {target_heater: current_temp}))
        current_time += hold_time_s
        current_temp += step

    return schedule

def generate_spacing_sweep(fixed_heater, sweep_heaters, target_temp, hold_time_s):
    """
    Experiment 2: Multi-Plume Interference
    Keeps Heater 0 on, and sequentially turns on Heater 1, then 2, then 3...
    to test the merging height at different separation distances (r).
    """
    schedule = []
    current_time = 0

    for moving_heater in sweep_heaters:
        active_heaters = {
            fixed_heater: target_temp,
            moving_heater: target_temp
        }
        schedule.append((current_time, current_time + hold_time_s, active_heaters))
        current_time += hold_time_s

    return schedule

def phase_difference(heater1, heater2, target_temp, delay_s, hold_time_s, iterations=1):
    """
    Experiment 3: Fire heater1, then heater2 after delay_s.
    Both run together for the remainder of hold_time_s.
    Repeats for 'iterations' cycles with both heaters off between cycles.
    """
    schedule = []
    current_time = 0

    for _ in range(iterations):
        # Phase A: heater1 only
        schedule.append((current_time, current_time + delay_s, {heater1: target_temp}))
        
        # Phase B: both heaters together for remaining hold time
        schedule.append((current_time + delay_s, current_time + hold_time_s, {
            heater1: target_temp,
            heater2: target_temp
        }))
        
        # Cool-down gap between iterations (equal to hold_time_s)
        current_time += hold_time_s + hold_time_s

    return schedule

############################
# Schedule Setup
############################

# Choose WHICH experiment to run by uncommenting one of these:

# --- Experiment 1: Temp Sweep on Heater 3 (30C to 70C in 5C steps, 60s hold each) ---
# schedule = generate_temp_sweep(target_heater=3, start_temp=30, end_temp=90, step=5, hold_time_s=150)

# --- Experiment 2: Keep Heater 0 at 60C, test spacing by enabling H1..H6 for 90s each ---
#schedule = generate_spacing_sweep(fixed_heater=1, sweep_heaters=[2,3,4,5,6], target_temp=90, hold_time_s=150)


schedule = phase_difference(heater1=1, heater2=2, target_temp=90, delay_s=0.2, hold_time_s=40, iterations=1)

############################
# Serial & Logging Setup
############################

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # Wait for Arduino to reset after serial connect

logfile = open(LOGFILE, "w", newline="")
writer = csv.writer(logfile)
writer.writerow(["timestamp", "T0", "T1", "T2", "T3", "T4", "T5", "T6", "mon1", "mon2", "State"])

############################
# Controller Functions
############################

def set_temp(channel, temp):
    """Send a SET command to the Arduino. Uses CRLF and flushes immediately."""
    cmd = f"SET,{channel},{temp}\r\n"      
    print(f"  >> Sending: {cmd.strip()}")   
    ser.write(cmd.encode())
    ser.flush()                           

def read_line():
    """Read one line from serial. Handles disconnect and garbled bytes gracefully."""
    try:
        return ser.readline().decode().strip()
    except serial.SerialException as e:     #
        print(f"Serial error: {e}")
        return ""
    except UnicodeDecodeError:              # skip garbled bytes silently
        return ""

############################
# Safety
############################

def safety_check(temps):
    for t in temps:
        try:
            val = float(t)
            if val < -10 or val > MAX_SAFE_TEMP:
                return False
        except ValueError:
            return False  # Drop out if thermistor reads garbage/disconnects
    return True

############################
# Main Control Loop
############################

print("APL Automated Controller Started")
print(f"Safety limit: max {MAX_SAFE_TEMP}°C")

start_time = time.time()
last_command = 0
current_phase_index = -1
last_sent_setpoints = {}   

while True:
    line = read_line()

    if line.startswith("DATA"):
        parts = line.split(",")
        temps = parts[1:]
        timestamp = datetime.now().isoformat()

        if len(temps) != NUM_TEMPS:
            print(f"  [WARN] Skipping malformed line (got {len(temps)} temps, expected {NUM_TEMPS}): {line}")
            continue

        heater_temps = temps[:NUM_HEATERS]   
        writer.writerow([timestamp] + temps + [current_phase_index])
        logfile.flush()  # ensure data hits disk even if we crash
        print(f"{timestamp}  temps={temps}  phase={current_phase_index}")

        if not safety_check(heater_temps):
            print("\n!!! THERMAL RUNAWAY OR THERMISTOR DISCONNECT DETECTED !!!")
            print("SAFETY SHUTDOWN ENGAGED.")
            for i in range(NUM_HEATERS):
                if last_sent_setpoints.get(i) != 0:
                    set_temp(i, 0)
            break

    now = time.time()
    elapsed = now - start_time



    if now - last_command > COMMAND_INTERVAL:

        active_phase_found = False

        for idx, entry in enumerate(schedule):
            start, end, target_dict = entry

            if start <= elapsed <= end:
                active_phase_found = True

                if current_phase_index != idx:
                    print(f"\n--- [T={int(elapsed)}s] STARTING PHASE {idx} ---")
                    print(f"--- TARGETS: {target_dict} ---")
                    current_phase_index = idx

                for ch in range(NUM_HEATERS):
                    target = target_dict.get(ch, 0)  # 0 if not in dict (heater off)
                    if last_sent_setpoints.get(ch) != target:
                        set_temp(ch, target)
                        last_sent_setpoints[ch] = target

        if not active_phase_found and elapsed > schedule[-1][1]:
            print("\n--- EXPERIMENT COMPLETE ---")
            for i in range(NUM_HEATERS):
                if last_sent_setpoints.get(i) != 0:
                    set_temp(i, 0)
            break

        last_command = now

    time.sleep(0.01)

logfile.close()
ser.close()
print("Controller shut down cleanly.")
# %%
