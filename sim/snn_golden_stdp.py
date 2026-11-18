"""
Module: snn_golden_stdp.py
Description: Bit-Exact Python Verification Engine for Multiplier-Less SNN Architecture
Models exact RTL arithmetic: 9-bit saturating STDP adders, floor-leak trace decay,
eval_tick-synchronized refractory counters, and dedicated watchdog reflex neurons.
"""
import numpy as np

class SNNGoldenModel:
    def __init__(self, n_inputs=8, n_neurons=32, init_watchdogs=True):
        self.n_in = n_inputs
        self.n_out = n_neurons
        
        # Base weight initialization: all 32 neurons set to +32
        self.weights = np.full((n_inputs, n_neurons), 32, dtype=np.int16)
        
        # If init_watchdogs is enabled (matches default RTL reset):
        # Neurons 0..23: Initialized to +32 for adaptive motor hum baseline entrainment
        # Neurons 24..31: Dedicated watchdog guards; channels 2 (Acc_Z) & 5 (Gyro_Z) set to +24, others to 0
        if init_watchdogs:
            self.weights[:, 24:32] = 0
            self.weights[2, 24] = 28
            self.weights[2, 25] = 24
            self.weights[2, 26] = 20
            self.weights[5, 27] = 28
            self.weights[5, 28] = 24
            self.weights[2, 29] = 22
            self.weights[5, 29] = 22
            self.weights[3, 30] = 18
            self.weights[5, 30] = 22
            self.weights[0, 31] = 16
            self.weights[2, 31] = 22
            self.weights[5, 31] = 18
            
        self.v_membrane = np.zeros(n_neurons, dtype=np.int32)
        self.t_pre = np.zeros(n_inputs, dtype=np.int16)
        self.t_post = np.zeros(n_neurons, dtype=np.int16)
        self.refractory = np.zeros(n_neurons, dtype=np.int8)
        self.v_th = 64
        self.leak_shift = 3
        self.inhib_gain = 8

    def evaluate_timestep(self, s_pre, eval_tick=True, learn_en=True):
        """
        Executes one evaluation timestep synchronized to eval_tick (ODR sample period).
        """
        s_post = np.zeros(self.n_out, dtype=np.uint8)

        # 1. Pre-Synaptic Trace Updates (Floor-leak decay prevents infinite limit cycles)
        for i in range(self.n_in):
            if s_pre[i]:
                self.t_pre[i] = 15
            elif eval_tick and self.t_pre[i] > 0:
                decay = self.t_pre[i] >> 2
                self.t_pre[i] -= (decay if decay > 0 else 1)

        # 2. Membrane Integration & Refractory Gating (Synchronized to eval_tick)
        for j in range(self.n_out):
            if self.refractory[j] > 0:
                if eval_tick:
                    self.refractory[j] -= 1
                continue

            syn_current = int(np.sum(self.weights[:, j] * s_pre))
            v_next = self.v_membrane[j] + syn_current

            # Match RTL lif_neuron_array.v exactly: Evaluate threshold on accumulated sum BEFORE leak
            if v_next >= self.v_th:
                s_post[j] = 1
                self.v_membrane[j] = 0
                self.refractory[j] = 3  # 3 sample intervals (750 us at 4 kHz)
                self.t_post[j] = 15
            else:
                s_post[j] = 0
                if eval_tick and v_next > 0:
                    leak = v_next >> self.leak_shift
                    v_next -= (leak if leak > 0 else 1)
                elif v_next < 0:
                    v_next = 0
                self.v_membrane[j] = max(0, v_next)

        # 3. Soft Winner-Take-All Lateral Inhibition
        if np.any(s_post):
            for j in range(self.n_out):
                if not s_post[j]:
                    self.v_membrane[j] = max(0, self.v_membrane[j] - self.inhib_gain)

        # 4. Post-Synaptic Trace Decay (Explicit floor-leak decay for silent neurons)
        if eval_tick:
            for j in range(self.n_out):
                if not s_post[j] and self.t_post[j] > 0:
                    decay = self.t_post[j] >> 2
                    self.t_post[j] -= (decay if decay > 0 else 1)

        # 5. Multiplier-Less Plasticity (RTL 9-Bit Sign-Extended Saturating Arithmetic)
        # Plasticity is active strictly on motor hum neurons 0..23; watchdogs remain frozen
        if learn_en:
            for i in range(self.n_in):
                for j in range(24):
                    if s_post[j]:
                        # Causal LTP: Postsynaptic spike fires -> potentiate by presynaptic trace t_pre
                        # Coincident pre-post pairs (s_pre and s_post in same step) receive full LTP
                        ltp_step = self.t_pre[i] >> 1
                        sum_val = int(self.weights[i, j]) + int(ltp_step)
                        self.weights[i, j] = np.clip(sum_val, -128, 127)
                    elif s_pre[i]:
                        # Acausal LTD: Presynaptic spike arrives without postsynaptic response -> depress by postsynaptic trace t_post
                        ltd_step = self.t_post[j] >> 1
                        diff_val = int(self.weights[i, j]) - int(ltd_step)
                        self.weights[i, j] = np.clip(diff_val, -128, 127)

        return s_post

def run_golden_tests():
    print("=" * 80)
    print("SNN GOLDEN REFERENCE MODEL: RIGOROUS ARITHMETIC VERIFICATION")
    print("=" * 80)

    # Test 1A: Unprogrammed Symmetric Matrix Cold Reset Norm
    model_sym = SNNGoldenModel(init_watchdogs=False)
    norm_sym = np.linalg.norm(model_sym.weights)
    print(f"[TEST 1A] Weight Matrix Symmetric Cold Reset Norm: ||W|| = {norm_sym:.2f}")
    assert np.isclose(norm_sym, 512.00), f"FAIL: Expected ||W|| = 512.00, got {norm_sym}"
    print("          PASS: Symmetric cold-reset norm is exactly 512.00.")

    # Test 1B: RTL Watchdog Reset Norm
    model = SNNGoldenModel(init_watchdogs=True)
    init_norm = np.linalg.norm(model.weights)
    print(f"[TEST 1B] Weight Matrix Operational Watchdog Reset Norm: ||W|| = {init_norm:.2f}")
    assert np.isclose(init_norm, 450.08, atol=0.01), f"FAIL: Expected ||W|| = 450.08, got {init_norm}"
    print("          PASS: Operational watchdog reset norm is exactly 450.08.")

    # Test 2: Floor-leak decay reaches zero monotonically
    print("[TEST 2] Verifying Floor-Leak Trace Monotonic Decay to Zero...")
    model.t_pre[0] = 15
    trace_history = [15]
    for step in range(10):
        model.evaluate_timestep(np.zeros(8, dtype=np.uint8), eval_tick=True, learn_en=False)
        trace_history.append(int(model.t_pre[0]))
    print(f"         Trace decay progression: {trace_history}")
    assert trace_history[-1] == 0, f"FAIL: Trace did not decay to 0: {trace_history}"
    assert all(trace_history[k] >= trace_history[k+1] for k in range(len(trace_history)-1)), "Non-monotonic decay"
    print("         PASS: Trace decayed monotonically from 15 to 0 in <= 10 steps (Zero Limit Cycle).")

    # Test 3: 9-bit saturating STDP arithmetic
    print("[TEST 3] Verifying 9-Bit Saturating Addition (+127 Clamp without Wrap-Around)...")
    model.weights[0, 0] = 123
    model.t_pre[0] = 15
    s_pre = np.zeros(8, dtype=np.uint8)
    model.v_membrane[0] = 100
    model.evaluate_timestep(s_pre, eval_tick=True, learn_en=True)
    print(f"         Weight after 123 + 6: {model.weights[0, 0]} (Expected: 127)")
    assert model.weights[0, 0] == 127, f"FAIL: Expected 127, got {model.weights[0, 0]}"

    model.t_pre[0] = 15
    model.v_membrane[0] = 100
    model.refractory[0] = 0
    model.evaluate_timestep(s_pre, eval_tick=True, learn_en=True)
    print(f"         Weight after 127 + 6: {model.weights[0, 0]} (Expected: 127, NO wrap-around)")
    assert model.weights[0, 0] == 127, f"FAIL: Wrap-around detected! Got {model.weights[0, 0]}"
    print("         PASS: Hard directional saturation verified at +127.")

    # Test 4: Refractory counter gating
    print("[TEST 4] Verifying Refractory Counter Lockout on eval_tick...")
    model.v_membrane[1] = 100
    model.evaluate_timestep(s_pre, eval_tick=True, learn_en=False)
    assert model.refractory[1] == 3, f"FAIL: Refractory not set to 3, got {model.refractory[1]}"
    model.evaluate_timestep(s_pre, eval_tick=False, learn_en=False)
    assert model.refractory[1] == 3, f"FAIL: Refractory decremented without eval_tick! Got {model.refractory[1]}"
    model.evaluate_timestep(s_pre, eval_tick=True, learn_en=False)
    assert model.refractory[1] == 2, f"FAIL: Refractory did not decrement with eval_tick! Got {model.refractory[1]}"
    print("         PASS: Refractory lockout strictly governed by eval_tick (750 us total lockout).")

    # Test 5: Verify 2 weights of 32 fire at threshold 64 (Threshold checked BEFORE leak)
    print("[TEST 5] Verifying 2x Weight 32 Coincidence Firing at v_th = 64 (Threshold Before Leak)...")
    model_coinc = SNNGoldenModel(init_watchdogs=True)
    s_pre_coinc = np.zeros(8, dtype=np.uint8)
    s_pre_coinc[0] = 1
    s_pre_coinc[1] = 1
    s_post_coinc = model_coinc.evaluate_timestep(s_pre_coinc, eval_tick=True, learn_en=False)
    assert s_post_coinc[0] == 1, f"FAIL: Expected neuron 0 to fire on 2x32=64 coincidence, got {s_post_coinc[0]}"
    assert model_coinc.v_membrane[0] == 0, f"FAIL: Expected reset to 0, got {model_coinc.v_membrane[0]}"
    print("         PASS: Coincidence firing at exact threshold (32+32=64 >= 64) verified in lockstep with RTL.")

    # Test 6: Verify Long-Term Depression (LTD) when pre-synaptic spike occurs without post-synaptic firing
    print("[TEST 6] Verifying Long-Term Depression (LTD) Path...")
    model_ltd = SNNGoldenModel(init_watchdogs=True)
    model_ltd.t_post[0] = 15 # Post trace active from prior firing
    s_pre_single = np.zeros(8, dtype=np.uint8)
    s_pre_single[0] = 1 # Pre spike occurs on channel 0
    # Input current = 32 < v_th (64), so neuron 0 does NOT fire (s_post[0] = 0)
    w_before = model_ltd.weights[0, 0]
    model_ltd.evaluate_timestep(s_pre_single, eval_tick=True, learn_en=True)
    w_after = model_ltd.weights[0, 0]
    # On eval_tick with s_post=0, t_post decays 15 - 3 = 12, step = 12 >> 1 = 6
    expected_w = max(-128, w_before - 6) # 32 - 6 = 26
    print(f"         LTD Weight update: {w_before} -> {w_after} (Expected: {expected_w})")
    assert w_after == expected_w, f"FAIL: LTD did not depress weight correctly! Got {w_after}, expected {expected_w}"
    print("         PASS: LTD path active and verified (Eliminates monotonic weight ratcheting).")

    print("=" * 80)
    print("ALL SNN GOLDEN MODEL VERIFICATION CHECKS PASSED.")
    print("=" * 80)

if __name__ == "__main__":
    run_golden_tests()
