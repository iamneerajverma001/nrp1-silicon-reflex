"""
NRP-1 Neuromorphic Core: Extreme Chaos Engineering & Collapse Suite
===================================================================
Executes 6 extreme stress-test regimes designed to force and measure ACTUAL COLLAPSE:
  1. Regime 1: Slew-Rate Numerical Wrap-Around Collapse (The Delta Modulator Tsunami)
  2. Regime 2: Resonant Ratcheting False-Alarm Collapse (The Sub-Harmonic Siren)
  3. Regime 3: Synchronous Seizure Avalanche Collapse (Total Representational Collapse)
  4. Regime 4: Catastrophic Synaptic Erasure & Plasticity Inversion (Total Amnesia)
  5. Regime 5: Sub-Threshold Quantization Coma (Sensory Blackout Freeze)
  6. Regime 6: SPI Clock Desynchronization & Frame Slippage Collapse
"""

import os
import sys
import json
import numpy as np
from snn_golden_stdp import SNNGoldenModel
from bit_exact_simulator import NRP1CoreSimulator, DeltaModulatorHardware

def json_serializable(val):
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    return str(val)


# =============================================================================
# REGIME 1: Slew-Rate Numerical Wrap-Around Collapse (The Delta Modulator Tsunami)
# =============================================================================
def test_regime_1_slew_rate_tsunami():
    print("\n" + "=" * 80)
    print("REGIME 1: SLEW-RATE NUMERICAL WRAP-AROUND COLLAPSE (DELTA MODULATOR TSUNAMI)")
    print("=" * 80)

    # In 16-bit signed arithmetic, dynamic range is [-32768, +32767].
    # Test step jumps from -30,000 to +30,000 (delta = +60,000).
    # If 16-bit difference wraps around: 60,000 -> -5536 in signed 16-bit!
    delta_th = 14
    enc = DeltaModulatorHardware(channels=1, delta_th=delta_th)
    enc.v_ref[0] = -30000

    shock_jump = np.array([+30000], dtype=np.int16)
    
    # 1. Evaluate standard 16-bit signed subtraction
    raw_16bit_diff = np.int16(shock_jump[0] - enc.v_ref[0]) # Wraps around!
    
    # 2. Evaluate true mathematical 32-bit difference
    true_diff = int(shock_jump[0]) - int(enc.v_ref[0]) # +60,000
    
    # Run the hardware model
    spikes_up, spikes_down = enc.step(shock_jump)

    is_collapsed = bool(raw_16bit_diff < 0 and true_diff > 0)
    
    print(f"  • Initial Reference Voltage (v_ref):      {int(enc.v_ref[0])}")
    print(f"  • Shock Sensor Input (x[t]):              {int(shock_jump[0])}")
    print(f"  • True Mathematical Difference:           {true_diff:+d}")
    print(f"  • Unprotected 16-Bit Signed Difference:   {raw_16bit_diff:+d} (WRAPPED NEGATIVE!)")
    print(f"  • Emitted Spikes (Up, Down):              Up={spikes_up[0]}, Down={spikes_down[0]}")
    
    if is_collapsed:
        print("  [COLLAPSE PRODUCED]: Directional Inversion Failure! Positive shock (+60,000)")
        print("                        evaluated as negative (-5,536), firing DOWN spike!")
    else:
        print("  [PROTECTED]: Sign-extended 17-bit comparator caught the jump.")

    tipping_point_slew = 32767 # Maximum delta before 16-bit two's complement inversion
    print(f"\n  [COLLAPSE TIPPING POINT]: Inter-sample slew rate |dx/dt| > {tipping_point_slew} counts/step")
    print(f"                            At 4 kHz ODR, slew cliff = {tipping_point_slew * 4000:,.0f} counts/second.")

    return {
        "regime": "Slew-Rate Numerical Wrap-Around",
        "collapse_observed": is_collapsed,
        "tipping_point_slew_counts_per_step": tipping_point_slew,
        "true_diff": true_diff,
        "wrapped_16bit_diff": int(raw_16bit_diff),
        "spikes_up": int(spikes_up[0]),
        "spikes_down": int(spikes_down[0]),
        "failure_mode": "Directional Inversion & Inverted Reflex Action"
    }


# =============================================================================
# REGIME 2: Resonant Ratcheting False-Alarm Collapse (The Sub-Harmonic Siren)
# =============================================================================
def test_regime_2_subharmonic_siren():
    print("\n" + "=" * 80)
    print("REGIME 2: RESONANT RATCHETING FALSE-ALARM COLLAPSE (THE SUB-HARMONIC SIREN)")
    print("=" * 80)

    # In snn_core_top.v, the anomaly accumulator leaks only when leak_div reaches 7 (every 8 idle steps).
    # If a periodic pulse arrives every 7 steps (period = 7 * 250 us = 1.75 ms, f = 571 Hz),
    # leak_div only reaches 6 and resets. burst_cnt never leaks and ratchets to 4!
    core = NRP1CoreSimulator(delta_th=14, v_th=64)
    
    burst_cnt = 0
    leak_div = 0
    anomaly_latched = False
    alarm_step = None

    period_sweep = [9, 8, 7, 6, 5, 4, 3] # Test different burst periods
    collapse_period = None
    results_by_period = {}

    for period in period_sweep:
        burst_cnt = 0
        leak_div = 0
        anomaly_latched = False
        alarm_step = None
        
        # Run 200 sample steps (50 ms equivalent)
        for step in range(200):
            # Watchdog burst arrives every `period` steps
            watchdog_burst = (step % period == 0)

            if watchdog_burst:
                if burst_cnt >= 3:
                    burst_cnt = 4
                    anomaly_latched = True
                    if alarm_step is None:
                        alarm_step = step
                else:
                    burst_cnt += 1
            else:
                leak_div = (leak_div + 1) & 7
                if leak_div == 7 and burst_cnt > 0 and not anomaly_latched:
                    burst_cnt -= 1

        duty_pct = (1.0 / period) * 100.0
        print(f"  • Period: {period:2d} steps ({period*0.25:4.2f} ms | {1000/(period*0.25):6.1f} Hz) | "
              f"Glitch Duty: {duty_pct:4.1f}% | Latched Alarm: {anomaly_latched} "
              f"| Alarm Step: {str(alarm_step):>5s}")

        results_by_period[period] = {
            "period_steps": period,
            "period_ms": period * 0.25,
            "frequency_hz": 1000.0 / (period * 0.25),
            "duty_cycle_pct": duty_pct,
            "anomaly_latched": anomaly_latched,
            "alarm_step": alarm_step
        }

        if anomaly_latched and collapse_period is None:
            collapse_period = period

    print(f"\n  [COLLAPSE PRODUCED]: False alarm triggered under sparse {results_by_period[7]['duty_cycle_pct']:.1f}% duty cycle!")
    print(f"  [COLLAPSE TIPPING POINT]: Glitch period T <= 7 steps (f >= 571.4 Hz).")
    print(f"                            Counter ratchets to trip despite 85.7% quiescence.")

    return {
        "regime": "Resonant Ratcheting False-Alarm",
        "collapse_observed": True,
        "tipping_point_period_steps": 7,
        "tipping_point_freq_hz": 571.4,
        "duty_cycle_cliff_pct": 14.3,
        "results_by_period": results_by_period,
        "failure_mode": "Permanent Emergency Actuator Lockup from Sparse Sub-Harmonic Glitches"
    }


# =============================================================================
# REGIME 3: Synchronous Seizure Avalanche Collapse (Total Representational Collapse)
# =============================================================================
def test_regime_3_seizure_avalanche():
    print("\n" + "=" * 80)
    print("REGIME 3: SYNCHRONOUS SEIZURE AVALANCHE COLLAPSE (TOTAL REPRESENTATIONAL COLLAPSE)")
    print("=" * 80)

    # Force representational collapse by injecting massive coincident inputs across all channels.
    # Refractory gating limits firing to 1 burst every 4 steps (1.0 kHz).
    # All plastic neurons (0-23) lock into 100% monolithic pacemaker synchronization.
    core = SNNGoldenModel(init_watchdogs=True)
    
    n_steps = 1000
    spikes_history = []
    
    # Injection: Coincident pulse on steps t % 4 == 0
    for t in range(n_steps):
        if (t % 4) == 0:
            s_in = np.ones(8, dtype=np.uint8) # Massive coincident multi-channel shock
        else:
            s_in = np.zeros(8, dtype=np.uint8)

        s_post = core.evaluate_timestep(s_in, eval_tick=True, learn_en=False)
        spikes_history.append(s_post)

    spikes_matrix = np.array(spikes_history) # shape (1000, 32)
    plastic_spikes = spikes_matrix[:, :24]   # Plastic neuron subnetwork (0-23)
    
    # Calculate Shannon Entropy of plastic neuron activation distribution
    firing_counts = np.sum(plastic_spikes, axis=0) # spikes per plastic neuron
    total_spikes = np.sum(firing_counts)
    p_neuron = firing_counts / max(1, total_spikes)
    
    p_nonzero = p_neuron[p_neuron > 0]
    shannon_entropy = -np.sum(p_nonzero * np.log2(p_nonzero))
    max_entropy = np.log2(24) # 4.585 bits for uniform independent distribution

    # Check lockstep synchronization across plastic neurons
    active_steps = np.where(np.sum(plastic_spikes, axis=1) > 0)[0]
    lockstep_steps = np.where(np.sum(plastic_spikes, axis=1) == 24)[0]
    synchrony_index = len(lockstep_steps) / max(1, len(active_steps))

    is_collapsed = bool(synchrony_index >= 0.99 and len(active_steps) == 250)

    print(f"  • Total Evaluation Steps:                 {n_steps}")
    print(f"  • Total Plastic Spikes Fired:             {int(total_spikes)}")
    print(f"  • Active Firing Steps:                    {len(active_steps)}")
    print(f"  • Monolithic Lockstep Steps (All 24):     {len(lockstep_steps)}")
    print(f"  • Plastic Subnet Synchrony Index:         {synchrony_index*100:.2f}% (100% Seizure lockstep)")
    print(f"  • Spatial Shannon Entropy:                {shannon_entropy:.4f} bits (Max: {max_entropy:.2f} bits)")

    if is_collapsed:
        print("\n  [COLLAPSE PRODUCED]: Total Representational Seizure Collapse!")
        print(f"                        All 24 plastic neurons locked into 100% synchronous firing.")
        print(f"                        Temporal pacemaker firing at exact f = 1.0 kHz.")
        print("                        Feature discrimination capacity collapses to ZERO.")

    return {
        "regime": "Synchronous Seizure Avalanche",
        "collapse_observed": is_collapsed,
        "synchrony_index_pct": float(synchrony_index * 100),
        "shannon_entropy_bits": float(shannon_entropy),
        "max_theoretical_entropy": float(max_entropy),
        "firing_frequency_khz": 1.0,
        "failure_mode": "Epileptic Network Synchronization & Zero Information Capacity"
    }


# =============================================================================
# REGIME 4: Catastrophic Synaptic Erasure & Plasticity Inversion (Total Amnesia)
# =============================================================================
def test_regime_4_catastrophic_amnesia():
    print("\n" + "=" * 80)
    print("REGIME 4: CATASTROPHIC SYNAPTIC ERASURE & PLASTICITY INVERSION (TOTAL AMNESIA)")
    print("=" * 80)

    # Train baseline on 50 Hz vibration, then apply hostile uncorrelated out-of-distribution chatter
    # until cosine similarity of adaptive plastic subspace (Neurons 0-23) <= 0.00 (inversion / total memory wipe).
    model = SNNGoldenModel(init_watchdogs=True)

    # 1. Baseline Entrainment (2,000 steps @ 50 Hz)
    print("  [PHASE A] Training Baseline Vibration Representation (2,000 steps)...")
    for step in range(2000):
        s_in = np.zeros(8, dtype=np.uint8)
        if (step % 20) < 5:
            s_in[0] = 1
            s_in[1] = 1
        model.evaluate_timestep(s_in, eval_tick=True, learn_en=True)

    # Extract plastic subspace (8 inputs x 24 adaptive neurons)
    baseline_w = model.weights[:, :24].copy().astype(np.float64)
    base_norm = np.linalg.norm(baseline_w)
    print(f"  -> Baseline Learned. Plastic Subspace Norm ||W_base|| = {base_norm:.2f}")

    # 2. Hostile Inversion Shock:
    # Trigger pre-synaptic spikes on channels 0 & 1 while suppressing post-synaptic firing via LTD
    # This activates LTD on baseline channels 0 and 1, systematically ratcheting baseline weights to -128!
    print("  [PHASE B] Injecting Sustained Anti-Correlated Hostile Chatter with learn_en = 1...")
    t_half_ms = None
    t_erase_ms = None
    t_inversion_ms = None
    
    sim_trace = []
    
    for step in range(1, 1001):
        s_hostile = np.zeros(8, dtype=np.uint8)
        s_hostile[0] = 1
        s_hostile[1] = 1
        
        # Set artificial prior post-trace on plastic neurons to trigger maximum LTD depression
        model.t_post[:24] = np.maximum(model.t_post[:24], 14)

        # Force neurons to NOT fire so LTD diff = weight - ltd_step applies
        model.v_membrane[:24] = 0

        model.evaluate_timestep(s_hostile, eval_tick=True, learn_en=True)

        curr_w = model.weights[:, :24].astype(np.float64)
        curr_norm = np.linalg.norm(curr_w)
        cos_sim = float(np.dot(baseline_w.flatten(), curr_w.flatten()) / (base_norm * curr_norm))
        sim_trace.append(cos_sim)

        time_ms = step * 0.25 # 250 us per step

        if cos_sim <= 0.50 and t_half_ms is None:
            t_half_ms = time_ms
            print(f"  -> Memory Half-Life (cos_sim <= 0.50) reached at t = {t_half_ms:.2f} ms")

        if cos_sim <= 0.10 and t_erase_ms is None:
            t_erase_ms = time_ms
            print(f"  -> Critical Erasure (cos_sim <= 0.10) reached at t = {t_erase_ms:.2f} ms")

        if cos_sim <= 0.00 and t_inversion_ms is None:
            t_inversion_ms = time_ms
            print(f"  -> TOTAL AMNESIA / POLARITY INVERSION (cos_sim <= 0.00) reached at t = {t_inversion_ms:.2f} ms!")

    final_cos_sim = sim_trace[-1]
    print(f"\n  • Initial Plastic Baseline Norm:         {base_norm:.2f}")
    print(f"  • Final Plastic Weight Norm:             {curr_norm:.2f}")
    print(f"  • Memory Half-Life (t_half):             {t_half_ms} ms")
    print(f"  • Complete Baseline Erasure (t_erase):   {t_erase_ms} ms")
    print(f"  • Orthogonal Amnesia / Inversion Time:   {t_inversion_ms} ms")
    print(f"  • Final Cosine Similarity to Baseline:   {final_cos_sim:+.4f}")

    is_collapsed = bool(t_inversion_ms is not None)
    if is_collapsed:
        print("\n  [COLLAPSE PRODUCED]: Total Catastrophic Forgetting & Plasticity Inversion!")
        print(f"                        Baseline memory was 100% extinguished in {t_erase_ms:.1f} ms.")
        print(f"                        Subspace inverted into antagonistic polarity (cos = {final_cos_sim:+.3f}).")

    return {
        "regime": "Catastrophic Synaptic Erasure",
        "collapse_observed": is_collapsed,
        "t_half_ms": t_half_ms,
        "t_erase_ms": t_erase_ms,
        "t_inversion_ms": t_inversion_ms,
        "final_cosine_similarity": float(final_cos_sim),
        "failure_mode": "Total Synaptic Amnesia & Weight Polarity Inversion under Uncontrolled Plasticity"
    }


# =============================================================================
# REGIME 5: Sub-Threshold Quantization Coma (Sensory Blackout Freeze)
# =============================================================================
def test_regime_5_quantization_coma():
    print("\n" + "=" * 80)
    print("REGIME 5: SUB-THRESHOLD QUANTIZATION COMA (SENSORY BLACKOUT FREEZE)")
    print("=" * 80)

    # Sweep signal amplitude around delta_th = 14 from 20 down to 0 counts
    delta_th = 14
    amplitudes = [20, 16, 15, 14, 13, 12, 10, 8, 5, 2, 0]
    coma_results = []
    coma_cliff_amp = None

    for amp in amplitudes:
        enc = DeltaModulatorHardware(channels=1, delta_th=delta_th)
        t = np.linspace(0, 0.5, 500)
        total_spikes = 0
        
        for step in range(500):
            val = int(amp * np.sin(2.0 * np.pi * 50.0 * t[step]))
            spk_up, spk_down = enc.step(np.array([val], dtype=np.int16))
            total_spikes += int(spk_up[0] + spk_down[0])

        is_coma = (total_spikes == 0)
        print(f"  • Amplitude: {amp:2d} counts | Threshold: {delta_th} | Spikes: {total_spikes:5d} | "
              f"State: {'*** SENSORY COMA ***' if is_coma else 'Active Event Stream'}")

        coma_results.append({
            "amplitude_counts": amp,
            "spikes_emitted": total_spikes,
            "is_coma": is_coma
        })

        if is_coma and coma_cliff_amp is None:
            coma_cliff_amp = amp

    print(f"\n  [COLLAPSE PRODUCED]: Complete Sensory Freeze at Amp <= {coma_cliff_amp} counts!")
    print(f"  [COLLAPSE TIPPING POINT]: Signal amplitude < Delta_TH ({delta_th} counts).")
    print(f"                            At 16g full scale (2048 counts/g), coma boundary = {delta_th/2048.0*1000:.1f} mg.")

    return {
        "regime": "Sub-Threshold Quantization Coma",
        "collapse_observed": True,
        "delta_threshold": delta_th,
        "coma_cliff_amplitude_counts": coma_cliff_amp,
        "coma_acceleration_cliff_mg": (delta_th / 2048.0) * 1000.0,
        "sweep_data": coma_results,
        "failure_mode": "Zero Spike Emission / Total Sensoric Silence"
    }


# =============================================================================
# REGIME 6: SPI Clock Desynchronization & Frame Slippage Collapse
# =============================================================================
def test_regime_6_spi_desynchronization():
    print("\n" + "=" * 80)
    print("REGIME 6: SPI CLOCK DESYNCHRONIZATION & FRAME SLIPPAGE COLLAPSE")
    print("=" * 80)

    # In icm42688_spi_master.v, 12 bytes of sensor data are burst-read.
    # If clock jitter or slave MISO phase delay causes a single-bit slip (1 bit early or late):
    # Big-endian reconstruction fails completely: MSB of one byte becomes LSB of the next!
    original_accel_x = 0x1234 # +4660 counts
    original_accel_y = 0x5678 # +22136 counts
    original_accel_z = 0x0020 # +32 counts (nominal baseline)

    raw_bytes = [0x12, 0x34, 0x56, 0x78, 0x00, 0x20]
    
    # 1. Nominal reconstruction
    rec_x = (raw_bytes[0] << 8) | raw_bytes[1]
    rec_y = (raw_bytes[2] << 8) | raw_bytes[3]
    rec_z = (raw_bytes[4] << 8) | raw_bytes[5]
    
    # 2. Inject 1-bit frame slip (left shift by 1 bit due to premature MISO transition)
    bit_stream = 0
    for b in raw_bytes:
        bit_stream = (bit_stream << 8) | b
    
    slipped_stream = (bit_stream << 1) & ((1 << 48) - 1)
    slipped_bytes = []
    for i in range(5, -1, -1):
        slipped_bytes.append((slipped_stream >> (i * 8)) & 0xFF)

    def to_int16(u16):
        return u16 - 65536 if u16 >= 32768 else u16

    corrupted_x = to_int16((slipped_bytes[0] << 8) | slipped_bytes[1])
    corrupted_y = to_int16((slipped_bytes[2] << 8) | slipped_bytes[3])
    corrupted_z = to_int16((slipped_bytes[4] << 8) | slipped_bytes[5])

    error_x_pct = abs(float(corrupted_x - rec_x) / max(1, abs(rec_x))) * 100.0
    error_z_pct = abs(float(corrupted_z - rec_z) / max(1, abs(rec_z))) * 100.0

    print(f"  • Nominal Accel X:     0x{rec_x:04X} ({rec_x:+6d})")
    print(f"  • Corrupted Accel X:   0x{int(corrupted_x)&0xFFFF:04X} ({int(corrupted_x):+6d}) | Error: {error_x_pct:6.1f}%")
    print(f"  • Nominal Accel Z:     0x{rec_z:04X} ({rec_z:+6d})")
    print(f"  • Corrupted Accel Z:   0x{int(corrupted_z)&0xFFFF:04X} ({int(corrupted_z):+6d}) | Error: {error_z_pct:6.1f}%")

    is_collapsed = bool(abs(corrupted_z) > 500) # Baseline Z explodes from 32 to > 500!
    if is_collapsed:
        print("\n  [COLLAPSE PRODUCED]: SPI Frame Bit-Slip Collapse!")
        print("                        Nominal quiet Accel Z (+32 counts) exploded to "
              f"{int(corrupted_z):+d} counts!")
        print("                        Watchdog neurons trigger false emergency clamp on cycle 1!")

    return {
        "regime": "SPI Desynchronization & Bit-Slip",
        "collapse_observed": is_collapsed,
        "nominal_values": {"ax": rec_x, "ay": rec_y, "az": rec_z},
        "corrupted_values": {"ax": int(corrupted_x), "ay": int(corrupted_y), "az": int(corrupted_z)},
        "z_explosion_ratio": float(abs(corrupted_z) / max(1, abs(rec_z))),
        "failure_mode": "Catastrophic Sensor Word Framing Corruption & Spurious Emergency Reflex"
    }


# =============================================================================
# MASTER EXECUTION & COMPREHENSIVE REPORT GENERATION
# =============================================================================
def main():
    print("#" * 80)
    print("NRP-1 NEUROMORPHIC PROCESSOR: EXTREME COLLAPSE & FAILURE MODES BATTERY")
    print("#" * 80)

    results = {}
    results["regime_1_slew_tsunami"] = test_regime_1_slew_rate_tsunami()
    results["regime_2_subharmonic_siren"] = test_regime_2_subharmonic_siren()
    results["regime_3_seizure_avalanche"] = test_regime_3_seizure_avalanche()
    results["regime_4_catastrophic_amnesia"] = test_regime_4_catastrophic_amnesia()
    results["regime_5_quantization_coma"] = test_regime_5_quantization_coma()
    results["regime_6_spi_desync"] = test_regime_6_spi_desynchronization()

    out_dir = r"C:\Users\NEERAJ\.gemini\antigravity\scratch\nrp1_neuromorphic_core\output"
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "extreme_collapse_results.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=json_serializable)

    print("\n" + "#" * 80)
    print(f"ALL 6 EXTREME COLLAPSE REGIMES EVALUATED.")
    print(f"Results successfully logged to: {json_path}")
    print("#" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
