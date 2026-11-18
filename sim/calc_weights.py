import numpy as np

W = np.zeros((32, 8), dtype=int)
for out_idx in range(24):
    for in_idx in range(8):
        W[out_idx, in_idx] = 32

# Diverse watchdogs 24-31 across different failure modes and axes
# Acc_Z = channel 2, Gyro_Z = channel 5, Acc_X = 0, Gyro_X = 3
W[24, 2] = 28 # Acc_Z high-frequency transient
W[25, 2] = 24 # Acc_Z resonant band
W[26, 2] = 20 # Acc_Z broad alert
W[27, 5] = 28 # Gyro_Z angular chatter
W[28, 5] = 24 # Gyro_Z resonant band
W[29, 2] = 22 # Acc_Z + Gyro_Z coupled shear
W[29, 5] = 22
W[30, 3] = 18 # Gyro_X + Gyro_Z cross-axis
W[30, 5] = 22
W[31, 0] = 16 # Tri-axial shock
W[31, 2] = 22
W[31, 5] = 18

print('Sum of squares:', np.sum(W**2))
print(f'Norm: {np.linalg.norm(W):.4f}')
