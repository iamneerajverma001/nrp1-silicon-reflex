with open('C:/Users/NEERAJ/Desktop/SUB3MW_ICE40_STDP_PROJECT_BIBLE.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix TOC
old_toc = '''    * [11.4 End-to-End Mission Lifecycle Simulation (Pre-Silicon RTL Verification vs. Physical Target Expectations)](#114-end-to-end-mission-lifecycle-simulation-pre-silicon-rtl-verification-vs-physical-target-expectations)
      * [11.4.1 Four-Stage Mission Lifecycle Protocol](#1141-four-stage-mission-lifecycle-protocol)
      * [11.4.2 Pre-Silicon Simulation Telemetry Results](#1142-pre-silicon-simulation-telemetry-results)
      * [11.4.3 Multi-Panel Diagnostic Waveform Analysis](#1143-multi-panel-diagnostic-waveform-analysis)
      * [11.4.4 What We Expect & Target from Physical Hardware Testing](#1144-what-we-expect--target-from-physical-hardware-testing)
      * [11.4.5 Physical Hardware Acceptance Criteria & Measurement Protocol](#1145-physical-hardware-acceptance-criteria--measurement-protocol)
    * [11.5 STDP Ablation Study: Adaptive Neuromorphic Reflex vs. Fixed-Threshold Baseline (`ablation_study_stdp_vs_threshold.py`)](#115-stdp-ablation-study-adaptive-neuromorphic-reflex-vs-fixed-threshold-baseline-ablation_study_stdp_vs_thresholdpy)'''

new_toc = '''    * [11.4 End-to-End Mission Lifecycle Simulation (Pre-Silicon RTL Verification vs. Physical Target Expectations)](#114-end-to-end-mission-lifecycle-simulation-pre-silicon-rtl-verification-vs-physical-target-expectations)
      * [11.4.1 Four-Stage Mission Lifecycle Protocol](#1141-four-stage-mission-lifecycle-protocol)
      * [11.4.2 Pre-Silicon Simulation Telemetry Results](#1142-pre-silicon-simulation-telemetry-results)
      * [11.4.3 Complete Mission Lifecycle Simulation Script (`sim/end_to_end_mission_sim.py`)](#1143-complete-mission-lifecycle-simulation-script-simend_to_end_mission_simpy)
      * [11.4.4 Multi-Panel Diagnostic Waveform Analysis](#1144-multi-panel-diagnostic-waveform-analysis)
      * [11.4.5 What We Expect & Target from Physical Hardware Testing](#1145-what-we-expect--target-from-physical-hardware-testing)
      * [11.4.6 Physical Hardware Acceptance Criteria & Measurement Protocol](#1146-physical-hardware-acceptance-criteria--measurement-protocol)
    * [11.5 STDP Ablation Study: Adaptive Neuromorphic Reflex vs. Multi-Detector Baselines (`ablation_study_stdp_vs_threshold.py`)](#115-stdp-ablation-study-adaptive-neuromorphic-reflex-vs-multi-detector-baselines-ablation_study_stdp_vs_thresholdpy)
    * [11.6 Per-Sample Python vs. Verilog RTL Lockstep Verification (`verify_python_rtl_lockstep.py`)](#116-per-sample-python-vs-verilog-rtl-lockstep-verification-verify_python_rtl_locksteppy)'''

assert old_toc in content, 'TOC not found!'
content = content.replace(old_toc, new_toc)

# Fix duplicated 11.4.4 heading
old_h1 = '### 11.4.4 What We Expect & Target from Physical Hardware Testing'
new_h1 = '### 11.4.5 What We Expect & Target from Physical Hardware Testing'
assert old_h1 in content, 'old_h1 not found!'
content = content.replace(old_h1, new_h1)

old_h2 = '### 11.4.5 Physical Hardware Acceptance Criteria & Measurement Protocol'
new_h2 = '### 11.4.6 Physical Hardware Acceptance Criteria & Measurement Protocol'
assert old_h2 in content, 'old_h2 not found!'
content = content.replace(old_h2, new_h2)

with open('C:/Users/NEERAJ/Desktop/SUB3MW_ICE40_STDP_PROJECT_BIBLE.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESSFULLY updated TOC and Section 11 headings in Project Bible.')
