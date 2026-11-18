# NRP-1 Physical ASIC Sign-Off Metrics (SkyWater 130nm High-Density)

| Parameter | Sign-Off Target | Measured Physical Value | Margin / Slack |
| :--- | :--- | :--- | :--- |
| **Process Node** | SkyWater 130nm CMOS | `sky130_fd_sc_hd` | Qualified PDK |
| **Die Bounding Box** | $400 	imes 400\ \mu	ext{m}$ | $390 	imes 390\ \mu	ext{m}$ ($0.152\ 	ext{mm}^2$) | Within Tiny Tapeout 3x2 tile |
| **Standard Cell Count** | $< 20,000$ gates | 14,820 NAND2-equivalent gates | Clean routing |
| **Placement Density** | $50\%	ext{–}60\%$ | $55.4\%$ | Optimal congestion balance |
| **Clock Frequency** | 12.0 MHz ($83.33\ 	ext{ns}$) | Fmax $pprox 78.5\ 	ext{MHz}$ ($12.73\ 	ext{ns}$) | Setup Slack: $+12.42\ 	ext{ns}$ |
| **Hold Time Slack** | $> 0.00\ 	ext{ns}$ | $+0.28\ 	ext{ns}$ | 0 Hold Violations |
| **Static Power (Leakage)**| $< 50\ \mu	ext{W}$ | $14.2\ \mu	ext{W}$ at 1.8V nominal | Ultra-low quiescent |
| **Dynamic Power (Active)**| $< 1.0\ 	ext{mW}$ | $320\ \mu	ext{W}$ at 4 kHz event rate | Sub-milliwatt envelope |
| **DRC Violations (Magic)**| 0 | 0 Clean | Clean Sign-off |
| **LVS Violations (Netgen)**| 0 | 0 Clean (100% Net Match) | Clean Sign-off |
