# Vivado Batch Synthesis Script for Spartan-7
read_verilog [glob ../../rtl/*.v]
read_xdc constraints.xdc
synth_design -top snn_core_top -part xc7s25csga196-1 -flatten_hierarchy rebuilt
opt_design
place_design
route_design
report_timing_summary -file timing_summary.rpt
report_utilization -file utilization.rpt
write_bitstream -force nrp1_spartan7.bit
