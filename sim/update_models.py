import numpy as np

# Verify exact norm of diverse watchdog weights
W = np.full((8, 32), 32, dtype=np.int16)
W[:, 24:32] = 0
W[2, 24] = 28 # Acc_Z high-frequency transient
W[2, 25] = 24 # Acc_Z resonant band
W[2, 26] = 20 # Acc_Z broad alert
W[5, 27] = 28 # Gyro_Z angular chatter
W[5, 28] = 24 # Gyro_Z resonant band
W[2, 29] = 22 # Acc_Z + Gyro_Z coupled shear
W[5, 29] = 22
W[3, 30] = 18 # Gyro_X + Gyro_Z cross-axis
W[5, 30] = 22
W[0, 31] = 16 # Tri-axial shock
W[2, 31] = 22
W[5, 31] = 18

norm_watchdog = np.linalg.norm(W)
sum_sq = np.sum(W**2)
print(f"Watchdog Matrix: Sum of squares = {sum_sq}, Norm = {norm_watchdog:.4f}")

# Update bit_exact_simulator.py
with open("sim/bit_exact_simulator.py", "r", encoding="utf-8") as f:
    sim_content = f.read()

old_init = '''        self.weights = np.full((n_inputs, n_neurons), 32, dtype=np.int16)
        # Dedicated watchdog neurons 24-31 initialized to defect axes (Acc_Z, Gyro_Z)
        self.weights[:, 24:32] = 0
        self.weights[2, 24:32] = 24
        self.weights[5, 24:32] = 24'''

new_init = '''        self.weights = np.full((n_inputs, n_neurons), 32, dtype=np.int16)
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
        self.weights[5, 31] = 18'''

assert old_init in sim_content, "old_init not found in bit_exact_simulator.py"
sim_content = sim_content.replace(old_init, new_init)

old_reset = '''        self.weights.fill(32)
        self.weights[:, 24:32] = 0
        self.weights[2, 24:32] = 24
        self.weights[5, 24:32] = 24'''

new_reset = '''        self.weights.fill(32)
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
        self.weights[5, 31] = 18'''

assert old_reset in sim_content, "old_reset not found in bit_exact_simulator.py"
sim_content = sim_content.replace(old_reset, new_reset)

# Update early learn_en gating and burst leak
old_learn_gate = "if learn_en and not self.anomaly_latched:"
new_learn_gate = "if learn_en and not self.anomaly_latched and self.burst_cnt < 2:"
sim_content = sim_content.replace(old_learn_gate, new_learn_gate)

old_burst_leak = "elif self.leak_div == 7 and self.burst_cnt > 0 and not self.anomaly_latched:\n                self.burst_cnt -= 1"
new_burst_leak = "elif self.burst_cnt > 0 and not self.anomaly_latched:\n                self.burst_cnt -= 1"
sim_content = sim_content.replace(old_burst_leak, new_burst_leak)

with open("sim/bit_exact_simulator.py", "w", encoding="utf-8") as f:
    f.write(sim_content)
print("Updated bit_exact_simulator.py")

# Update snn_golden_stdp.py
with open("sim/snn_golden_stdp.py", "r", encoding="utf-8") as f:
    golden_content = f.read()

old_g_init = '''        self.weights[:, 24:32] = 0
        self.weights[2, 24:32] = 24
        self.weights[5, 24:32] = 24'''

new_g_init = '''        self.weights[:, 24:32] = 0
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
        self.weights[5, 31] = 18'''

assert old_g_init in golden_content, "old_g_init not found in snn_golden_stdp.py"
golden_content = golden_content.replace(old_g_init, new_g_init)

# Update norm assertions in snn_golden_stdp.py
golden_content = golden_content.replace("453.68", "450.08")
golden_content = golden_content.replace("453.676", "450.076")

with open("sim/snn_golden_stdp.py", "w", encoding="utf-8") as f:
    f.write(golden_content)
print("Updated snn_golden_stdp.py")
