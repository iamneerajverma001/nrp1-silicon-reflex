"""
Module: bit_exact_simulator.py
Description: Register-Accurate, Cycle-Accurate Python Hardware Simulator for NRP-1
Models exact two's complement integer arithmetic, bit-shifts, and saturation clipping of RTL.
"""
import numpy as np

class DeltaModulatorHardware:
    def __init__(self, channels=8, width=16, delta_th=14):
        self.channels = channels
        self.width = width
        self.delta_th = delta_th
        self.v_ref = np.zeros(channels, dtype=np.int32)
        self.initialized = False

    def reset(self):
        self.v_ref.fill(0)
        self.initialized = False

    def step(self, sensor_samples):
        """
        sensor_samples: int array of length `channels` with signed 16-bit values.
        Returns: (spikes_up, spikes_down) as uint8 arrays.
        """
        spikes_up = np.zeros(self.channels, dtype=np.uint8)
        spikes_down = np.zeros(self.channels, dtype=np.uint8)

        # Preload DC reference on first sample to eliminate power-up avalanche
        if not self.initialized:
            self.v_ref = np.array(sensor_samples, dtype=np.int32).copy()
            self.initialized = True
            return spikes_up, spikes_down

        for i in range(self.channels):
            x = int(sensor_samples[i])
            diff = x - self.v_ref[i]

            if diff >= self.delta_th:
                spikes_up[i] = 1
                spikes_down[i] = 0
                leak = (x - self.v_ref[i]) >> 4
                self.v_ref[i] = self.v_ref[i] + self.delta_th + leak
            elif -diff >= self.delta_th:
                spikes_up[i] = 0
                spikes_down[i] = 1
                leak = (x - self.v_ref[i]) >> 4
                self.v_ref[i] = self.v_ref[i] - self.delta_th + leak
            else:
                spikes_up[i] = 0
                spikes_down[i] = 0
                leak = (x - self.v_ref[i]) >> 4
                self.v_ref[i] = self.v_ref[i] + leak

            # Clamp v_ref to 16-bit signed range [-32768, 32767]
            self.v_ref[i] = max(-32768, min(32767, self.v_ref[i]))

        return spikes_up, spikes_down


class NRP1CoreSimulator:
    def __init__(self, n_inputs=8, n_neurons=32, v_th=64, leak_shift=3, delta_th=14, inhib_gain=8):
        self.n_in = n_inputs
        self.n_out = n_neurons
        self.v_th = v_th
        self.leak_shift = leak_shift
        self.inhib_gain = inhib_gain

        self.delta_enc = DeltaModulatorHardware(channels=n_inputs, delta_th=delta_th)
        self.weights = np.full((n_inputs, n_neurons), 32, dtype=np.int16)
        # Diverse orthogonal watchdog neurons 24-31 across failure modes (Acc_Z, Gyro_Z, Gyro_X, Acc_X)
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

        self.burst_cnt = 0
        self.leak_div = 0
        self.anomaly_latched = False

    def reset(self):
        self.weights.fill(32)
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
        self.v_membrane.fill(0)
        self.t_pre.fill(0)
        self.t_post.fill(0)
        self.refractory.fill(0)
        self.delta_enc.reset()
        self.burst_cnt = 0
        self.leak_div = 0
        self.anomaly_latched = False

    def evaluate_timestep(self, sensor_samples, bio_tick=True, learn_en=True):
        """
        Executes one complete evaluation cycle matching snn_core_top.v.
        """
        # 1. Delta Modulation
        spikes_up, spikes_down = self.delta_enc.step(sensor_samples)
        s_pre = spikes_up | spikes_down

        # 2. Pre-Synaptic Trace Updates
        for i in range(self.n_in):
            if s_pre[i]:
                self.t_pre[i] = 15
            elif bio_tick:
                decay = self.t_pre[i] >> 2
                self.t_pre[i] -= (decay if decay > 0 else (1 if self.t_pre[i] > 0 else 0))

        # 3. Synaptic Current Accumulation
        s_post = np.zeros(self.n_out, dtype=np.uint8)
        syn_current = np.zeros(self.n_out, dtype=np.int32)

        for j in range(self.n_out):
            for i in range(self.n_in):
                if s_pre[i]:
                    syn_current[j] += self.weights[i, j]

        # 4. Membrane Potential Integration & Firing
        fired_any = False
        for j in range(self.n_out):
            if self.refractory[j] > 0:
                self.refractory[j] -= 1
                s_post[j] = 0
            else:
                v_next = self.v_membrane[j] + syn_current[j]

                # Match RTL lif_neuron_array.v: evaluate threshold on accumulated sum BEFORE leak
                if v_next >= self.v_th:
                    s_post[j] = 1
                    fired_any = True
                    self.v_membrane[j] = 0
                    self.refractory[j] = 3
                else:
                    s_post[j] = 0
                    if bio_tick and v_next > 0:
                        leak = v_next >> self.leak_shift
                        v_next -= (leak if leak > 0 else 1)
                    elif v_next < 0:
                        v_next = 0
                    self.v_membrane[j] = max(0, v_next)

        # 5. Soft Winner-Take-All Lateral Inhibition
        if fired_any:
            for j in range(self.n_out):
                if not s_post[j]:
                    self.v_membrane[j] = max(0, self.v_membrane[j] - self.inhib_gain)

        # 6. Multiplier-Less STDP Weight Updates (evaluated on strobe_post using current registered traces)
        # Plasticity is active during baseline calibration but automatically locks LOW upon anomaly latch
        if learn_en and not self.anomaly_latched and self.burst_cnt < 2:
            for i in range(self.n_in):
                for j in range(24): # Watchdog neurons 24..31 retain calibrated reflex weights
                    if s_post[j]:
                        # Causal LTP: Postsynaptic spike fires -> potentiate by presynaptic trace t_pre
                        # Coincident pre-post pairs receive full LTP
                        ltp_step = self.t_pre[i] >> 1
                        self.weights[i, j] = np.clip(self.weights[i, j] + ltp_step, -128, 127)
                    elif s_pre[i]:
                        # Acausal LTD: Presynaptic spike arrives without postsynaptic response -> depress by postsynaptic trace t_post
                        ltd_step = self.t_post[j] >> 1
                        self.weights[i, j] = np.clip(self.weights[i, j] - ltd_step, -128, 127)

        # 7. Post-Synaptic Trace Updates (executed on strobe_post registered clock edge)
        if bio_tick:
            for j in range(self.n_out):
                if s_post[j]:
                    self.t_post[j] = 15
                elif self.t_post[j] > 0:
                    decay = self.t_post[j] >> 2
                    self.t_post[j] -= (decay if decay > 0 else 1)

        # 8. Anomaly Classifier (Leaky-Bucket Burst Accumulator with Free-Running Prescaler)
        burst_out = self.burst_cnt
        alarm_out = self.anomaly_latched

        if bio_tick:
            # Free-running biological leak prescaler: increments unconditionally every sample step
            self.leak_div = (self.leak_div + 1) & 7
            if np.any(s_post[24:32]):
                if self.burst_cnt >= 3:
                    self.burst_cnt = 4
                    self.anomaly_latched = True
                else:
                    self.burst_cnt += 1
            elif self.burst_cnt > 0 and not self.anomaly_latched:
                self.burst_cnt -= 1

        return {
            "s_pre": s_pre,
            "s_post": s_post,
            "weights": self.weights.copy(),
            "v_membrane": self.v_membrane.copy(),
            "anomaly": alarm_out,
            "burst_cnt": burst_out
        }

    def evaluate_spikes(self, s_pre, bio_tick=True, learn_en=True):
        """
        Direct pre-synaptic spike interface for lockstep verification against SNNGoldenModel.
        """
        # 1. Pre-Synaptic Trace Updates
        for i in range(self.n_in):
            if s_pre[i]:
                self.t_pre[i] = 15
            elif bio_tick:
                decay = self.t_pre[i] >> 2
                self.t_pre[i] -= (decay if decay > 0 else (1 if self.t_pre[i] > 0 else 0))

        # 2. Synaptic Current Accumulation
        s_post = np.zeros(self.n_out, dtype=np.uint8)
        syn_current = np.zeros(self.n_out, dtype=np.int32)
        for j in range(self.n_out):
            for i in range(self.n_in):
                if s_pre[i]:
                    syn_current[j] += self.weights[i, j]

        # 3. Membrane Potential Integration & Firing
        fired_any = False
        for j in range(self.n_out):
            if self.refractory[j] > 0:
                self.refractory[j] -= 1
                s_post[j] = 0
            else:
                v_next = self.v_membrane[j] + syn_current[j]
                if v_next >= self.v_th:
                    s_post[j] = 1
                    fired_any = True
                    self.v_membrane[j] = 0
                    self.refractory[j] = 3
                else:
                    s_post[j] = 0
                    if bio_tick and v_next > 0:
                        leak = v_next >> self.leak_shift
                        v_next -= (leak if leak > 0 else 1)
                    elif v_next < 0:
                        v_next = 0
                    self.v_membrane[j] = max(0, v_next)

        # 4. Soft Winner-Take-All Lateral Inhibition
        if fired_any:
            for j in range(self.n_out):
                if not s_post[j]:
                    self.v_membrane[j] = max(0, self.v_membrane[j] - self.inhib_gain)

        # 5. Post-Synaptic Trace Decay
        if bio_tick:
            for j in range(self.n_out):
                if not s_post[j] and self.t_post[j] > 0:
                    decay = self.t_post[j] >> 2
                    self.t_post[j] -= (decay if decay > 0 else 1)

        # 6. Multiplier-Less STDP Weight Updates (Plasticity restricted to neurons 0..23)
        if learn_en and not self.anomaly_latched and self.burst_cnt < 2:
            for i in range(self.n_in):
                for j in range(24):
                    if s_post[j]:
                        # Causal LTP: Postsynaptic spike fires -> potentiate by presynaptic trace t_pre
                        ltp_step = self.t_pre[i] >> 1
                        self.weights[i, j] = np.clip(self.weights[i, j] + ltp_step, -128, 127)
                    elif s_pre[i]:
                        # Acausal LTD: Presynaptic spike arrives without postsynaptic response -> depress by postsynaptic trace t_post
                        ltd_step = self.t_post[j] >> 1
                        self.weights[i, j] = np.clip(self.weights[i, j] - ltd_step, -128, 127)

        return s_post
