// =============================================================================
// Module: delta_encoder.v
// Description: Platform-Agnostic 8-Channel Dynamic Delta Modulator with Leaky DC Reference
// Compatibility: Xilinx Vivado (Artix/Spartan) / Yosys (iCE40) / OpenLane 2 (Sky130)
// =============================================================================
`default_nettype none

module delta_encoder #(
    parameter integer CHANNELS = 8,
    parameter integer WIDTH    = 16
)(
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      sample_valid,
    input  wire [CHANNELS*WIDTH-1:0] sensor_data_bus,
    input  wire [7:0]                delta_th,
    output reg  [CHANNELS-1:0]       spikes_up,
    output reg  [CHANNELS-1:0]       spikes_down
);

    reg signed [WIDTH-1:0] v_ref [0:CHANNELS-1];
    reg                    initialized;
    integer i;

    wire signed [WIDTH-1:0] channel_data [0:CHANNELS-1];
    // 17-Bit Sign-Extended Subtraction to eliminate Section 4.5 wrap-around cliff & directional inversion
    wire signed [WIDTH:0]   diff_ext     [0:CHANNELS-1];
    genvar g;
    generate
        for (g = 0; g < CHANNELS; g = g + 1) begin : UNPACK_INPUTS
            assign channel_data[g] = sensor_data_bus[g*WIDTH +: WIDTH];
            assign diff_ext[g]     = {channel_data[g][WIDTH-1], channel_data[g]} - 
                                     {v_ref[g][WIDTH-1], v_ref[g]};
        end
    endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spikes_up   <= {CHANNELS{1'b0}};
            spikes_down <= {CHANNELS{1'b0}};
            initialized <= 1'b0;
            for (i = 0; i < CHANNELS; i = i + 1) begin
                v_ref[i] <= {WIDTH{1'b0}};
            end
        end else if (sample_valid) begin
            if (!initialized) begin
                // Preload DC baseline reference on first sample to prevent power-up spike surge
                initialized <= 1'b1;
                spikes_up   <= {CHANNELS{1'b0}};
                spikes_down <= {CHANNELS{1'b0}};
                for (i = 0; i < CHANNELS; i = i + 1) begin
                    v_ref[i] <= channel_data[i];
                end
            end else begin
                for (i = 0; i < CHANNELS; i = i + 1) begin
                    if (diff_ext[i] >= $signed({9'd0, delta_th})) begin
                        spikes_up[i]   <= 1'b1;
                        spikes_down[i] <= 1'b0;
                        v_ref[i]       <= v_ref[i] + $signed({8'd0, delta_th}) + 
                                          $signed(diff_ext[i] >>> 4);
                    end else if (diff_ext[i] <= -$signed({9'd0, delta_th})) begin
                        spikes_up[i]   <= 1'b0;
                        spikes_down[i] <= 1'b1;
                        v_ref[i]       <= v_ref[i] - $signed({8'd0, delta_th}) + 
                                          $signed(diff_ext[i] >>> 4);
                    end else begin
                        spikes_up[i]   <= 1'b0;
                        spikes_down[i] <= 1'b0;
                        v_ref[i]       <= v_ref[i] + $signed(diff_ext[i] >>> 4);
                    end
                end
            end
        end else begin
            spikes_up   <= {CHANNELS{1'b0}};
            spikes_down <= {CHANNELS{1'b0}};
        end
    end

endmodule
`default_nettype wire
