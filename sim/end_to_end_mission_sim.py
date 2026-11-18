"""
NRP-1 Neuromorphic Reflex Processor: Complete Mission Simulation
===================================================================
Models full physical lifecycle:
  Stage 1: Cold start & 50 Hz healthy motor baseline entrainment (0 - 1500 ms)
  Stage 2: Plasticity freeze & armed normal operation (1500 - 2000 ms)
  Stage 3: High-frequency bearing defect / chatter injection (2000 - 2500 ms)
  Stage 4: Ultra-fast reflex triggering & micro-servo PWM emergency shutoff

Measures:
  - Weight convergence and stability
  - False alarm rate under normal operation
  - Hardware detection latency (fault onset -> PWM trip)
  - Spike counts, neuron firing distribution, and dynamic power dissipation
"""

import os
import sys
import json
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure local module import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bit_exact_simulator import NRP1CoreSimulator

def run_mission_simulation():
    print("=" * 80)
    print("NRP-1 NEUROMORPHIC PROCESSOR: COMPLETE MISSION SIMULATION")
    print("=" * 80)

    # Simulation parameters
    fs = 4000  # IMU sampling frequency = 4 kHz
    dt = 1.0 / fs  # 250 microseconds per sample
    duration = 2.5  # 2.5 seconds total mission duration
    total_steps = int(duration * fs)  # 10,000 timesteps
    time_axis = np.linspace(0, duration, total_steps, endpoint=False)

    print(f"Total Timesteps: {total_steps} (Time: 0.0s to {duration}s at {fs} Hz ODR)")

    # 1. Generate Synthetic IMU Telemetry (8 channels)
    # Realistic ICM-42688 RMS noise: sigma = 3.0 counts (at +/-16g, 2048 LSB/g)
    np.random.seed(42)
    sensor_stream = np.zeros((total_steps, 8), dtype=np.int16)
    f_motor = 50.0

    for i in range(total_steps):
        t = time_axis[i]
        harm1 = 80.0 * np.sin(2.0 * np.pi * f_motor * t)
        harm2 = 25.0 * np.sin(2.0 * np.pi * 2.0 * f_motor * t + 0.4)
        noise = np.random.normal(0, 3.0, 8)

        # Baseline channel mapping
        ch0 = harm1 + harm2 + noise[0]                 # Acc_X
        ch1 = (harm1 * 0.6) - (harm2 * 0.4) + noise[1] # Acc_Y
        ch2 = noise[2]                                 # Acc_Z (low baseline)
        ch3 = 15.0 * np.sin(2.0 * np.pi * f_motor * t + 1.2) + noise[3] # Gyro_X
        ch4 = 10.0 * np.cos(2.0 * np.pi * f_motor * t) + noise[4]        # Gyro_Y
        ch5 = noise[5]                                 # Gyro_Z
        ch6 = 0                                        # Ch6 tied to 0 in RTL snn_core_top.v
        ch7 = 0                                        # Ch7 tied to 0 in RTL snn_core_top.v

        # Fault Injection at t >= 2.0s (Step 8000)
        # Bearing outer race defect: 1.2 kHz resonant ringing + 40 Hz ball pass impacts
        if t >= 2.0:
            t_fault = t - 2.0
            chatter = 140.0 * np.sin(2.0 * np.pi * 1200.0 * t_fault)
            shock_phase = (t_fault % 0.025) / 0.025
            shock = 220.0 * np.exp(-shock_phase * 15.0) if shock_phase < 0.3 else 0.0

            # Severely impact Acc_Z, Gyro_Z, and cross-couple into Acc_X
            ch2 += chatter + shock + np.random.normal(0, 10.0)
            ch5 += chatter * 0.7 + shock * 0.8
            ch0 += shock * 0.3

        sensor_stream[i, :] = np.clip([ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7], -32768, 32767).astype(np.int16)

    # 2. Instantiate Hardware-Exact NRP-1 Core (Matching RTL parameters)
    core = NRP1CoreSimulator(delta_th=14, v_th=64, leak_shift=3, inhib_gain=8)

    # Watchdog neurons 24-31 retain diverse orthogonal receptive fields (Initial Norm = 450.08)
    watchdog_weights = core.weights[:, 24:32].copy()

    # Telemetry logging buffers
    pre_spike_counts = np.zeros(total_steps, dtype=np.int32)
    post_spike_counts = np.zeros(total_steps, dtype=np.int32)
    anomaly_spike_counts = np.zeros(total_steps, dtype=np.int32)
    weight_norm_trace = np.zeros(total_steps, dtype=np.float64)
    burst_cnt_trace = np.zeros(total_steps, dtype=np.int32)
    alarm_trace = np.zeros(total_steps, dtype=np.bool_)
    servo_pwm_us_trace = np.zeros(total_steps, dtype=np.float64)

    # Exact event timestamps
    fault_start_time = 2.000  # seconds
    first_pre_anomaly_spike_time = None
    first_post_anomaly_spike_time = None
    alarm_assert_time = None
    servo_trip_time = None

    print("\n[EXECUTION] Commencing 10,000-step cycle-accurate simulation...")
    t_start_wall = time.time()

    servo_pwm_us = 1500.0  # Neutral 1.5ms pulse

    for i in range(total_steps):
        t = time_axis[i]

        # Stage Control:
        # Stage 1: 0.0s to 1.5s (learn_en = True on baseline channels)
        # Stage 2: 1.5s to 2.0s (learn_en = False, baseline locked)
        # Stage 3: 2.0s to 2.5s (learn_en = False, fault active)
        learn_en = (t < 1.5)

        # Keep watchdog weights locked against baseline noise drift
        core.weights[:, 24:32] = watchdog_weights.copy()

        # Evaluate hardware timestep
        res = core.evaluate_timestep(sensor_stream[i, :], bio_tick=True, learn_en=learn_en)

        s_pre = res["s_pre"]
        s_post = res["s_post"]
        weights = res["weights"]
        anomaly_active = res["anomaly"]
        burst_cnt = res["burst_cnt"]

        # Logging
        pre_spike_counts[i] = np.sum(s_pre)
        post_spike_counts[i] = np.sum(s_post)
        anomaly_spike_counts[i] = np.sum(s_post[24:32])
        weight_norm_trace[i] = np.linalg.norm(weights)
        burst_cnt_trace[i] = burst_cnt
        alarm_trace[i] = anomaly_active

        # Servo reflex controller behavior:
        # Trip from 1500 us (neutral) to 2000 us (emergency shut-off clamp)
        if anomaly_active:
            servo_pwm_us = 2000.0
            if servo_trip_time is None and t >= fault_start_time - 1e-9:
                servo_trip_time = t
        else:
            servo_pwm_us = 1500.0

        servo_pwm_us_trace[i] = servo_pwm_us

        # Timestamp tracking for fault event
        if t >= fault_start_time - 1e-9:
            if np.sum(s_pre[2]) > 0 and first_pre_anomaly_spike_time is None:
                first_pre_anomaly_spike_time = t
            if np.sum(s_post[24:32]) > 0 and first_post_anomaly_spike_time is None:
                first_post_anomaly_spike_time = t
            if anomaly_active and alarm_assert_time is None:
                alarm_assert_time = t

    t_wall_elapsed = time.time() - t_start_wall
    print(f"Simulation completed in {t_wall_elapsed:.3f}s wall-clock time.")

    # 3. Latency & Performance Calculations
    fault_onset_ms = fault_start_time * 1000.0
    pre_spike_lat_ms = (first_pre_anomaly_spike_time * 1000.0 - fault_onset_ms) if first_pre_anomaly_spike_time else None
    post_spike_lat_ms = (first_post_anomaly_spike_time * 1000.0 - fault_onset_ms) if first_post_anomaly_spike_time else None
    alarm_lat_ms = (alarm_assert_time * 1000.0 - fault_onset_ms) if alarm_assert_time else None
    servo_lat_ms = (servo_trip_time * 1000.0 - fault_onset_ms) if servo_trip_time else None

    # False alarm verification (Stage 1 & 2: 0.0s to 2.0s)
    baseline_alarms = np.sum(alarm_trace[:int(2.0*fs)])
    false_alarm_rate = float(baseline_alarms) / (2.0 * fs)

    # Dynamic Power Modeling
    total_spikes = np.sum(pre_spike_counts) + np.sum(post_spike_counts)
    spike_rate_hz = total_spikes / duration
    energy_per_spike_nj = 2.15  # Analytical SkyWater130/iCE40 energy per synaptic event
    core_dynamic_power_mw = (spike_rate_hz * energy_per_spike_nj * 1e-9) * 1e3
    static_power_mw = 0.42  # iCE40UP5K standby power
    total_power_mw = static_power_mw + core_dynamic_power_mw

    print("\n" + "="*80)
    print("MISSION SIMULATION QUANTITATIVE RESULTS")
    print("="*80)
    print(f"1. Baseline Weight Norm Initial:   {weight_norm_trace[0]:.2f}")
    print(f"2. Baseline Weight Norm at Lock:  {weight_norm_trace[int(1.5*fs)]:.2f}")
    print(f"3. False Alarms (0.0s to 2.0s):    {baseline_alarms} (Rate: {false_alarm_rate*100:.2f}%)")
    print(f"4. Fault Onset Timestamp:          {fault_onset_ms:.2f} ms")
    if pre_spike_lat_ms is not None:
        print(f"5. First Sensor Pre-Spike Latency: {pre_spike_lat_ms:.3f} ms ({int(pre_spike_lat_ms/0.25)} sample steps)")
    if post_spike_lat_ms is not None:
        print(f"6. First Anomaly Post-Spike:       {post_spike_lat_ms:.3f} ms ({int(post_spike_lat_ms/0.25)} sample steps)")
    if alarm_lat_ms is not None:
        print(f"7. Anomaly Alarm Assertion Latency:{alarm_lat_ms:.3f} ms ({int(alarm_lat_ms/0.25)} sample steps)")
    if servo_lat_ms is not None:
        print(f"8. Micro-Servo Reflex PWM Trip:    {servo_lat_ms:.3f} ms ({int(servo_lat_ms/0.25)} sample steps)")
    print(f"9. Total Active Silicon Power:     {total_power_mw:.2f} mW (Static: {static_power_mw:.2f} mW, Dynamic: {core_dynamic_power_mw:.2f} mW)")
    print(f"10. Energy per Reflex Actuation:   {energy_per_spike_nj * np.sum(post_spike_counts[int(2.0*fs):]):.2f} nJ")
    print("="*80)

    # 4. Generate High-Resolution Diagnostic Figures
    os.makedirs("output", exist_ok=True)
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    # Panel 1: Raw Sensor Input (Acc_X vs Acc_Z Fault Channel)
    axes[0].plot(time_axis, sensor_stream[:, 0], color='#2b5c8f', label='Channel 0 (Acc_X Baseline)', alpha=0.7, lw=0.9)
    axes[0].plot(time_axis, sensor_stream[:, 2], color='#d9534f', label='Channel 2 (Acc_Z Fault Injection)', lw=1.1)
    axes[0].axvline(1.5, color='#5cb85c', linestyle='--', label='Plasticity Freeze (learn_en=0)')
    axes[0].axvline(2.0, color='#d9534f', linestyle='--', label='Bearing Fault Onset (t=2.0s)')
    axes[0].set_ylabel('Raw Counts')
    axes[0].set_title('NRP-1 Full Mission Trace: 50 Hz Baseline Entrainment -> Armed Reflex -> Bearing Fault Trip', fontsize=12, fontweight='bold')
    axes[0].legend(loc='upper left', fontsize=9)
    axes[0].grid(True, linestyle=':', alpha=0.6)

    # Panel 2: Spiking Dynamics (Pre vs Post)
    axes[1].plot(time_axis, pre_spike_counts, color='#6f42c1', label='Pre-Synaptic Spikes (8 Ch Input)', alpha=0.6, lw=0.8)
    axes[1].plot(time_axis, anomaly_spike_counts, color='#d9534f', label='Anomaly Neurons 24-31 (Post)', lw=1.2)
    axes[1].axvline(1.5, color='#5cb85c', linestyle='--')
    axes[1].axvline(2.0, color='#d9534f', linestyle='--')
    axes[1].set_ylabel('Spike Count / Step')
    axes[1].legend(loc='upper left', fontsize=9)
    axes[1].grid(True, linestyle=':', alpha=0.6)

    # Panel 3: Synaptic Weight Norm
    axes[2].plot(time_axis, weight_norm_trace, color='#0275d8', lw=1.4, label='Synaptic Weight Matrix L2 Norm ||W||')
    axes[2].axvline(1.5, color='#5cb85c', linestyle='--')
    axes[2].axvline(2.0, color='#d9534f', linestyle='--')
    axes[2].set_ylabel('||W|| Magnitude')
    axes[2].legend(loc='upper left', fontsize=9)
    axes[2].grid(True, linestyle=':', alpha=0.6)

    # Panel 4: Anomaly Burst Accumulator
    axes[3].plot(time_axis, burst_cnt_trace, color='#f0ad4e', lw=1.5, label='Anomaly Burst Integrator (Threshold = 4)')
    axes[3].axhline(4, color='#d9534f', linestyle=':', label='Alarm Trigger Threshold')
    axes[3].axvline(1.5, color='#5cb85c', linestyle='--')
    axes[3].axvline(2.0, color='#d9534f', linestyle='--')
    axes[3].set_ylabel('Burst Count')
    axes[3].legend(loc='upper left', fontsize=9)
    axes[3].grid(True, linestyle=':', alpha=0.6)

    # Panel 5: Servo Reflex Actuator PWM Output
    axes[4].plot(time_axis, servo_pwm_us_trace, color='#d9534f', lw=1.8, label='Actuator PWM Pulse (1500us Neutral -> 2000us Emergency Trip)')
    axes[4].axvline(1.5, color='#5cb85c', linestyle='--')
    axes[4].axvline(2.0, color='#d9534f', linestyle='--')
    if servo_trip_time:
        axes[4].scatter([servo_trip_time], [2000.0], color='black', s=60, zorder=5, label=f'Reflex Trip: +{servo_lat_ms:.2f} ms')
    axes[4].set_ylabel('Pulse Width (us)')
    axes[4].set_xlabel('Time (seconds)', fontsize=11)
    axes[4].legend(loc='upper left', fontsize=9)
    axes[4].grid(True, linestyle=':', alpha=0.6)

    plot_path = os.path.join("output", "mission_simulation_waveform.png")
    fig.savefig(plot_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"\n[FIGURE] High-resolution waveform saved to: {plot_path}")

    # Export to Desktop and Brain artifacts directory
    desktop_plot = r"C:\Users\NEERAJ\Desktop\mission_simulation_waveform.png"
    brain_plot = r"C:\Users\NEERAJ\.gemini\antigravity\brain\b19f1ac1-0798-4627-8b60-bfeba507c2b4\mission_simulation_waveform.png"
    import shutil
    try:
        shutil.copyfile(plot_path, desktop_plot)
        print(f"[EXPORT] Waveform copied to Desktop: {desktop_plot}")
    except Exception as e:
        print(f"[WARN] Desktop copy skipped: {e}")
    try:
        shutil.copyfile(plot_path, brain_plot)
        print(f"[EXPORT] Waveform copied to Brain: {brain_plot}")
    except Exception as e:
        print(f"[WARN] Brain copy skipped: {e}")

    # 5. Export JSON Report
    results = {
        "simulation_parameters": {
            "sampling_frequency_hz": fs,
            "sample_period_us": dt * 1e6,
            "total_timesteps": total_steps,
            "mission_duration_seconds": duration
        },
        "timings": {
            "fault_onset_ms": fault_onset_ms,
            "pre_spike_latency_ms": pre_spike_lat_ms,
            "post_spike_latency_ms": post_spike_lat_ms,
            "alarm_assert_latency_ms": alarm_lat_ms,
            "servo_trip_latency_ms": servo_lat_ms
        },
        "reliability": {
            "false_alarms_in_baseline_and_armed": int(baseline_alarms),
            "false_alarm_rate_percent": false_alarm_rate * 100.0
        },
        "power_and_energy": {
            "static_power_mw": static_power_mw,
            "dynamic_power_mw": core_dynamic_power_mw,
            "total_power_mw": total_power_mw,
            "energy_per_synaptic_event_nj": energy_per_spike_nj
        },
        "weights": {
            "initial_l2_norm": float(weight_norm_trace[0]),
            "final_entrained_l2_norm": float(weight_norm_trace[int(1.5*fs)])
        }
    }

    json_path = os.path.join("output", "mission_simulation_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[DATA] Results successfully exported to: {json_path}")

    return results

if __name__ == "__main__":
    run_mission_simulation()
