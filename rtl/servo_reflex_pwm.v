// =============================================================================
// Module: servo_reflex_pwm.v
// Description: Micro-Servo PWM Controller with Immediate Emergency Pulse Restart
// Standard: IEEE 1364-2001 Verilog
// =============================================================================
`default_nettype none

module servo_reflex_pwm (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        slip_trigger,
    output reg         servo_pwm,
    output reg         clamp_active
);

    localparam [17:0] PERIOD_20MS    = 18'd240000; // 20 ms @ 12 MHz
    localparam [17:0] NORMAL_GRIP    = 18'd18000;  // 1.5 ms pulse width
    localparam [17:0] REFLEX_CLAMP   = 18'd24000;  // 2.0 ms pulse width

    reg [17:0] timer_cnt;
    reg [17:0] target_pulse;
    reg        slip_trigger_d1;

    wire slip_edge = slip_trigger && !slip_trigger_d1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timer_cnt       <= 18'd0;
            servo_pwm       <= 1'b0;
            target_pulse    <= NORMAL_GRIP;
            clamp_active    <= 1'b0;
            slip_trigger_d1 <= 1'b0;
        end else begin
            slip_trigger_d1 <= slip_trigger;

            if (slip_trigger) begin
                target_pulse <= REFLEX_CLAMP;
                clamp_active <= 1'b1;
            end

            // Immediate emergency pulse restart on rising edge of reflex trigger
            // Bypasses the up-to-20ms wait for the next PWM frame
            if (slip_edge && !clamp_active) begin
                timer_cnt <= 18'd0;
                servo_pwm <= 1'b1;
            end else if (timer_cnt >= PERIOD_20MS - 1) begin
                timer_cnt <= 18'd0;
                servo_pwm <= 1'b1;
            end else begin
                timer_cnt <= timer_cnt + 18'd1;
                if (timer_cnt >= target_pulse)
                    servo_pwm <= 1'b0;
            end
        end
    end

endmodule
`default_nettype wire
