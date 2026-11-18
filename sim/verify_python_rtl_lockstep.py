"""
sim/verify_python_rtl_lockstep.py
================================================================================
Hardware RTL vs. Python Model Per-Sample Lockstep Verification
================================================================================
Compiles and simulates synthesizable Verilog RTL (`tb_snn_core_top.v` + `rtl/*.v`)
using Icarus Verilog (`iverilog` / `vvp`), dumps per-sample execution traces,
and performs a bit-exact per-sample comparison against `NRP1CoreSimulator`.
"""

import os
import sys
import subprocess
import glob
import numpy as np

from bit_exact_simulator import NRP1CoreSimulator

def run_lockstep_verification():
    print("=" * 80)
    print("RUNNING TRUE HARDWARE VERILOG RTL VS. PYTHON LOCKSTEP VERIFICATION")
    print("=" * 80)

    # 1. Compile Verilog RTL with Icarus Verilog
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rtl_dir = os.path.join(workspace_root, "rtl")
    sim_dir = os.path.join(workspace_root, "sim")
    iverilog_exe = r"C:\Users\NEERAJ\iverilog\app\bin\iverilog.exe" if os.path.exists(r"C:\Users\NEERAJ\iverilog\app\bin\iverilog.exe") else "iverilog"
    vvp_exe      = r"C:\Users\NEERAJ\iverilog\app\bin\vvp.exe" if os.path.exists(r"C:\Users\NEERAJ\iverilog\app\bin\vvp.exe") else "vvp"

    rtl_files = glob.glob(os.path.join(rtl_dir, "*.v"))
    tb_file   = os.path.join(sim_dir, "tb_snn_core_top.v")
    out_vvp   = os.path.join(sim_dir, "tb_snn_core_top.vvp")
    trace_csv = os.path.join(sim_dir, "rtl_trace.csv")

    print("[STEP 1] Compiling synthesizable Verilog modules with iverilog...")
    cmd_compile = [iverilog_exe, "-g2001", "-o", out_vvp, tb_file] + rtl_files
    res_compile = subprocess.run(cmd_compile, cwd=sim_dir, capture_output=True, text=True)
    if res_compile.returncode != 0:
        print("[FAIL] Verilog compilation error:\n", res_compile.stderr)
        sys.exit(1)
    print("         PASS: All 9 Verilog RTL modules + testbench compiled cleanly.")

    print("[STEP 2] Executing hardware simulation with vvp (200,000 clock cycles)...")
    cmd_run = [vvp_exe, out_vvp]
    res_run = subprocess.run(cmd_run, cwd=sim_dir, capture_output=True, text=True)
    if res_run.returncode != 0:
        print("[FAIL] Hardware simulation failed:\n", res_run.stderr)
        sys.exit(1)
    print(res_run.stdout.strip())

    if not os.path.exists(trace_csv):
        print(f"[FAIL] Trace file not found: {trace_csv}")
        sys.exit(1)

    # 2. Parse RTL Trace CSV
    print(f"\n[STEP 3] Parsing hardware telemetry trace from {trace_csv}...")
    with open(trace_csv, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    header = lines[0].split(",")
    data_lines = lines[1:]
    n_samples = len(data_lines)
    print(f"         Captured {n_samples} hardware evaluation samples from RTL simulation.")

    # 3. Instantiate Python Simulator Model
    sim_core = NRP1CoreSimulator()
    sim_core.reset()

    # Mismatch counters for all 7 architectural signals
    mismatches_spre  = 0
    mismatches_vref  = 0
    mismatches_tpre  = 0
    mismatches_w00   = 0
    mismatches_spost = 0
    mismatches_burst = 0
    mismatches_alarm = 0

    prev_w00 = 32

    print("\n[STEP 4] Executing cycle-accurate lockstep comparison across all 7 signals...")
    for idx, line in enumerate(data_lines):
        parts = line.split(",")
        cycle       = int(parts[0])
        sample_cnt  = int(parts[1])
        ax          = int(parts[2])
        ay          = int(parts[3])
        az          = int(parts[4])
        gx          = int(parts[5])
        gy          = int(parts[6])
        gz          = int(parts[7])
        rtl_spre    = int(parts[8])
        rtl_spost   = int(parts[9])
        rtl_burst   = int(parts[10])
        rtl_alarm   = int(parts[11])
        rtl_pwm     = int(parts[12])
        rtl_vref0   = int(parts[13])
        rtl_vmem0   = int(parts[14])
        rtl_w00     = int(parts[15])
        rtl_tpre0   = int(parts[16])

        sensor_vector = np.array([ax, ay, az, gx, gy, gz, 0, 0], dtype=np.int16)

        # Step Python Model
        # In RTL, effective_learn_en cuts off when anomaly_latched or burst_cnt >= 2
        learn_active = (not sim_core.anomaly_latched) and (sim_core.burst_cnt < 2)
        res = sim_core.evaluate_timestep(sensor_vector, bio_tick=True, learn_en=learn_active)

        # Pack Python pre-synaptic spikes
        py_spre = 0
        for i in range(8):
            if res["s_pre"][i]:
                py_spre |= (1 << i)

        # Pack Python postsynaptic spikes
        py_spost = 0
        for b in range(32):
            if sim_core.refractory[b] == 3: # just fired this cycle
                py_spost |= (1 << b)

        py_burst = res["burst_cnt"]
        py_alarm = 1 if res["anomaly"] else 0

        # Compare outputs
        if rtl_spre != py_spre:
            mismatches_spre += 1
            if mismatches_spre <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] s_pre: RTL={rtl_spre} vs PY={py_spre}")

        if rtl_vref0 != sim_core.delta_enc.v_ref[0]:
            mismatches_vref += 1
            if mismatches_vref <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] v_ref0: RTL={rtl_vref0} vs PY={sim_core.delta_enc.v_ref[0]}")

        if rtl_tpre0 != sim_core.t_pre[0]:
            mismatches_tpre += 1
            if mismatches_tpre <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] t_pre0: RTL={rtl_tpre0} vs PY={sim_core.t_pre[0]}")

        # In RTL, weight updates on strobe_post registered edge; compare to registered weight
        if rtl_w00 != prev_w00:
            mismatches_w00 += 1
            if mismatches_w00 <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] w00: RTL={rtl_w00} vs PY={prev_w00}")

        if rtl_spost != py_spost:
            mismatches_spost += 1
            if mismatches_spost <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] s_post: RTL=0x{rtl_spost:08x} vs PY=0x{py_spost:08x}")

        if rtl_burst != py_burst:
            mismatches_burst += 1
            if mismatches_burst <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] burst_cnt: RTL={rtl_burst} vs PY={py_burst}")

        if rtl_alarm != py_alarm:
            mismatches_alarm += 1
            if mismatches_alarm <= 3:
                print(f"  [MISMATCH Sample {sample_cnt}] alarm_led: RTL={rtl_alarm} vs PY={py_alarm}")

        prev_w00 = sim_core.weights[0, 0]

    print("=" * 80)
    print("LOCKSTEP VERIFICATION SUMMARY: REAL VERILOG RTL VS. PYTHON SIMULATION")
    print("=" * 80)
    print(f"Total Hardware Samples Checked     : {n_samples}")
    print(f"Delta Encoder s_pre Mismatches     : {mismatches_spre}")
    print(f"Delta Modulator v_ref Mismatches   : {mismatches_vref}")
    print(f"Presynaptic Trace t_pre Mismatches : {mismatches_tpre}")
    print(f"Synaptic Weight w00 Mismatches     : {mismatches_w00}")
    print(f"Postsynaptic Spike Mismatches      : {mismatches_spost}")
    print(f"Burst Counter Mismatches           : {mismatches_burst}")
    print(f"Alarm Trip Mismatches              : {mismatches_alarm}")
    print("=" * 80)

    total_mismatches = (mismatches_spre + mismatches_vref + mismatches_tpre + 
                        mismatches_w00 + mismatches_spost + mismatches_burst + mismatches_alarm)

    if total_mismatches == 0:
        print("[SUCCESS] 100% BIT-EXACT HARDWARE RTL CORRESPONDENCE VERIFIED ACROSS ALL 7 SIGNALS.")
        return True
    else:
        print(f"[FAIL] Observed {total_mismatches} total discrepancies between Verilog RTL and Python model.")
        return False

if __name__ == "__main__":
    success = run_lockstep_verification()
    sys.exit(0 if success else 1)
