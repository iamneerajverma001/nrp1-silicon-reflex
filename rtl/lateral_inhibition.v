// =============================================================================
// Module: lateral_inhibition.v
// Description: Combinational Soft Winner-Take-All Lateral Inhibition Subtractor
// =============================================================================
`default_nettype none

module lateral_inhibition (
    input  wire [31:0] s_post_bus,
    input  wire [7:0]  inhib_gain,
    output reg  [7:0]  wta_inhib_val,
    output reg  [31:0] wta_inhib_mask
);

    always @(*) begin
        wta_inhib_val = inhib_gain;
        if (|s_post_bus) begin
            wta_inhib_mask = ~s_post_bus;
        end else begin
            wta_inhib_mask = 32'd0;
        end
    end

endmodule
`default_nettype wire
