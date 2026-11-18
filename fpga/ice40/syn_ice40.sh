#!/bin/bash
set -e
echo "Synthesizing NRP-1 for Lattice iCE40UP5K with Yosys..."
yosys -p "synth_ice40 -top snn_core_top -json nrp1_core.json" \
  ../../rtl/snn_core_top.v \
  ../../rtl/delta_encoder.v \
  ../../rtl/stdp_synapse_unit.v \
  ../../rtl/stdp_trace_generator.v \
  ../../rtl/synapse_crossbar_256.v \
  ../../rtl/lif_neuron_array.v \
  ../../rtl/lateral_inhibition.v \
  ../../rtl/icm42688_spi_master.v \
  ../../rtl/servo_reflex_pwm.v

echo "Place and Route with nextpnr-ice40..."
nextpnr-ice40 --up5k --package sg48 --json nrp1_core.json --pcf pins.pcf --asc nrp1_core.asc

echo "Generating Bitstream with icepack..."
icepack nrp1_core.asc nrp1_core.bin
echo "[SUCCESS] iCE40 bitstream ready: nrp1_core.bin"
