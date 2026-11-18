with open('C:/Users/NEERAJ/Desktop/NRP1_STRATEGIC_BUSINESS_DEFENSE_DOSSIER.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'ablation_study_stdp_vs_threshold.py' in line and 'Nonlinear Habituation' in line:
        new_lines.append(
            '  2. **Nonlinear Habituation & Multi-Detector Ablation Benchmark:** In our rigorous 4-detector benchmark (`sim/ablation_study_stdp_vs_threshold.py`), an industrial electric motor transitioned from 50 Hz cruise (3,000 RPM) to 75 Hz heavy load (4,500 RPM, $2.5\\times$ vibration amplitude surge) followed by a 1.2 kHz bearing defect:\n'
            '     - **Fixed-Threshold Detector ($A > 150$ counts):** FAILED immediately, tripping a false alarm at $t = 1001.0\\ \\text{ms}$ ($1.0\\ \\text{ms}$ into load surge) because amplitude thresholds cannot distinguish legitimate RPM increase from mechanical failure.\n'
            '     - **2nd-Order Butterworth HPF ($f_c = 200\\ \\text{Hz}$) + Energy Detector:** FAILED, tripping a false alarm at $t = 1018.5\\ \\text{ms}$ ($18.5\\ \\text{ms}$ into load surge) because the broadband transient and motor harmonic distortion ($225\\ \\text{Hz}$, $300\\ \\text{Hz}$) blow through the filter passband.\n'
            '     - **Frozen SNN (Static Weights, No STDP):** FAILED, tripping a false alarm at $t = 1002.5\\ \\text{ms}$ ($2.5\\ \\text{ms}$ into load surge) because rigid receptive fields saturate under the increased spike arrival density.\n'
            '     - **Adaptive NRP-1 Core (Online STDP):** PASSED with **0 False Alarms ($0.00\\%$)** across the entire mode shift. Plastic synapses homeostatically entrained ($\\|\\mathbf{W}\\| = 74.62 \\to 136.83$), maintaining sub-threshold balance, and detected the genuine 1.2 kHz bearing defect in **$0.75\\ \\text{ms}$** ($6.75\\ \\text{ms}$ worst-case decimated reflex latch).\n'
        )
    elif '| Total Equivalent Logic Gates' in line:
        new_lines.append('| Total Equivalent Logic Gates      | ~12,400 Gates (~28.4k Std Cls)| ~12,400 Gates (~28.4k Std Cls)|\n')
        new_lines.append('| Digital Sequential Flip-Flops     | 2,114 FFs                     | 2,114 FFs                     |\n')
    else:
        new_lines.append(line)

with open('C:/Users/NEERAJ/Desktop/NRP1_STRATEGIC_BUSINESS_DEFENSE_DOSSIER.md', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('SUCCESSFULLY updated NRP1_STRATEGIC_BUSINESS_DEFENSE_DOSSIER.md line by line.')
