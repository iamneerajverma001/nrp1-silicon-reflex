# ==============================================================================
# Xilinx Spartan-7 XC7S25-CSGA196 Pin & Timing Constraints
# ==============================================================================

# Clock Constraint (12.0 MHz = 83.333 ns period)
create_clock -period 83.333 -name sys_clk [get_ports clk]

# Pin Assignments (Bank 14/34 3.3V LVCMOS)
set_property PACKAGE_PIN H14 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]

set_property PACKAGE_PIN M14 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

set_property PACKAGE_PIN M15 [get_ports learn_switch]
set_property IOSTANDARD LVCMOS33 [get_ports learn_switch]

set_property PACKAGE_PIN J13 [get_ports spi_sck]
set_property IOSTANDARD LVCMOS33 [get_ports spi_sck]

set_property PACKAGE_PIN J14 [get_ports spi_cs_n]
set_property IOSTANDARD LVCMOS33 [get_ports spi_cs_n]

set_property PACKAGE_PIN K14 [get_ports spi_mosi]
set_property IOSTANDARD LVCMOS33 [get_ports spi_mosi]

set_property PACKAGE_PIN K15 [get_ports spi_miso]
set_property IOSTANDARD LVCMOS33 [get_ports spi_miso]

set_property PACKAGE_PIN L14 [get_ports imu_int1]
set_property IOSTANDARD LVCMOS33 [get_ports imu_int1]

set_property PACKAGE_PIN N14 [get_ports servo_pwm]
set_property IOSTANDARD LVCMOS33 [get_ports servo_pwm]

set_property PACKAGE_PIN N15 [get_ports alarm_led]
set_property IOSTANDARD LVCMOS33 [get_ports alarm_led]

set_property PACKAGE_PIN P14 [get_ports clamp_led]
set_property IOSTANDARD LVCMOS33 [get_ports clamp_led]

set_property PACKAGE_PIN P15 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
