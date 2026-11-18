// =============================================================================
// Module: icm42688_spi_master.v
// Description: Synchronous SPI Master Interface with 6-Register Hardware Init FSM
// Configures:
//   1. GYRO_CONFIG0  (0x4F) <= 0x04 (4 kHz ODR [0x04], +/-2000 dps)
//   2. ACCEL_CONFIG0 (0x50) <= 0x04 (4 kHz ODR [0x04], +/-16g)
//   3. INT_CONFIG    (0x14) <= 0x03 (INT1: Push-Pull, Active-High, Pulsed)
//   4. INT_CONFIG1   (0x64) <= 0x40 (Bit 6=1: 8 us pulse for >=4 kHz ODR, Bit 4=0: TDK async reset fix)
//   5. INT_SOURCE0   (0x65) <= 0x08 (Route UI Data-Ready Interrupt to INT1)
//   6. PWR_MGMT0     (0x4E) <= 0x0F (Accel & Gyro Low-Noise Mode - powered up last)
// Followed by >= 50 ms startup stabilization guard before burst reads
// Reads 6-Axis Burst: Accel (X, Y, Z) and Gyro (X, Y, Z) - 12 Bytes (104 bits total)
// Standard: IEEE 1364-2001 Verilog
// =============================================================================
`default_nettype none

module icm42688_spi_master #(
    parameter [19:0] STARTUP_DELAY_CYCLES = 20'd600000 // 50 ms datasheet stabilization guard default for physical hardware (override to 20'd2400 in fast simulation)
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        trigger_read,
    output reg         spi_sck,
    output reg         spi_cs_n,
    output reg         spi_mosi,
    input  wire        spi_miso,
    output reg [15:0]  accel_x,
    output reg [15:0]  accel_y,
    output reg [15:0]  accel_z,
    output reg [15:0]  gyro_x,
    output reg [15:0]  gyro_y,
    output reg [15:0]  gyro_z,
    output reg         sensor_ready,
    output reg         data_ready_pulse
);

    localparam [3:0] INIT_LOAD_CMD   = 4'd0,
                     INIT_TX_BITS    = 4'd1,
                     INIT_HOLD_CS    = 4'd2,
                     INIT_DESELECT   = 4'd3,
                     STARTUP_GUARD   = 4'd4,
                     IDLE            = 4'd5,
                     BURST_TX_CMD    = 4'd6,
                     BURST_RX_DATA   = 4'd7,
                     BURST_HOLD_CS   = 4'd8,
                     BURST_FINISH    = 4'd9;

    reg [3:0]   state;
    reg [2:0]   cmd_idx;
    reg [6:0]   bit_cnt;
    reg [15:0]  cmd_word;
    reg [7:0]   tx_shift_reg;
    reg [103:0] rx_shift_reg;
    reg [19:0]  guard_timer;
    reg [3:0]   desel_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= INIT_LOAD_CMD;
            cmd_idx          <= 3'd0;
            spi_sck          <= 1'b1;
            spi_cs_n         <= 1'b1;
            spi_mosi         <= 1'b0;
            bit_cnt          <= 7'd0;
            cmd_word         <= 16'd0;
            tx_shift_reg     <= 8'd0;
            rx_shift_reg     <= 104'd0;
            guard_timer      <= STARTUP_DELAY_CYCLES;
            desel_cnt        <= 4'd0;
            accel_x          <= 16'd0;
            accel_y          <= 16'd0;
            accel_z          <= 16'd0;
            gyro_x           <= 16'd0;
            gyro_y           <= 16'd0;
            gyro_z           <= 16'd0;
            sensor_ready     <= 1'b0;
            data_ready_pulse <= 1'b0;
        end else begin
            case (state)
                INIT_LOAD_CMD: begin
                    spi_cs_n <= 1'b0;
                    spi_sck  <= 1'b1;
                    bit_cnt  <= 7'd15;
                    case (cmd_idx)
                        // Datasheet power-up rule: Write config registers FIRST while in Standby/Reset,
                        // and write PWR_MGMT0 LAST. Then wait >= 50 ms stabilization before any reads.
                        3'd0: cmd_word <= {8'h4F, 8'h04}; // GYRO_CONFIG0: 4 kHz ODR (0x04), +/-2000 dps
                        3'd1: cmd_word <= {8'h50, 8'h04}; // ACCEL_CONFIG0: 4 kHz ODR (0x04), +/-16g
                        3'd2: cmd_word <= {8'h14, 8'h03}; // INT_CONFIG: Push-Pull, Active-High, Pulsed
                        3'd3: cmd_word <= {8'h64, 8'h40}; // INT_CONFIG1 (0x64): Bit 6=1 (8 us pulse for >=4 kHz ODR), Bit 4=0 (TDK async reset fix)
                        3'd4: cmd_word <= {8'h65, 8'h08}; // INT_SOURCE0: Route UI Data Ready to INT1
                        3'd5: cmd_word <= {8'h4E, 8'h0F}; // PWR_MGMT0: Enable Accel & Gyro in Low-Noise Mode
                        default: cmd_word <= 16'h0000;
                    endcase
                    state <= INIT_TX_BITS;
                end

                INIT_TX_BITS: begin
                    spi_sck <= ~spi_sck;
                    if (spi_sck) begin
                        // SCK falling edge: update MOSI
                        spi_mosi <= cmd_word[bit_cnt];
                    end else begin
                        // SCK rising edge: slave samples MOSI
                        if (bit_cnt == 7'd0) begin
                            state <= INIT_HOLD_CS;
                        end else begin
                            bit_cnt <= bit_cnt - 7'd1;
                        end
                    end
                end

                INIT_HOLD_CS: begin
                    // Half-cycle hold time for the last bit before raising CS
                    spi_sck   <= 1'b1;
                    spi_cs_n  <= 1'b0;
                    desel_cnt <= 4'd4; // 4 clock cycles deselect time
                    state     <= INIT_DESELECT;
                end

                INIT_DESELECT: begin
                    spi_cs_n <= 1'b1;
                    spi_sck  <= 1'b1;
                    spi_mosi <= 1'b0;
                    if (desel_cnt > 4'd0) begin
                        desel_cnt <= desel_cnt - 4'd1;
                    end else begin
                        if (cmd_idx < 3'd5) begin
                            cmd_idx <= cmd_idx + 3'd1;
                            state   <= INIT_LOAD_CMD;
                        end else begin
                            state   <= STARTUP_GUARD;
                        end
                    end
                end

                STARTUP_GUARD: begin
                    spi_cs_n <= 1'b1;
                    spi_sck  <= 1'b1;
                    if (guard_timer > 20'd0) begin
                        guard_timer <= guard_timer - 20'd1;
                    end else begin
                        sensor_ready <= 1'b1;
                        state        <= IDLE;
                    end
                end

                IDLE: begin
                    spi_cs_n         <= 1'b1;
                    spi_sck          <= 1'b1;
                    spi_mosi         <= 1'b0;
                    data_ready_pulse <= 1'b0;
                    if (trigger_read && sensor_ready) begin
                        spi_cs_n     <= 1'b0;
                        // Read 12 bytes starting at ACCEL_DATA_X1 (Reg 0x1F | 0x80 = 0x9F)
                        // Use dedicated TX shift register to transmit exact 0x9F without bit-skipping
                        tx_shift_reg <= 8'h9F;
                        rx_shift_reg <= 104'd0;
                        bit_cnt      <= 7'd103;
                        state        <= BURST_TX_CMD;
                    end
                end

                BURST_TX_CMD, BURST_RX_DATA: begin
                    spi_sck <= ~spi_sck;
                    if (spi_sck) begin
                        // SCK falling edge: shift MOSI out
                        if (bit_cnt >= 7'd96)
                            spi_mosi <= tx_shift_reg[7];
                        else
                            spi_mosi <= 1'b0;
                    end else begin
                        // SCK rising edge: sample MISO and shift TX byte
                        if (bit_cnt >= 7'd96)
                            tx_shift_reg <= {tx_shift_reg[6:0], 1'b0};
                        rx_shift_reg <= {rx_shift_reg[102:0], spi_miso};
                        if (bit_cnt == 7'd0) begin
                            state <= BURST_HOLD_CS;
                        end else begin
                            bit_cnt <= bit_cnt - 7'd1;
                        end
                    end
                end

                BURST_HOLD_CS: begin
                    spi_sck  <= 1'b1;
                    spi_cs_n <= 1'b0;
                    state    <= BURST_FINISH;
                end

                BURST_FINISH: begin
                    spi_cs_n <= 1'b1;
                    spi_sck  <= 1'b1;
                    // Reconstruct 6-Axis Big-Endian Words:
                    // rx_shift_reg[95:0] holds 12 bytes received:
                    // Bytes 0-1: Accel X | Bytes 2-3: Accel Y | Bytes 4-5: Accel Z
                    // Bytes 6-7: Gyro X  | Bytes 8-9: Gyro Y  | Bytes 10-11: Gyro Z
                    accel_x          <= rx_shift_reg[95:80];
                    accel_y          <= rx_shift_reg[79:64];
                    accel_z          <= rx_shift_reg[63:48];
                    gyro_x           <= rx_shift_reg[47:32];
                    gyro_y           <= rx_shift_reg[31:16];
                    gyro_z           <= rx_shift_reg[15:0];
                    data_ready_pulse <= 1'b1;
                    state            <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
`default_nettype wire
