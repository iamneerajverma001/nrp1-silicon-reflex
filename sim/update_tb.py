with open('C:/Users/NEERAJ/.gemini/antigravity/scratch/nrp1_neuromorphic_core/sim/tb_snn_core_top.v', 'r') as f:
    content = f.read()

# Replace baseline stimulus with smooth 32-entry sine LUT
old_stim = '''            // Generate Sensor Stimulus
            if (cycle < FAULT_CYCLE) begin
                // Normal Healthy Baseline: 50 Hz vibration on Acc_X & Acc_Z
                // Period at 12 MHz = 240,000 cycles. Half period = 120,000 cycles.
                stim_ax <= ((cycle % 24000) < 12000) ? 16'sd60 : -16'sd60;
                stim_ay <= ((cycle % 36000) < 18000) ? 16'sd30 : -16'sd30;
                stim_az <= ((cycle % 24000) < 12000) ? 16'sd24 : -16'sd24;
                stim_gx <= 16'sd12;
                stim_gy <= 16'sd8;
                stim_gz <= 16'sd16;

                // STRICT ASSERTION: Zero false alarms during normal baseline!
                if (alarm_led) begin
                    $display("[FATAL ERROR] False alarm tripped at cycle %0d during normal baseline operation!", cycle);
                    $fclose(trace_fd);
                    $finish;
                end
            end else begin'''

new_stim = '''            // Generate Sensor Stimulus using smooth 32-point 50 Hz sinusoidal table
            // Period at 12 MHz = 240,000 cycles (7,500 cycles per phase step)
            if (cycle < FAULT_CYCLE) begin
                case ((cycle / 7500) % 32)
                    0:  stim_ax <= 16'sd0;
                    1:  stim_ax <= 16'sd16;
                    2:  stim_ax <= 16'sd31;
                    3:  stim_ax <= 16'sd44;
                    4:  stim_ax <= 16'sd57;
                    5:  stim_ax <= 16'sd67;
                    6:  stim_ax <= 16'sd74;
                    7:  stim_ax <= 16'sd78;
                    8:  stim_ax <= 16'sd80;
                    9:  stim_ax <= 16'sd78;
                    10: stim_ax <= 16'sd74;
                    11: stim_ax <= 16'sd67;
                    12: stim_ax <= 16'sd57;
                    13: stim_ax <= 16'sd44;
                    14: stim_ax <= 16'sd31;
                    15: stim_ax <= 16'sd16;
                    16: stim_ax <= 16'sd0;
                    17: stim_ax <= -16'sd16;
                    18: stim_ax <= -16'sd31;
                    19: stim_ax <= -16'sd44;
                    20: stim_ax <= -16'sd57;
                    21: stim_ax <= -16'sd67;
                    22: stim_ax <= -16'sd74;
                    23: stim_ax <= -16'sd78;
                    24: stim_ax <= -16'sd80;
                    25: stim_ax <= -16'sd78;
                    26: stim_ax <= -16'sd74;
                    27: stim_ax <= -16'sd67;
                    28: stim_ax <= -16'sd57;
                    29: stim_ax <= -16'sd44;
                    30: stim_ax <= -16'sd31;
                    31: stim_ax <= -16'sd16;
                endcase
                stim_ay <= stim_ax >>> 1; // 50% amplitude on Ay
                stim_az <= 16'sd12;       // Stable DC gravity baseline on Az
                stim_gx <= 16'sd8;
                stim_gy <= 16'sd4;
                stim_gz <= 16'sd10;

                // STRICT ASSERTION: Zero false alarms during normal baseline!
                if (alarm_led) begin
                    $display("[FATAL ERROR] False alarm tripped at cycle %0d during normal baseline operation!", cycle);
                    $fclose(trace_fd);
                    $finish;
                end
            end else begin'''

assert old_stim in content, 'old_stim not found in tb_snn_core_top.v'
content = content.replace(old_stim, new_stim)

with open('C:/Users/NEERAJ/.gemini/antigravity/scratch/nrp1_neuromorphic_core/sim/tb_snn_core_top.v', 'w') as f:
    f.write(content)

print('SUCCESSFULLY updated tb_snn_core_top.v with smooth 50 Hz sine LUT.')
