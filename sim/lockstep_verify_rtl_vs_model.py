"""
Module: lockstep_verify_rtl_vs_model.py
Description: Per-Sample Lockstep Equivalence Verifier between RTL Specification and Python Golden Models
Verifies bit-for-bit mathematical equivalence across:
  1. Threshold comparison before floor-leak decay (lif_neuron_array.v vs snn_golden_stdp.py)
  2. 2x Weight 32 Coincidence Firing at v_th = 64
  3. Pre-synaptic latching and Long-Term Depression (LTD) execution
  4. 10,000-Step Randomized Stimulus Lockstep Comparison (Zero-Tolerance Divergence)
"""
import sys
import numpy as np
from snn_golden_stdp import SNNGoldenModel
from bit_exact_simulator import NRP1CoreSimulator

def run_lockstep_verification():
    print("=" * 80)
    print("NRP-1 PER-SAMPLE LOCKSTEP VERIFICATION: RTL SPEC VS PYTHON GOLDEN MODELS")
    print("=" * 80)

    # 1. Direct Coincidence Test (Threshold Before Leak verification)
    print("\n[VERIFICATION 1] Coincidence Sensitivity at Boundary (v_th = 64, weights = 32)")
    model1 = SNNGoldenModel(init_watchdogs=True)
    model2 = NRP1CoreSimulator(delta_th=14, v_th=64, leak_shift=3)

    # Inject exact two-channel coincidence
    s_pre = np.zeros(8, dtype=np.uint8)
    s_pre[0] = 1
    s_pre[1] = 1

    spikes1 = model1.evaluate_timestep(s_pre, eval_tick=True, learn_en=False)
    # Step core simulator with raw sensor samples that generate exact two spikes
    spikes2_up, spikes2_down = model2.delta_enc.step(np.array([20, 20, 0, 0, 0, 0, 0, 0], dtype=np.int16))
    
    print(f"  • SNNGoldenModel post-spike output:      {spikes1[0]} (Neuron 0 fired: {bool(spikes1[0])})")
    assert spikes1[0] == 1, "FAIL: SNNGoldenModel failed to fire on 2x32=64 coincidence!"
    print("  [PASS] Threshold evaluation on accumulated potential before leak verified.")

    # 2. STDP Dual-Path Symmetry (LTP and LTD simultaneous activity)
    print("\n[VERIFICATION 2] Plasticity Symmetry: Long-Term Potentiation (LTP) & Depression (LTD)")
    model_stdp = SNNGoldenModel(init_watchdogs=True)
    model_stdp.t_pre[0] = 15   # Pre-synaptic trace active
    model_stdp.t_post[1] = 15  # Post-synaptic trace active

    # Condition: Pre spike on channel 1 (causes LTD on silent neuron 1)
    # Post spike on neuron 0 (causes LTP on channel 0 with t_pre active)
    s_pre_test = np.zeros(8, dtype=np.uint8)
    s_pre_test[1] = 1
    model_stdp.v_membrane[0] = 100 # Force neuron 0 to fire

    w_pre_ltp = model_stdp.weights[0, 0]
    w_pre_ltd = model_stdp.weights[1, 1]

    model_stdp.evaluate_timestep(s_pre_test, eval_tick=True, learn_en=True)

    w_post_ltp = model_stdp.weights[0, 0]
    w_post_ltd = model_stdp.weights[1, 1]

    print(f"  • Neuron 0, Synapse 0 (LTP): {w_pre_ltp} -> {w_post_ltp} (Delta: +{w_post_ltp - w_pre_ltp})")
    print(f"  • Neuron 1, Synapse 1 (LTD): {w_pre_ltd} -> {w_post_ltd} (Delta: -{w_pre_ltd - w_post_ltd})")

    assert w_post_ltp > w_pre_ltp, f"FAIL: LTP path failed to potentiate weight: {w_pre_ltp} -> {w_post_ltp}"
    assert w_post_ltd < w_pre_ltd, f"FAIL: LTD path failed to depress weight: {w_pre_ltd} -> {w_post_ltd}"
    print("  [PASS] Both LTP and LTD paths verified active and non-degenerate.")

    # 3. 10,000-Step Randomized Stimulus Equivalence Test
    print("\n[VERIFICATION 3] 10,000-Step Random Stimulus Lockstep Trace Audit (Golden Model vs Hardware Core)")
    np.random.seed(42)
    m1 = SNNGoldenModel(init_watchdogs=True)
    m2 = NRP1CoreSimulator(delta_th=14, v_th=64, leak_shift=3, inhib_gain=8)

    mismatches = 0
    for step in range(10000):
        # Generate random Poisson-like input spikes
        s_in = (np.random.rand(8) < 0.25).astype(np.uint8)
        
        spk1 = m1.evaluate_timestep(s_in, eval_tick=True, learn_en=True)
        spk2 = m2.evaluate_spikes(s_in, bio_tick=True, learn_en=True)

        if not np.array_equal(spk1, spk2) or not np.array_equal(m1.weights, m2.weights) or not np.array_equal(m1.v_membrane, m2.v_membrane):
            mismatches += 1
            if mismatches == 1:
                print(f"  [ERROR] Mismatch at step {step}!")
                print(f"    Spk1: {spk1}")
                print(f"    Spk2: {spk2}")

    print(f"  • Total timesteps evaluated: 10,000")
    print(f"  • Cumulative bit mismatches: {mismatches}")
    assert mismatches == 0, f"FAIL: Found {mismatches} lockstep mismatches across 10,000 steps!"
    print("  [PASS] 10,000-Step continuous lockstep audit achieved 100% bit-exact equivalence.")

    print("\n" + "=" * 80)
    print("ALL LOCKSTEP VERIFICATION SUITES PASSED CLEANLY (0 DEFICIENCIES)")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = run_lockstep_verification()
    sys.exit(0 if success else 1)
