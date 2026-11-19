# ACADEMIC PROJECT BRIEF: NEUROMORPHIC REFLEX PROCESSOR (NRP-1)
**Project Title:** NRP-1: An Event-Driven Neuromorphic Reflex Processor with On-Chip Online STDP Learning for Sub-2 Millisecond Cyber-Physical Actuation  
**Candidate:** ECE Undergraduate Major Research Project  
**Target Submission / Track:** Final Year Major Project Thesis & IEEE BioCAS / ISCAS (Student Demonstration Track)  
**Repository (SSOT):** [https://github.com/iamneerajverma001/nrp1-silicon-reflex](https://github.com/iamneerajverma001/nrp1-silicon-reflex)  

---

## 1. Problem Statement & Research Gap: Why This Work?
In modern autonomous edge systems (high-speed robotics, prosthetics, and industrial rotating machinery), fast mechanical failures occur within 5–15 milliseconds. Current edge computing relies on embedded microcontrollers (ARM Cortex-M) or edge GPUs (NVIDIA Jetson) that:
1. **Suffer from Non-Deterministic Latency (15–50 ms):** Software polling loops, RTOS scheduling, and bus arbitration introduce latencies that are too slow to prevent high-speed mechanical fractures.
2. **Burn Excessive Active Power (30–85 mW for MCUs; 2–15 W for GPUs):** Unacceptable for energy-harvested or battery-constrained edge nodes.
3. **Execute Static Pre-Trained Weights:** Traditional embedded AI models are trained offline. When operational physics drift (such as motor acceleration sweeps from 50 Hz to 120 Hz), static filters cannot adapt, resulting in false alarms or undetected structural failure.

**The Research Question:** *Can we design a non-Von-Neumann, event-driven silicon macro that learns local vibrational physics online without a host CPU, reacting to mechanical defects in under 2 milliseconds at sub-milliwatt power?*

---

## 2. Proposed Silicon Architecture: What Was Built?
Rather than executing software on a generic CPU, we designed a dedicated hardware macro in **pure synthesizable IEEE 1364-2001 Verilog** acting as a **silicon spinal reflex arc**:

```
+---------------------------------------------------------------------------------------------------------+
|                                    NRP-1 HARDWARE PIPELINE TOPOLOGY                                     |
+---------------------------------------------------------------------------------------------------------+
| [ICM-42688-P IMU] --(SPI @ 6 MHz)--> [Autonomous 6-Register SPI Master FSM (4 kHz Burst Telemetry)]     |
|                                                          |                                              |
|                                                          v                                              |
|                      [8-Channel Dynamic Delta-Modulation Spike Encoder (17-bit Subtraction)]            |
|                                                          | (s_pre Spikes)                               |
|                                                          v                                              |
|                      [256 Plastic Synapses: 9-Bit Saturating Adders + Floor-Leak STDP Traces]           |
|                                                          |                                              |
|                                                          v                                              |
|                      [32 Leaky Integrate-and-Fire (LIF) Neurons + Soft Winner-Take-All (WTA)]            |
|                                                          | (s_post Spikes)                              |
|                                                          v                                              |
|                      [Hardware Timer-Reload PWM Controller (< 1.6 ms Reflex Latch -> 1.5ms to 2.0ms)]   |
+---------------------------------------------------------------------------------------------------------+
```

### Key Circuit Innovations
* **Zero Digital Multipliers:** All membrane leak, STDP eligibility decay, and synaptic current calculations use bit-shift and sign-extended 9-bit saturating integer arithmetic ($0$ DSP blocks used).
* **On-Chip Online Plasticity:** Implements Spike-Timing-Dependent Plasticity (STDP) locally on silicon. Plasticity dynamically habituates to operational baseline vibrations and freezes upon anomaly detection to prevent memory corruption.
* **Autonomous Telemetry Master:** The SPI master handles register initialization and 104-bit burst transactions directly in hardware without microprocessor supervision.

---

## 3. Measured Experimental & Verification Results

| Metric / Parameter | Traditional MCU Baseline (Cortex-M4) | NRP-1 Neuromorphic Core (Measured) | Validation Mechanism |
| :--- | :--- | :--- | :--- |
| **Reflex Latency** | $15\text{--}45\ \text{ms}$ (Interrupt jitter) | **$1.601\ \text{ms}$ (19,213 cycles @ 12 MHz)** | Cycle-accurate hardware testbench |
| **Active Core Power** | $30\text{--}85\ \text{mW}$ | **$0.47\ \text{mW}$ (FPGA) / $320\ \mu\text{W}$ (ASIC)** | Power estimation & gate-level STA |
| **Adaptivity vs. False Alarms** | $12.4\%$ (Fixed HPF trips at $945.5\text{ ms}$) | **$0.00\%$ False Alarms ($50 \to 120\text{ Hz}$ sweep)** | 5-Arm speed-sweep ablation study |
| **Digital Multipliers** | 1--4 Hardware Multipliers | **$0$ (100% Shift-Add Integer Logic)** | Synthesis netlist resource report |
| **Pre/Post-Silicon Match** | N/A (Software abstraction) | **100% Bit-Exact (0 mismatches across 7 signals)** | 10,000-sample Python-RTL lockstep |

---

## 4. Hardware Implementation & Deliverables
1. **Mathematical Golden Model:** Bit-exact Python simulator (`sim/bit_exact_simulator.py`) with formal proofs of BIBO stability and bounded trace decay ($T \to 0$ in $\le 10$ quiet steps).
2. **Synthesizable Verilog RTL:** 9 modular Verilog files (`rtl/`) adhering strictly to IEEE 1364-2001 (100% 1D packed buses, 0 internal latches, 0 vendor primitives).
3. **FPGA Emulation:** Synthesized and placed for **Lattice iCE40UP5K-SG48** (88% LUT4 utilization, $0.47\ \text{mW}$) and **AMD/Xilinx Spartan-7** (XC7S25).
4. **ASIC Physical Design (Tapeout Ready):** Completed OpenLane 2 physical flow on **SkyWater 130nm CMOS** (`sky130_fd_sc_hd`):
   * Die Area: $390\ \mu\text{m} \times 390\ \mu\text{m}$ ($0.152\ \text{mm}^2$, fits Tiny Tapeout 3x2 tile).
   * Gate Count: 14,820 NAND2-equivalent standard cells ($55.4\%$ cell density).
   * Static Timing Analysis: Setup slack $+12.42\ \text{ns}$ at 12.0 MHz ($F_{\text{max}} \approx 78.5\ \text{MHz}$). Clean DRC/LVS.

---

## 5. Foundational Literature & Research Citations

1. **Mead, C. (1990).** *"Neuromorphic electronic systems."* *Proceedings of the IEEE*, 78(10), 1629-1636.  
   * **DOI:** [10.1109/5.58356](https://doi.org/10.1109/5.58356)  
   * *Significance:* First paper defining the principle of computing in physical time with sub-milliwatt physics-matched silicon rather than Von Neumann architectures.

2. **Bi, G. Q., & Poo, M. M. (1998).** *"Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, calcium influx, and the sequence of stimulation."* *Journal of Neuroscience*, 18(24), 10464-10472.  
   * **URL:** [https://www.jneurosci.org/content/18/24/10464](https://www.jneurosci.org/content/18/24/10464)  
   * *Significance:* Biological foundation for the exponential STDP learning window implemented in NRP-1's `stdp_trace_generator.v`.

3. **Hennessy, J. L., & Patterson, D. A. (2019).** *"A new golden age for computer architecture."* *Communications of the ACM*, 62(2), 48-60.  
   * **DOI:** [10.1145/3282307](https://doi.org/10.1145/3282307)  
   * *Significance:* Establishes that the demise of Dennard scaling and the memory wall mandate Domain-Specific Architectures (DSAs) for energy efficiency.

4. **Davies, M., Srinivasa, N., Lin, T. H., et al. (Intel Labs, 2018).** *"Loihi: A neuromorphic manycore processor with on-chip learning."* *IEEE Micro*, 38(1), 82-99.  
   * **DOI:** [10.1109/MM.2018.112130359](https://doi.org/10.1109/MM.2018.112130359)  
   * *Significance:* Benchmarks on-chip online learning in digital CMOS, against which NRP-1 is framed as an ultra-compact single-core reflex macro.

5. **Frenkel, C., Lefebvre, M., Legat, J. D., & Bol, D. (2019).** *"A 0.086-mm² 12.7-pJ/SOP 64k-synapse 256-neuron online-learning digital spiking neuromorphic processor in 28-nm FDSOI."* *IEEE Transactions on Biomedical Circuits and Systems (TBCAS)*, 13(1), 145-158.  
   * **DOI:** [10.1109/TBCAS.2018.2880425](https://doi.org/10.1109/TBCAS.2018.2880425)  
   * *Significance:* Peer-reviewed benchmark for multiplier-less digital STDP SNNs; directly validates NRP-1's shift-register trace arithmetic and sub-milliwatt target envelope.

6. **Indiveri, G., Linares-Barranco, B., Hamilton, T. J., et al. (2011).** *"Neuromorphic silicon neuron circuits."* *Frontiers in Neuroscience*, 5, 73.  
   * **DOI:** [10.3389/fnins.2011.00073](https://doi.org/10.3389/fnins.2011.00073)  
   * *Significance:* Comprehensive review of physical leaky integrate-and-fire circuit dynamics and threshold-leak synchronization.
