// =============================================================================
// Module: synapse_crossbar_256.v
// Description: 8-Input to 32-Neuron Parallel Synapse Matrix with Watchdog Weights
// Standard: IEEE 1364-2001 Verilog (Pure 1D Packed Ports for Universal Synthesis)
// =============================================================================
`default_nettype none

module synapse_crossbar_256 (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      learn_en,
    input  wire                      update_strobe,   // Cycle 2: Execute STDP weight updates
    input  wire [7:0]                s_pre,           // Cycle 1: Pre-synaptic spikes for current integration
    input  wire [7:0]                s_pre_update,    // Latched pre-synaptic spikes for STDP update phase
    input  wire [31:0]               s_post,
    input  wire [8*4-1:0]            t_pre_bus,
    input  wire [32*4-1:0]           t_post_bus,
    output wire signed [32*12-1:0]   syn_current_bus
);

    genvar in_idx, out_idx;
    generate
        for (out_idx = 0; out_idx < 32; out_idx = out_idx + 1) begin : NEURON_COLUMN
            wire signed [7:0] syn_w [0:7];
            wire signed [11:0] weighted_inputs [0:7];

            // Neurons 0..23 adapt via STDP; Neurons 24..31 are calibrated watchdog guards
            wire col_learn_en = (out_idx < 24) ? (learn_en && update_strobe) : 1'b0;

            for (in_idx = 0; in_idx < 8; in_idx = in_idx + 1) begin : SYNAPSE_ELEMENT
                // Parameterize initial weight:
                // Neurons 0-23: Initialized to +32 for adaptive baseline entrainment
                // Neurons 24-31 (Watchdogs): Diverse orthogonal receptive fields across bearing defect modes
                // Norm: sqrt(196608 + 5960) = 450.08
                localparam signed [7:0] INIT_VAL = 
                    (out_idx < 24) ? 8'sd32 :
                    (out_idx == 24 && in_idx == 2) ? 8'sd28 :
                    (out_idx == 25 && in_idx == 2) ? 8'sd24 :
                    (out_idx == 26 && in_idx == 2) ? 8'sd20 :
                    (out_idx == 27 && in_idx == 5) ? 8'sd28 :
                    (out_idx == 28 && in_idx == 5) ? 8'sd24 :
                    (out_idx == 29 && (in_idx == 2 || in_idx == 5)) ? 8'sd22 :
                    (out_idx == 30 && in_idx == 3) ? 8'sd18 :
                    (out_idx == 30 && in_idx == 5) ? 8'sd22 :
                    (out_idx == 31 && in_idx == 0) ? 8'sd16 :
                    (out_idx == 31 && in_idx == 2) ? 8'sd22 :
                    (out_idx == 31 && in_idx == 5) ? 8'sd18 : 8'sd0;

                stdp_synapse_unit #(
                    .INIT_WEIGHT(INIT_VAL)
                ) u_syn (
                    .clk           (clk),
                    .rst_n         (rst_n),
                    .learn_en      (col_learn_en),
                    .s_pre         (s_pre_update[in_idx]),
                    .s_post        (s_post[out_idx]),
                    .t_pre         (t_pre_bus[in_idx*4 +: 4]),
                    .t_post        (t_post_bus[out_idx*4 +: 4]),
                    .weight_wr_en  (1'b0),
                    .weight_wr_val (8'sd0),
                    .weight_out    (syn_w[in_idx])
                );

                assign weighted_inputs[in_idx] = s_pre[in_idx] ? 
                                                 {{4{syn_w[in_idx][7]}}, syn_w[in_idx]} : 12'sd0;
            end

            wire signed [11:0] col_sum = weighted_inputs[0] + weighted_inputs[1] +
                                         weighted_inputs[2] + weighted_inputs[3] +
                                         weighted_inputs[4] + weighted_inputs[5] +
                                         weighted_inputs[6] + weighted_inputs[7];

            assign syn_current_bus[out_idx*12 +: 12] = col_sum;
        end
    endgenerate

endmodule
`default_nettype wire
