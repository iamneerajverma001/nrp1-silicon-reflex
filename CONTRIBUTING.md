# Contributing to NRP-1 Neuromorphic Processor

Thank you for your interest in contributing to the **NRP-1 Silicon Reflex** open-source hardware project!

## Code of Conduct & Academic Integrity
This repository serves as an ECE Undergraduate Major Research Project and open-source hardware initiative. Every contribution must maintain strict verification standards and adhere to reproducible engineering practices.

## Verification Gate Requirements Before Pull Request
Before submitting any Pull Request modifying `rtl/` or `sim/`, you **MUST** run the full verification suite locally:
```bash
python run_verification.py
```
All 6 verification tiers must report **PASSED** with **0 mismatches** in the 7-signal lockstep engine.

## Verilog RTL Style Guidelines
* All Verilog RTL must adhere strictly to **IEEE 1364-2001 synthesizable Verilog**.
* **Zero unpacked array ports** (`input wire [7:0] port [0:31]` is strictly disallowed; use 1D packed buses `input wire [255:0] port`).
* **Zero internal tri-state buffers or latches**.
* Every module must begin with `` `default_nettype none `` and terminate with `` `default_nettype wire ``.
* Non-blocking assignments (`<=`) for sequential registers; blocking assignments (`=`) for combinational logic.
