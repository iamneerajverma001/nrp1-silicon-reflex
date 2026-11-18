// =============================================================================
// Module: snn_core_top.v
// Description: Complete Top-Level Neuromorphic Reflex Processor (NRP-1)
// Architecture:
//   - Autonomous 3-Register SPI Master (ICM-42688 Low-Noise Mode @ 4 kHz ODR)
//   - 3-Phase Pipelined Strobe Sequencer (Zero Timing Misalignment)
//   - 8-Channel Delta Modulation Spike Encoder
//   - 256-Synapse Plastic Crossbar (Dedicated Watchdog Neurons 24-31)
//   - 32 Integer LIF Neurons with Single-Chain Blocking Arithmetic
//   - Soft Winner-Take-All Lateral Inhibition Network
//   - Immediate Emergency Servo PWM Restart Reflex Controller
//   - 115,200 Baud Diagnostic Telemetry UART
// Standard: IEEE 1364-2001 Verilog
// =============================================================================
`default_nettype none

module snn_core_top #(
    parameter [19:0] STARTUP_DELAY = 20'd600000 // 50 ms datasheet stabilization default for physical hardware (override to 20'd2400 in fast simulation)
)(
    input  wire        clk,              // 12 MHz Master Clock
    input  wire        rst_n,            // Active-Low Hardware Reset
    input  wire        learn_switch,     // Mode: 1 = Continuous Plasticity, 0 = Frozen Reflex
    input  wire        imu_int1,         // ICM-42688 INT1 Data-Ready Interrupt Pin
    input  wire        spi_miso,         // SPI Master-In-Slave-Out
    output wire        spi_sck,          // SPI Serial Clock (6 MHz)
    output wire        spi_cs_n,         // SPI Chip Select (Active Low)
    output wire        spi_mosi,         // SPI Master-Out-Slave-In
    output wire        servo_pwm,        // 50 Hz PWM Actuator Lead
    output wire        alarm_led,        // Anomaly Trip Indicator (Active High)
    output wire        clamp_led,        // Reflex Clamped Indicator (Active High)
    output wire        uart_tx           // Diagnostic Telemetry Serial Out (115.2 kbps)
);

    // -------------------------------------------------------------------------
    // 1. 4.0 kHz Master Sensor Sampling Synchronizer (INT1 DRDY + Watchdog Timer)
    // -------------------------------------------------------------------------
    localparam [15:0] FALLBACK_TIMEOUT = 16'd6000; // 2 ODR periods @ 12 MHz (500 us) watchdog fallback
    localparam [15:0] AUTONOMOUS_ODR   = 16'd3000; // Exact 4.0 kHz period if INT1 is unused/unconnected

    reg [15:0] sample_timer;
    reg        trigger_sensor_read;
    reg        int1_active_mode;

    // 2-stage synchronizer for asynchronous IMU INT1 Data-Ready interrupt
    reg [2:0] int1_sync;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) int1_sync <= 3'b000;
        else        int1_sync <= {int1_sync[1:0], imu_int1};
    end
    wire int1_pulse = (int1_sync[2:1] == 2'b01);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_timer        <= 16'd0;
            trigger_sensor_read <= 1'b0;
            int1_active_mode    <= 1'b0;
        end else begin
            if (int1_pulse) begin
                // Synchronized hardware interrupt received: reset watchdog and trigger burst read
                int1_active_mode    <= 1'b1;
                sample_timer        <= 16'd0;
                trigger_sensor_read <= 1'b1;
            end else if (!int1_active_mode && sample_timer >= AUTONOMOUS_ODR - 16'd1) begin
                // INT1 not yet detected: autonomous 4.0 kHz timer mode
                sample_timer        <= 16'd0;
                trigger_sensor_read <= 1'b1;
            end else if (int1_active_mode && sample_timer >= FALLBACK_TIMEOUT - 16'd1) begin
                // INT1 mode active but interrupt was missed / delayed >= 2 periods: watchdog fallback trigger
                sample_timer        <= 16'd0;
                trigger_sensor_read <= 1'b1;
            end else begin
                sample_timer        <= sample_timer + 16'd1;
                trigger_sensor_read <= 1'b0;
            end
        end
    end

    // -------------------------------------------------------------------------
    // 2. Autonomous ICM-42688 SPI Master & Telemetry Acquisition
    // -------------------------------------------------------------------------
    wire [15:0] ax, ay, az;
    wire [15:0] gx, gy, gz;
    wire        sensor_valid;
    wire        sensor_ready;

    icm42688_spi_master #(
        .STARTUP_DELAY_CYCLES(STARTUP_DELAY)
    ) u_spi_master (
        .clk              (clk),
        .rst_n            (rst_n),
        .trigger_read     (trigger_sensor_read),
        .spi_sck          (spi_sck),
        .spi_cs_n         (spi_cs_n),
        .spi_mosi         (spi_mosi),
        .spi_miso         (spi_miso),
        .accel_x          (ax),
        .accel_y          (ay),
        .accel_z          (az),
        .gyro_x           (gx),
        .gyro_y           (gy),
        .gyro_z           (gz),
        .sensor_ready     (sensor_ready),
        .data_ready_pulse (sensor_valid)
    );

    // -------------------------------------------------------------------------
    // 3. Multi-Phase Synchronous Execution Pipeline Sequencer
    // Eliminates race conditions between encoder, synapse integration, and STDP
    // -------------------------------------------------------------------------
    reg [2:0] strobe_pipe;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            strobe_pipe <= 3'b000;
        end else begin
            strobe_pipe <= {strobe_pipe[1:0], sensor_valid};
        end
    end

    wire strobe_sample = sensor_valid;      // Phase 0 (Cycle 0): Delta encoder samples sensor bus
    wire strobe_lif    = strobe_pipe[0];    // Phase 1 (Cycle 1): LIF array integrates current & fires
    wire strobe_post   = strobe_pipe[1];    // Phase 2 (Cycle 2): WTA, Anomaly Accumulator & STDP updates

    // -------------------------------------------------------------------------
    // 4. Sensor Channel Bus Mapping (Correct Endianness and Alignment)
    // -------------------------------------------------------------------------
    wire [127:0] sensor_bus = {16'd0, 16'd0, gz, gy, gx, az, ay, ax};

    // -------------------------------------------------------------------------
    // 5. Asynchronous Leaky-Reference Delta Modulation Spike Encoder
    // -------------------------------------------------------------------------
    wire [7:0] s_pre_up, s_pre_down;

    delta_encoder #(
        .CHANNELS(8),
        .WIDTH(16)
    ) u_encoder (
        .clk             (clk),
        .rst_n           (rst_n),
        .sample_valid    (strobe_sample),
        .sensor_data_bus (sensor_bus),
        .delta_th        (8'd14),
        .spikes_up       (s_pre_up),
        .spikes_down     (s_pre_down)
    );

    wire [7:0] s_pre_combined = s_pre_up | s_pre_down;

    // -------------------------------------------------------------------------
    // 6. Pre- and Post-Synaptic Eligibility Trace Engines
    // -------------------------------------------------------------------------
    wire [31:0]    s_post_bus;
    wire [8*4-1:0]  t_pre_bus;
    wire [32*4-1:0] t_post_bus;

    stdp_trace_generator #(.NODES(8)) u_tpre (
        .clk        (clk),
        .rst_n      (rst_n),
        .bio_tick   (strobe_lif),
        .spike_in   (s_pre_combined),
        .traces_out (t_pre_bus)
    );

    stdp_trace_generator #(.NODES(32)) u_tpost (
        .clk        (clk),
        .rst_n      (rst_n),
        .bio_tick   (strobe_post),
        .spike_in   (s_post_bus),
        .traces_out (t_post_bus)
    );

    // -------------------------------------------------------------------------
    // 7. 256-Synapse Plastic Crossbar (With Watchdog Reset Weights & Norm = 450.08)
    // -------------------------------------------------------------------------
    wire signed [32*12-1:0] syn_currents_bus;

    // Registers for Hardware Anomaly Classifier (Leaky-Bucket Burst Accumulator)
    reg [2:0] burst_cnt;
    reg [2:0] leak_div;
    reg       anomaly_latched;

    // Plasticity is active during baseline calibration but automatically cuts off
    // when burst_cnt >= 2 (anomaly onset pre-filter, 0.5 ms) and permanently locks LOW
    // the instant anomaly_latched asserts, protecting the learned receptive field from catastrophic forgetting
    wire effective_learn_en = learn_switch && sensor_ready && !anomaly_latched && (burst_cnt < 3'd2);

    // Pipeline latch for pre-synaptic spikes to bridge Phase 1 (integration) and Phase 2 (STDP)
    // Guarantees s_pre is active during update_strobe (strobe_post) so both LTP and LTD fire accurately
    reg [7:0] s_pre_latched;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_pre_latched <= 8'd0;
        end else if (strobe_lif) begin
            s_pre_latched <= s_pre_combined;
        end else if (strobe_post) begin
            s_pre_latched <= 8'd0;
        end
    end

    synapse_crossbar_256 u_crossbar (
        .clk             (clk),
        .rst_n           (rst_n),
        .learn_en        (effective_learn_en),
        .update_strobe   (strobe_post),
        .s_pre           (s_pre_combined),
        .s_pre_update    (s_pre_latched),
        .s_post          (s_post_bus),
        .t_pre_bus       (t_pre_bus),
        .t_post_bus      (t_post_bus),
        .syn_current_bus (syn_currents_bus)
    );

    // -------------------------------------------------------------------------
    // 8. Soft Winner-Take-All Lateral Inhibition Network
    // -------------------------------------------------------------------------
    wire [7:0]  wta_inhib_val;
    wire [31:0] wta_inhib_mask;

    lateral_inhibition u_wta (
        .s_post_bus     (s_post_bus),
        .inhib_gain     (8'd8),
        .wta_inhib_val  (wta_inhib_val),
        .wta_inhib_mask (wta_inhib_mask)
    );

    // -------------------------------------------------------------------------
    // 9. 32-Neuron Integer LIF Array with Single-Chain Blocking Arithmetic
    // -------------------------------------------------------------------------
    lif_neuron_array u_neurons (
        .clk             (clk),
        .rst_n           (rst_n),
        .eval_tick       (strobe_lif),
        .wta_tick        (strobe_post),
        .v_th            (8'd64),
        .leak_shift      (3'd3),
        .syn_current_bus (syn_currents_bus),
        .wta_inhib_val   (wta_inhib_val),
        .wta_inhib_mask  (wta_inhib_mask),
        .s_post_bus      (s_post_bus)
    );

    // -------------------------------------------------------------------------
    // 10. Hardware Anomaly Classifier (Leaky-Bucket Burst Accumulator)
    // Synchronously evaluates watchdog neuron cluster (neurons 24-31) in Phase 2
    // -------------------------------------------------------------------------
    wire watchdog_burst = |s_post_bus[31:24];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            burst_cnt       <= 3'd0;
            leak_div        <= 3'd0;
            anomaly_latched <= 1'b0;
        end else if (sensor_ready && strobe_post) begin
            // Free-running biological leak prescaler: increments unconditionally every sample step (ODR tick)
            leak_div <= leak_div + 3'd1;
            if (watchdog_burst) begin
                if (burst_cnt >= 3'd3) begin
                    burst_cnt       <= 3'd4;
                    anomaly_latched <= 1'b1;
                end else begin
                    burst_cnt <= burst_cnt + 3'd1;
                end
            end else if (burst_cnt > 3'd0 && !anomaly_latched) begin
                burst_cnt <= burst_cnt - 3'd1;
            end
        end
    end

    assign alarm_led = anomaly_latched;

    // -------------------------------------------------------------------------
    // 11. High-Speed Actuation Controller with Immediate Emergency Pulse Restart
    // -------------------------------------------------------------------------
    servo_reflex_pwm u_servo (
        .clk          (clk),
        .rst_n        (rst_n),
        .slip_trigger (anomaly_latched),
        .servo_pwm    (servo_pwm),
        .clamp_active (clamp_led)
    );

    // -------------------------------------------------------------------------
    // 12. Hardware Diagnostic Telemetry UART (115,200 Baud)
    // Transmits compact 2-byte frame: 0xAA header + status telemetry byte
    // -------------------------------------------------------------------------
    localparam [9:0] UART_DIV = 10'd104; // 12 MHz / 115200 baud = 104 cycles
    reg [9:0]  uart_clk_cnt;
    reg [3:0]  uart_bit_cnt;
    reg [9:0]  uart_tx_shift;
    reg        uart_active;
    reg [1:0]  uart_state;

    // Sticky activity registers to preserve 1-cycle spike strobes across multi-cycle UART transmission
    reg uart_s_post_latched;
    reg uart_s_pre_latched;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_s_post_latched <= 1'b0;
            uart_s_pre_latched  <= 1'b0;
        end else if (sensor_valid) begin
            uart_s_post_latched <= 1'b0;
            uart_s_pre_latched  <= 1'b0;
        end else begin
            if (|s_pre_combined) uart_s_pre_latched  <= 1'b1;
            if (|s_post_bus)     uart_s_post_latched <= 1'b1;
        end
    end

    wire [7:0] status_byte = {anomaly_latched, clamp_led, uart_s_post_latched, uart_s_pre_latched, 2'b00, burst_cnt[1:0]};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_clk_cnt  <= 10'd0;
            uart_bit_cnt  <= 4'd0;
            uart_tx_shift <= 10'h3FF;
            uart_active   <= 1'b0;
            uart_state    <= 2'd0;
        end else begin
            if (sensor_valid && !uart_active) begin
                uart_active   <= 1'b1;
                uart_state    <= 2'd0;
                uart_clk_cnt  <= 10'd0;
                uart_bit_cnt  <= 4'd0;
                uart_tx_shift <= {1'b1, 8'hAA, 1'b0}; // Frame 0: 0xAA Sync Byte
            end else if (uart_active) begin
                if (uart_clk_cnt >= UART_DIV - 1) begin
                    uart_clk_cnt  <= 10'd0;
                    uart_tx_shift <= {1'b1, uart_tx_shift[9:1]};
                    if (uart_bit_cnt >= 4'd9) begin
                        uart_bit_cnt <= 4'd0;
                        if (uart_state == 2'd0) begin
                            uart_state    <= 2'd1;
                            uart_tx_shift <= {1'b1, status_byte, 1'b0}; // Frame 1: Status Byte
                        end else begin
                            uart_active <= 1'b0;
                        end
                    end else begin
                        uart_bit_cnt <= uart_bit_cnt + 4'd1;
                    end
                end else begin
                    uart_clk_cnt <= uart_clk_cnt + 10'd1;
                end
            end
        end
    end

    assign uart_tx = uart_tx_shift[0];

endmodule
`default_nettype wire
