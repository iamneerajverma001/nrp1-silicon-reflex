// =============================================================================
// Module: stdp_trace_generator.v
// Description: Multiplier-Less Shift-Register Eligibility Trace Engine
// =============================================================================
`default_nettype none

module stdp_trace_generator #(
    parameter integer NODES = 8
)(
    input  wire               clk,
    input  wire               rst_n,
    input  wire               bio_tick,
    input  wire [NODES-1:0]   spike_in,
    output reg  [NODES*4-1:0] traces_out
);

    reg [3:0] trace_regs [0:NODES-1];
    integer i;

    genvar g;
    generate
        for (g = 0; g < NODES; g = g + 1) begin : PACK_OUTPUTS
            always @(*) traces_out[g*4 +: 4] = trace_regs[g];
        end
    endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < NODES; i = i + 1) begin
                trace_regs[i] <= 4'd0;
            end
        end else begin
            for (i = 0; i < NODES; i = i + 1) begin
                if (spike_in[i]) begin
                    trace_regs[i] <= 4'd15;
                end else if (bio_tick && (trace_regs[i] > 4'd0)) begin
                    trace_regs[i] <= trace_regs[i] - ((trace_regs[i] >> 2) != 4'd0 ? (trace_regs[i] >> 2) : 4'd1);
                end
            end
        end
    end

endmodule
`default_nettype wire
