// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Primary design header
//
// This header should be included by all source files instantiating the design.
// The class here is then constructed to instantiate the design.
// See the Verilator manual for examples.

#ifndef _VCFU_H_
#define _VCFU_H_  // guard

#include "verilated.h"

//==========

class Vcfu__Syms;

//----------

VL_MODULE(Vcfu) {
  public:
    
    // PORTS
    // The application code writes and reads these signals to
    // propagate new values into/out from the Verilated model.
    VL_IN8(clk,0,0);
    VL_OUT8(cmd_ready,0,0);
    VL_IN8(cmd_valid,0,0);
    VL_IN8(reset,0,0);
    VL_IN8(rsp_ready,0,0);
    VL_OUT8(rsp_valid,0,0);
    VL_OUT8(rst,0,0);
    VL_IN16(cmd_payload_function_id,9,0);
    VL_IN(cmd_payload_inputs_0,31,0);
    VL_IN(cmd_payload_inputs_1,31,0);
    VL_IN(port0_addr,31,0);
    VL_IN(port0_din,31,0);
    VL_IN(port1_addr,31,0);
    VL_IN(port1_din,31,0);
    VL_IN(port2_addr,31,0);
    VL_IN(port2_din,31,0);
    VL_IN(port3_addr,31,0);
    VL_IN(port3_din,31,0);
    VL_OUT(rsp_payload_outputs_0,31,0);
    
    // LOCAL SIGNALS
    // Internals; generally not touched by application code
    CData/*0:0*/ Cfu__DOT____024signal__0242;
    CData/*0:0*/ Cfu__DOT__current_function_done;
    CData/*2:0*/ Cfu__DOT__current_function_id;
    CData/*0:0*/ Cfu__DOT__fn0_done;
    CData/*1:0*/ Cfu__DOT__fsm_state;
    CData/*1:0*/ Cfu__DOT__fsm_state__024next;
    CData/*2:0*/ Cfu__DOT__stored_function_id;
    CData/*2:0*/ Cfu__DOT__stored_function_id__024next;
    CData/*0:0*/ Cfu__DOT__fn0__DOT__done__024next;
    IData/*31:0*/ Cfu__DOT__fn0_output;
    IData/*31:0*/ Cfu__DOT__stored_output;
    IData/*31:0*/ Cfu__DOT__stored_output__024next;
    IData/*31:0*/ Cfu__DOT__fn0__DOT__output__024next;
    
    // LOCAL VARIABLES
    // Internals; generally not touched by application code
    CData/*5:0*/ __Vtableidx1;
    CData/*3:0*/ __Vtableidx2;
    CData/*5:0*/ __Vtableidx3;
    CData/*0:0*/ __Vclklast__TOP__clk;
    static CData/*0:0*/ __Vtable1_Cfu__DOT____024signal__0242[64];
    static CData/*0:0*/ __Vtable2_rsp_valid[16];
    static CData/*1:0*/ __Vtable3_Cfu__DOT__fsm_state__024next[64];
    
    // INTERNAL VARIABLES
    // Internals; generally not touched by application code
    Vcfu__Syms* __VlSymsp;  // Symbol table
    
    // CONSTRUCTORS
  private:
    VL_UNCOPYABLE(Vcfu);  ///< Copying not allowed
  public:
    /// Construct the model; called by application code
    /// The special name  may be used to make a wrapper with a
    /// single model invisible with respect to DPI scope names.
    Vcfu(const char* name = "TOP");
    /// Destroy the model; called (often implicitly) by application code
    ~Vcfu();
    
    // API METHODS
    /// Evaluate the model.  Application must call when inputs change.
    void eval();
    /// Simulation complete, run final blocks.  Application must call on completion.
    void final();
    
    // INTERNAL METHODS
  private:
    static void _eval_initial_loop(Vcfu__Syms* __restrict vlSymsp);
  public:
    void __Vconfigure(Vcfu__Syms* symsp, bool first);
  private:
    static QData _change_request(Vcfu__Syms* __restrict vlSymsp);
  public:
    static void _combo__TOP__2(Vcfu__Syms* __restrict vlSymsp);
    static void _combo__TOP__5(Vcfu__Syms* __restrict vlSymsp);
  private:
    void _ctor_var_reset() VL_ATTR_COLD;
  public:
    static void _eval(Vcfu__Syms* __restrict vlSymsp);
  private:
#ifdef VL_DEBUG
    void _eval_debug_assertions();
#endif  // VL_DEBUG
  public:
    static void _eval_initial(Vcfu__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _eval_settle(Vcfu__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _initial__TOP__1(Vcfu__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _sequent__TOP__4(Vcfu__Syms* __restrict vlSymsp);
    static void _settle__TOP__3(Vcfu__Syms* __restrict vlSymsp) VL_ATTR_COLD;
} VL_ATTR_ALIGNED(VL_CACHE_LINE_BYTES);

//----------


#endif  // guard
