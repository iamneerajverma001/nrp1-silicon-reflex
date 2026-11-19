# NRP-1: An Event-Driven Neuromorphic Reflex Processor
## Plain-English Engineering Overview & Project Summary
**Project Type:** Undergraduate Major Research Project  
**Discipline:** Electronics & Communication Engineering (Digital VLSI & Edge Neuromorphic Systems)  
**Authors:** ECE Major Capstone Research Team  
**Repository:** [github.com/iamneerajverma001/nrp1-silicon-reflex](https://github.com/iamneerajverma001/nrp1-silicon-reflex)  

---

## 1. What Is This Project?

This project is a custom-designed microchip (called **NRP-1**) that gives physical machines an **instant biological reflex**. 

Just like a human spinal cord pulls your hand away from a hot surface in milliseconds before your conscious brain even registers pain, NRP-1 sits directly on a motion sensor, monitors mechanical vibrations, learns what "normal" operation feels like, and triggers an emergency shut-off in **under 2 milliseconds** if something cracks or breaks.

Crucially, it does all of this **directly on the silicon** without running an operating system, without executing lines of software code, without sending data to the cloud, and while burning **less than half a milliwatt (0.47 mW)** of power.

```
                    THE BIOLOGICAL REFLEX PRINCIPLE
                    
   Conventional Edge AI (The "Cerebral Cortex"):
   [ Sensors ] ---> [ Complex MCU / GPU ] ---> [ Heavy Software OS ] ---> [ Late Decision (30-50 ms) ]
                    (Burns 30-85 mW, waits on software loops, rigid pre-trained weights)

   Our Approach (The "Silicon Spinal Cord"):
   [ Sensors ] ---> [ NRP-1 Custom Silicon ] --------------------------> [ Instant Reflex (< 1.6 ms) ]
                    (Burns < 0.5 mW, multiplier-less logic, learns on-chip in real time)
```

---

## 2. The Real Problem We Are Solving

When engineers want to monitor machines, industrial motors, drones, or robotic arms today, they usually attach an off-the-shelf microcontroller (like an Arduino or STM32) or a small AI board (like a Raspberry Pi or NVIDIA Jetson). 

In physical systems, this approach fails for three specific reasons:

1. **Software Latency Is Too Slow:**  
   Microcontrollers run instructions in a sequential software loop. Between reading sensors over a shared bus, running filter algorithms, and executing logic, the system takes **15 to 50 milliseconds** to decide to stop. In high-speed machinery, a cracked bearing or propeller fractures in **less than 5 milliseconds**. By the time the software reacts, the hardware has already suffered catastrophic damage.

2. **Power Consumption Is Too High:**  
   Standard microprocessors continuously poll sensors and calculate heavy floating-point numbers. They consume **30 to 85 milliwatts** (and edge AI chips consume several watts). Tiny battery-powered edge devices, biomedical implants, and energy-harvesting industrial sensors cannot sustain this power draw.

3. **Static Pre-Trained Models Cannot Adapt:**  
   Traditional machine learning models are trained on a computer and their parameters are frozen before deployment. If an industrial motor speeds up normally (e.g., from 3,000 RPM to 7,200 RPM), the vibration frequency shifts. Standard mathematical filters mistake this normal operational change for a defect and trigger false alarms.

---

## 3. How NRP-1 Works (Inside the Silicon)

Instead of relying on software, we designed the entire system from the transistor-register level up in synthesizable digital logic (Verilog). The chip operates in four hardware stages:

### Step 1: Autonomous Sensor Telemetry (SPI Master)
The chip talks directly to an industrial 6-axis accelerometer/gyroscope (ICM-42688-P) over an SPI bus at **4,000 samples per second**. A dedicated hardware state machine configures and reads the sensor without needing a host CPU.

### Step 2: Pulse Generation (Delta-Spike Modulation)
Instead of processing full 16-bit numbers, the chip compares each incoming reading with its previous value. If the vibration moves up or down by a set threshold, it outputs a single 1-bit digital pulse (a "spike"). If nothing changes, the chip emits zero spikes. This event-driven approach cuts dynamic power consumption by over 90%.

### Step 3: On-Chip Online Learning (Hardware STDP)
The processor contains **32 digital artificial neurons** connected through **256 programmable synapses**. 
* The chip implements a biological learning rule called **STDP** (*Spike-Timing-Dependent Plasticity*): connections that fire together are strengthened, while inactive connections are weakened.
* As the machine operates, the chip continuously tunes its internal weights to habituate to the normal background hum.
* **100% Multiplier-Less Arithmetic:** Instead of expensive digital multipliers, all learning and thresholding math is done with simple bit-shifts and additions, keeping the chip small and efficient.

### Step 4: The Sub-2 Millisecond Reflex (PWM Actuation)
If a high-frequency fracture or violent vibration occurs, a dedicated set of "watchdog" neurons fires in rapid bursts. When 4 bursts occur across consecutive samples, the chip trips a hardware latch within **1.601 milliseconds** (19,213 clock cycles at 12 MHz), immediately forcing an actuator pulse to disconnect motor power or engage a mechanical brake.

---

## 4. How We Proved It: The Motor Speed-Sweep Test

To evaluate whether on-chip learning outperforms traditional methods, we set up a benchmark test vehicle: a motor accelerating across a broad speed sweep from **50 Hz to 120 Hz (3,000 to 7,200 RPM)**, followed by an injected 1.2 kHz resonant defect.

| Detection Method | Speed Sweep Behavior (50 to 120 Hz) | Defect Reaction Time | Overall Outcome |
| :--- | :--- | :---: | :---: |
| **Standard 2nd-Order High-Pass Filter** | **False Alarm at 945.5 ms** (Motor harmonic crossed into passband) | Failed (Tripped prematurely) | **FAIL** (False trip during normal acceleration) |
| **Envelope-Tracking Detector** | **False Alarm at 176.2 ms** (Tripped on start-up ripple) | Failed (Tripped prematurely) | **FAIL** (Too sensitive to acceleration ripple) |
| **Our NRP-1 Core (On-Chip STDP Learning)** | **0.00% False Alarms** (Weights adapted from 450.08 to 1,417.51) | **1.75 ms** post-defect onset | **PASS** (Zero false alarms + sub-2 ms reflex) |

**Conclusion:** Traditional static filters cannot distinguish between a machine changing speeds and a real defect. NRP-1 adapts locally to speed changes while remaining primed to catch sudden structural fractures in under two milliseconds.

---

## 5. What We Actually Built (The Engineering Stack)

This project was built from scratch without using pre-packaged AI libraries or proprietary vendor IP blocks. We delivered the complete five-stage VLSI hardware pipeline:

```
+---------------------------------------------------------------------------------------------------------+
| DESIGN STAGE                   | ENGINEERING WORK DELIVERED                                             |
+--------------------------------+------------------------------------------------------------------------+
| 1. Mathematical Modeling       | Bit-exact Python emulator modeling all integer arithmetic, leaky      |
|                                | traces, and saturation boundaries with zero floating-point math.      |
+--------------------------------+------------------------------------------------------------------------+
| 2. Synthesizable Digital RTL   | 9 modular hardware blocks written in pure IEEE 1364-2001 Verilog       |
|                                | (delta encoder, STDP synapses, LIF neurons, SPI master, PWM driver).   |
+--------------------------------+------------------------------------------------------------------------+
| 3. Dual-Model Lockstep Test    | Ran Python and real Verilog simulations side-by-side. Verified all 7   |
|                                | internal hardware signals with ZERO mismatches across thousands of cycles.|
+--------------------------------+------------------------------------------------------------------------+
| 4. FPGA Hardware Emulation     | Synthesized on a Lattice iCE40 UltraPlus (fits in < 3,200 LUTs)        |
|                                | and Xilinx Spartan-7, verifying 12.0 MHz timing closure at < 0.5 mW.   |
+--------------------------------+------------------------------------------------------------------------+
| 5. Physical ASIC Silicon Sign-Off | Hardened using OpenLane 2 on SkyWater 130nm CMOS. Produced DRC-clean |
|                                | and LVS-clean GDSII layout masks ready for factory silicon tapeout.   |
+--------------------------------+------------------------------------------------------------------------+
```

---

## 6. Where Can This Be Used in Real Life?

While our physical test vehicle was a rotating motor, the NRP-1 architecture is a universal reflex core applicable to any high-speed physical system:

1. **Bionic Prosthetics & Robotic Hands:**  
   Detecting microscopic object slippage in under 2 milliseconds to tighten grip force before a delicate glass or egg is dropped (human spinal reflexes take 20 ms; standard robot controllers take 50 ms).
2. **Drones & eVTOL Aircraft:**  
   Instant motor disengagement upon propeller strikes or sudden structural flutter, preventing in-flight airframe breakup.
3. **Ultra-Low-Power Medical Implants:**  
   Continuous microwatt cardiac anomaly detection or closed-loop seizure interruption, operating safely beneath the 10 milliwatt thermal limit that causes human tissue damage.
4. **Spacecraft & CubeSats:**  
   Because the chip has zero microcode, no instruction pointer, and no complex CPU caches, it cannot suffer software kernel panics from cosmic radiation (SEUs) and runs reliably on tiny solar budgets.

---

## 7. Key Project Numbers at a Glance

```
+---------------------------------------+-----------------------+-----------------------+
| METRIC                                | TRADITIONAL MCU / GPU | NRP-1 SILICON REFLEX  |
+---------------------------------------+-----------------------+-----------------------+
| Active Core Power                     | 30 to 85 mW (MCU)     | 0.47 mW (FPGA Core)   |
|                                       | 1,500 to 5,000 mW(GPU)| 320 uW (ASIC Core)    |
+---------------------------------------+-----------------------+-----------------------+
| Closed-Loop Reaction Latency          | 15 to 50 ms           | 1.601 ms (Verified)   |
+---------------------------------------+-----------------------+-----------------------+
| Digital Multipliers Required          | 1 to 4 Multipliers    | ZERO (Bit-shift only) |
+---------------------------------------+-----------------------+-----------------------+
| Learning Capability                   | Static Frozen Weights | On-Chip Online STDP   |
+---------------------------------------+-----------------------+-----------------------+
| Speed-Sweep False Alarm Rate          | 12.4% False Trips     | 0.00% False Alarms    |
+---------------------------------------+-----------------------+-----------------------+
| Silicon Area (SkyWater 130nm)         | N/A (Standard Chips)  | 0.152 mm^2 (14.8k cls)|
+---------------------------------------+-----------------------+-----------------------+
```

---

## Summary in Plain Words

> *"Instead of using a generic, power-hungry microcontroller running slow software loops, we designed a tiny, custom silicon brain-stem from scratch. It connects directly to a vibration sensor, learns on-chip what normal operating sounds like without needing a computer, and cuts off power in 1.6 milliseconds when a machine cracks—using less electrical energy than an LED indicator light."*
