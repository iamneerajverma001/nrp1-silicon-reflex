# PROJECT EXECUTIVE BRIEF: NEUROMORPHIC REFLEX PROCESSOR (NRP-1)
## An Event-Driven, Online-Learning Silicon Architecture for Ultra-Fast Cyber-Physical Reflexes

**Student Name:** Neeraj Verma  
**Degree / Department:** Bachelor of Technology in Electronics & Communication Engineering (ECE)  
**Project Category:** Final Year Major Research Project / Capstone  
**Supervisor Submission Date:** November 2026  
**Repository (Open-Source SSOT):** [https://github.com/iamneerajverma001/nrp1-silicon-reflex](https://github.com/iamneerajverma001/nrp1-silicon-reflex)  

---

### 1. Executive Summary

This project addresses a fundamental limitation in edge computing: conventional microcontrollers and embedded processors cannot execute sub-2 millisecond physical reflexes under microwatt power constraints. 

To solve this, we designed, simulated, verified, and placed on physical silicon layout the **Neuromorphic Reflex Processor (NRP-1)**. NRP-1 is a custom, non-Von-Neumann digital processor built from scratch in synthesizable Verilog. It connects directly to high-speed motion sensors, converts raw vibration into asynchronous 1-bit neural spikes, and learns the normal operational baseline on-chip using Spike-Timing-Dependent Plasticity (STDP). When a mechanical defect occurs, NRP-1 triggers an emergency reflex shut-off in **1.601 milliseconds** while consuming only **0.47 mW on an FPGA** and **320 µW on a 130 nm ASIC**.

---

### 2. Problem Statement & Motivation

| Parameter | Standard Embedded Approach (e.g., ARM Cortex-M4) | Proposed Silicon Solution (NRP-1) |
| :--- | :--- | :--- |
| **Computing Model** | Von Neumann (sequential instruction fetch & ALU loops) | Event-Driven Spiking Neural Network (non-Von-Neumann) |
| **Sensor Handling** | CPU polls sensor over SPI/I2C via periodic interrupts | Autonomous hardware SPI master streams directly to neurons |
| **Latency** | $15\text{--}45\text{ ms}$ (software loop & RTOS scheduling jitter) | **$1.601\text{ ms}$** (hardwired digital datapath: 19,213 clock cycles) |
| **Active Core Power** | $30\text{--}85\text{ mW}$ | **$0.47\text{ mW}$** (FPGA core) / **$320\ \mu\text{W}$** (130 nm ASIC) |
| **Arithmetic** | Heavy 32-bit hardware multipliers and floating-point units | **100% Multiplier-Less** (shift-and-add binary arithmetic) |
| **Model Adaptivity** | Static pre-trained weights (cannot adapt on-chip to drift) | **On-Chip Online STDP** (adapts locally without cloud/host) |

**The Engineering Problem:**  
When high-speed machinery, robotic hands, or aerospace surfaces suffer sudden structural defects (e.g., bearing cracks, gear fractures, or tactile slip), physical damage occurs within 5 to 10 milliseconds. Microcontrollers running software filtering loops are too slow to intervene. Conversely, fixed digital bandpass filters trigger unacceptable false alarms when machines legitimately change operating speeds.

---

### 3. Silicon Architecture & Technical Implementation

NRP-1 is implemented across 9 modular hardware blocks in pure **IEEE 1364-2001 Verilog**:

1. **Autonomous SPI Master (`icm42688_spi_master.v`):** Directly configures and reads an external 6-axis IMU (ICM-42688-P) at 4.0 kHz over a 6 MHz SPI bus without needing a host CPU.
2. **Delta-Modulation Event Encoder (`delta_encoder.v`):** Converts 16-bit signed sensor telemetry into asynchronous 1-bit presynaptic spike pulses ($s_{\text{pre}}$) using 17-bit sign-extended subtraction with DC gravity preloading. Logic only switches when motion changes.
3. **Plastic Synapse Crossbar (`synapse_crossbar_256.v`, `stdp_synapse_unit.v`):** A $8 \times 32$ crossbar (256 plastic synapses). Each synapse implements local STDP using sign-extended 9-bit saturating adders ($[-128, +127]$) to prevent arithmetic rollover.
4. **Multiplier-Less Eligibility Trace Engine (`stdp_trace_generator.v`):** Computes presynaptic and postsynaptic traces using a bit-shift floor leak ($T[t] = T[t-1] - (T[t-1] \gg 2)$), mathematically guaranteeing monotonic decay to zero in $\le 10$ quiet cycles (zero limit-cycle noise).
5. **Leaky Integrate-and-Fire Neuron Array (`lif_neuron_array.v`):** 32 integer LIF neurons with configurable leakage prescaling and threshold evaluation prior to leak subtraction.
6. **Soft Winner-Take-All Lateral Inhibition (`lateral_inhibition.v`):** Prevents network saturation by allowing the most active neuron to suppress neighboring activity.
7. **Direct Actuation PWM Engine (`servo_reflex_pwm.v`):** Immediately reloads hardware counter registers upon fault latching, eliminating PWM frame delay to drive an emergency shut-off servo.

---

### 4. Experimental Validation & Key Results

#### A. 7-Signal Cycle-Accurate Lockstep Verification
We built a bit-exact Python reference model (`bit_exact_simulator.py`) and simulated the complete Verilog RTL using Icarus Verilog (`iverilog`/`vvp`). Over an automated hardware evaluation trace, **all 7 core signals matched with 0 mismatches**:
* Presynaptic Spikes ($s_{\text{pre}}$): **0 errors**
* Reference Voltage ($v_{\text{ref}}$): **0 errors**
* Eligibility Traces ($t_{\text{pre}}$): **0 errors**
* Synaptic Weights ($w_{00}$): **0 errors**
* Postsynaptic Spikes ($s_{\text{post}}$): **0 errors**
* Burst Counter State: **0 errors**
* Alarm Latched Trip: **0 errors**

#### B. Dynamic Motor Speed-Sweep Benchmark (Ablation Study)
We evaluated NRP-1 against conventional detectors on a variable-speed motor testbench accelerating from **50 Hz to 120 Hz (3,000 to 7,200 RPM)**, followed by a sudden 1.2 kHz resonant chatter defect:
* **2nd-Order High-Pass Filter (HPF):** Triggered a **false alarm at 945.5 ms** because rotating machine harmonics crossed into the filter passband during normal acceleration.
* **Envelope-Tracking Baseline:** Triggered a **false alarm at 176.25 ms** due to transient start-up ripple.
* **NRP-1 (Adaptive STDP):** Maintained **0.00% false alarms** throughout the entire 50 Hz $\to$ 120 Hz speed sweep by continuously habituating its baseline weights ($\|\mathbf{W}\|: 450.08 \to 1,417.51$). When the 1.2 kHz crack defect was injected at $t = 2.000\text{ s}$, NRP-1 latched the emergency shut-off in **1.750 ms**.

#### C. Physical Synthesis & Silicon Implementation
* **FPGA Target (Lattice iCE40UP5K-SG48):** Fully synthesized using Yosys and nextpnr; fits within 4,820 LUT4s (91.3% of chip, or 1,180 LUTs when utilizing internal SPRAM blocks) at 12.0 MHz with **0.47 mW active core power**.
* **ASIC Sign-Off Target (SkyWater 130 nm CMOS - `sky130_fd_sc_hd`):** Pushed through OpenLane 2 physical layout. Achieved complete DRC/LVS clean sign-off in a **$390 \times 390\ \mu\text{m}$ ($0.152\ \text{mm}^2$)** bounding box, 14,820 standard gates, $+12.42\text{ ns}$ setup timing slack at 12.0 MHz, and **320 µW active power**.

---

### 5. Academic Foundations & Literature References

The theoretical, biological, and VLSI foundations of this work are grounded in the following peer-reviewed literature:

#### 1. Spike-Timing-Dependent Plasticity (STDP) Biological Mechanics
* **Bi, G. Q., & Poo, M. M. (1998).** *"Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, calcium influx, and prior synaptic activity."* **Journal of Neuroscience**, 18(24), 10464–10472.  
  DOI / URL: [https://doi.org/10.1523/JNEUROSCI.18-24-10464.1998](https://doi.org/10.1523/JNEUROSCI.18-24-10464.1998)  
  *Significance:* Establishes the asymmetric exponential biological Hebbian learning window that NRP-1 implements digitally.
* **Markram, H., Lübke, J., Frotscher, M., & Sakmann, B. (1997).** *"Regulation of synaptic efficacy by coincidence of postsynaptic APs and EPSPs."* **Science**, 275(5297), 213–215.  
  DOI / URL: [https://doi.org/10.1126/science.275.5297.213](https://doi.org/10.1126/science.275.5297.213)  
  *Significance:* Foundational discovery demonstrating that the precise sub-millisecond millivolt timing of pre- and post-synaptic events dictates causal synaptic potentiation (LTP) versus depression (LTD).

#### 2. Digital Neuromorphic Processors & On-Chip Online Learning
* **Frenkel, C., Lefebvre, M., Legat, J. D., & Bol, D. (2019).** *"A 0.086-mm² 12.7-pJ/SOP 64k-synapse 256-neuron online-learning digital spiking neuromorphic processor in 28-nm CMOS (ODIN)."* **IEEE Transactions on Biomedical Circuits and Systems (TBCAS)**, 13(1), 145–158.  
  DOI / URL: [https://doi.org/10.1109/TBCAS.2018.2880425](https://doi.org/10.1109/TBCAS.2018.2880425)  
  *Significance:* Proves the feasibility of phenomenological digital STDP implementations with integer arithmetic, directly informing our multiplier-less 9-bit saturating synapse design.
* **Davies, M., et al. (2018).** *"Loihi: A neuromorphic manycore processor with on-chip learning."* **IEEE Micro**, 38(1), 82–99.  
  DOI / URL: [https://doi.org/10.1109/MM.2018.112130359](https://doi.org/10.1109/MM.2018.112130359)  
  *Significance:* Demonstrates that local microcode-free on-chip plasticity provides substantial efficiency gains over cloud-trained static architectures.
* **Indiveri, G., et al. (2011).** *"Neuromorphic silicon neuron circuits."* **Frontiers in Neuroscience**, 5, 73.  
  DOI / URL: [https://doi.org/10.3389/fnins.2011.00073](https://doi.org/10.3389/fnins.2011.00073)  
  *Significance:* Reviews the physical dynamics of silicon leaky integrate-and-fire circuits, providing the architectural basis for our integer leak-prescaling model.

#### 3. Spinal Reflex Arcs & Tactile Cyber-Physical Slip Detection
* **Johansson, R. S., & Flanagan, J. R. (2009).** *"Coding and use of tactile signals from the human hand in object manipulation."* **Nature Reviews Neuroscience**, 10(5), 345–359.  
  DOI / URL: [https://doi.org/10.1038/nrn2621](https://doi.org/10.1038/nrn2621)  
  *Significance:* Details the biological Meissner and Pacinian tactile mechanoreceptors that trigger sub-20 ms spinal grasp reflexes to prevent object slippage, serving as our primary biological analogue.
* **Osborn, L. E., et al. (2018).** *"Prosthesis with neuromorphic tactile sensation offers improved neuroprosthetic control."* **Science Robotics**, 3(19), eaat3818.  
  DOI / URL: [https://doi.org/10.1126/scirobotics.aat3818](https://doi.org/10.1126/scirobotics.aat3818)  
  *Significance:* Highlights the practical necessity of low-latency spiking feedback loops in neuro-prosthetic actuators to prevent drops without cerebral intervention.

---

### 6. Deliverables Summary for Review

1. **Source Code Repository:** Complete synthesizable RTL, testbenches, simulation models, and synthesis scripts:  
   🔗 [https://github.com/iamneerajverma001/nrp1-silicon-reflex](https://github.com/iamneerajverma001/nrp1-silicon-reflex)
2. **Master Verification Command:** Execute the 6-tier verification suite locally:  
   `python run_verification.py` (all tests pass with 0 mismatches).
3. **Engineering Blueprint:** Detailed 16-chapter technical specification and mathematical derivations:  
   `docs/PROJECT_BLUEPRINT.md`
4. **Market & Strategic Dossier:** Macroeconomic unit economics and comparative competitor matrices:  
   `docs/DEFENSE_DOSSIER.md`
5. **Physical ASIC Manifest:** OpenLane 2 configuration and pad order files for SkyWater 130 nm CMOS fabrication:  
   `asic/openlane_config.json` and `asic/pin_order.cfg`
