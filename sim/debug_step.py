import sys
sys.path.append('sim')
from bit_exact_simulator import NRP1CoreSimulator
import csv

with open('sim/rtl_trace.csv', 'r') as f:
    rows = list(csv.DictReader(f))

sim = NRP1CoreSimulator()
sim.reset()

for k, row in enumerate(rows[:20]):
    vec = [int(row[col]) for col in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']] + [0, 0]
    sim.evaluate_timestep(vec, bio_tick=True, learn_en=True)
    if k in [4, 5, 12, 13, 14, 15]:
        print('Step ' + str(k+1) + ': weight[0, 0]=' + str(sim.weights[0, 0]) + ' | t_pre[0]=' + str(sim.t_pre[0]) + ' | t_post[0]=' + str(sim.t_post[0]) + ' | rtl_post=' + hex(int(row['s_post'])))
