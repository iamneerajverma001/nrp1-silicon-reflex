// =============================================================================
// Module: stdp_synapse_unit.v
// Description: Signed 8-Bit Plastic Synapse Unit with 9-Bit Saturating Arithmetic
// Standard: IEEE 1364-2001 Verilog
// =============================================================================
`default_nettype none

module stdp_synapse_unit #(
    parameter signed [7:0] INIT_WEIGHT = 8'sd32
)(
    input  wire              clk,
    input  wire              rst_n,
    input  wire              learn_en,
    input  wire              s_pre,
    input  wire              s_post,
    input  wire [3:0]        t_pre,
    input  wire [3:0]        t_post,
    input  wire              weight_wr_en,
    input  wire signed [7:0] weight_wr_val,
    output reg  signed [7:0] weight_out
);

    wire signed [7:0] ltp_step = $signed({4'd0, t_pre[3:1]});
    wire signed [7:0] ltd_step = $signed({4'd0, t_post[3:1]});

    // Sign-extended 9-bit intermediate operands to prevent two's complement wrap-around
    wire signed [8:0] sum_ltp  = {weight_out[7], weight_out} + {ltp_step[7], ltp_step};
    wire signed [8:0] diff_ltd = {weight_out[7], weight_out} - {ltd_step[7], ltd_step};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            weight_out <= INIT_WEIGHT;
        end else if (weight_wr_en) begin
            weight_out <= weight_wr_val;
        end else if (learn_en) begin
            if (s_post) begin
                // Causal LTP: Postsynaptic spike fires -> potentiate by presynaptic trace t_pre
                // Dropping !s_pre ensures causal coincident pairs (s_pre and s_post in same step) receive full LTP
                if (sum_ltp > 9'sd127)
                    weight_out <= 8'sd127;
                else
                    weight_out <= sum_ltp[7:0];
            end else if (s_pre) begin
                // Acausal LTD: Presynaptic spike arrives without postsynaptic response -> depress by postsynaptic trace t_post
                if (diff_ltd < -9'sd128)
                    weight_out <= -8'sd128;
                else
                    weight_out <= diff_ltd[7:0];
            end
        end
    end

endmodule
`default_nettype wire
