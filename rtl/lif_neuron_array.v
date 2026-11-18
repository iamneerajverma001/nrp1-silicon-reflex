// =============================================================================
// Module: lif_neuron_array.v
// Description: 32 Integer LIF Neurons with Pipelined Evaluation & Lateral Inhibition
// Standard: IEEE 1364-2001 Verilog (Pure 1D Packed Ports for Universal Synthesis)
// =============================================================================
`default_nettype none

module lif_neuron_array (
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire                     eval_tick,        // Cycle 1: Synaptic integration & fire
    input  wire                     wta_tick,         // Cycle 2: Lateral inhibition update
    input  wire [7:0]               v_th,
    input  wire [2:0]               leak_shift,
    input  wire signed [32*12-1:0]  syn_current_bus,  // 1D packed bus for Verilog-2001 compatibility
    input  wire signed [7:0]        wta_inhib_val,
    input  wire [31:0]              wta_inhib_mask,
    output reg  [31:0]              s_post_bus
);

    reg signed [15:0] v_membrane [0:31];
    reg [1:0]         refractory_cnt [0:31]; // Counts evaluation steps, NOT raw clock cycles
    integer i;

    // Unpack 1D syn_current_bus
    wire signed [11:0] syn_current [0:31];
    genvar g;
    generate
        for (g = 0; g < 32; g = g + 1) begin : UNPACK_CURRENT
            assign syn_current[g] = syn_current_bus[g*12 +: 12];
        end
    endgenerate

    // Temporary variables for blocking arithmetic evaluation
    reg signed [16:0] v_next;
    reg signed [16:0] leak_val;
    reg signed [16:0] v_wta;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_post_bus <= 32'd0;
            for (i = 0; i < 32; i = i + 1) begin
                v_membrane[i]     <= 16'sd0;
                refractory_cnt[i] <= 2'd0;
            end
        end else if (eval_tick) begin
            // Phase 1: Synaptic Integration, Threshold Comparison, and Floor Leak
            for (i = 0; i < 32; i = i + 1) begin
                if (refractory_cnt[i] > 2'd0) begin
                    refractory_cnt[i] <= refractory_cnt[i] - 2'd1;
                    s_post_bus[i]     <= 1'b0;
                end else begin
                    // Compute next potential using single blocking arithmetic chain
                    v_next = $signed(v_membrane[i]) + $signed({{5{syn_current[i][11]}}, syn_current[i]});

                    if (v_next >= $signed({9'd0, v_th})) begin
                        s_post_bus[i]     <= 1'b1;
                        v_membrane[i]     <= 16'sd0; // Hard reset to resting potential
                        refractory_cnt[i] <= 2'd3;   // Lock out for 3 evaluation steps (750 us at 4 kHz)
                    end else begin
                        s_post_bus[i] <= 1'b0;

                        // Floor leak towards resting potential (0)
                        if (v_next > 17'sd0) begin
                            leak_val = v_next >>> leak_shift;
                            v_next   = v_next - ((leak_val != 17'sd0) ? leak_val : 17'sd1);
                        end else if (v_next < 17'sd0) begin
                            v_next = 17'sd0; // Clamp against negative hyperpolarization
                        end

                        v_membrane[i] <= v_next[15:0];
                    end
                end
            end
        end else if (wta_tick) begin
            // Phase 2: Soft Winner-Take-All Lateral Inhibition Subtraction
            for (i = 0; i < 32; i = i + 1) begin
                if (wta_inhib_mask[i] && !s_post_bus[i]) begin
                    v_wta = $signed(v_membrane[i]) - $signed({9'd0, wta_inhib_val});
                    v_membrane[i] <= (v_wta > 17'sd0) ? v_wta[15:0] : 16'sd0;
                end
            end
        end else begin
            // Post-synaptic spike is held active through Phase 2, then cleared
            s_post_bus <= 32'd0;
        end
    end

endmodule
`default_nettype wire
