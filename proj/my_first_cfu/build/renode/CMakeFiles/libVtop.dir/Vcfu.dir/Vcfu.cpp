// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcfu.h for the primary calling header

#include "Vcfu.h"
#include "Vcfu__Syms.h"

//==========

VL_CTOR_IMP(Vcfu) {
    Vcfu__Syms* __restrict vlSymsp = __VlSymsp = new Vcfu__Syms(this, name());
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Reset internal values
    
    // Reset structure values
    _ctor_var_reset();
}

void Vcfu::__Vconfigure(Vcfu__Syms* vlSymsp, bool first) {
    if (0 && first) {}  // Prevent unused
    this->__VlSymsp = vlSymsp;
}

Vcfu::~Vcfu() {
    delete __VlSymsp; __VlSymsp=NULL;
}

void Vcfu::eval() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcfu::eval\n"); );
    Vcfu__Syms* __restrict vlSymsp = this->__VlSymsp;  // Setup global symbol table
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
#ifdef VL_DEBUG
    // Debug assertions
    _eval_debug_assertions();
#endif  // VL_DEBUG
    // Initialize
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) _eval_initial_loop(vlSymsp);
    // Evaluate till stable
    int __VclockLoop = 0;
    QData __Vchange = 1;
    do {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Clock loop\n"););
        _eval(vlSymsp);
        if (VL_UNLIKELY(++__VclockLoop > 100)) {
            // About to fail, so enable debug to see what's not settling.
            // Note you must run make with OPT=-DVL_DEBUG for debug prints.
            int __Vsaved_debug = Verilated::debug();
            Verilated::debug(1);
            __Vchange = _change_request(vlSymsp);
            Verilated::debug(__Vsaved_debug);
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/my_first_cfu/cfu.v", 1, "",
                "Verilated model didn't converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

void Vcfu::_eval_initial_loop(Vcfu__Syms* __restrict vlSymsp) {
    vlSymsp->__Vm_didInit = true;
    _eval_initial(vlSymsp);
    // Evaluate till stable
    int __VclockLoop = 0;
    QData __Vchange = 1;
    do {
        _eval_settle(vlSymsp);
        _eval(vlSymsp);
        if (VL_UNLIKELY(++__VclockLoop > 100)) {
            // About to fail, so enable debug to see what's not settling.
            // Note you must run make with OPT=-DVL_DEBUG for debug prints.
            int __Vsaved_debug = Verilated::debug();
            Verilated::debug(1);
            __Vchange = _change_request(vlSymsp);
            Verilated::debug(__Vsaved_debug);
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/my_first_cfu/cfu.v", 1, "",
                "Verilated model didn't DC converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

VL_INLINE_OPT void Vcfu::_sequent__TOP__1(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_sequent__TOP__1\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    CData/*0:0*/ __Vdly__rsp_valid;
    IData/*31:0*/ __Vdly__rsp_payload_outputs_0;
    // Body
    __Vdly__rsp_payload_outputs_0 = vlTOPp->rsp_payload_outputs_0;
    __Vdly__rsp_valid = vlTOPp->rsp_valid;
    if (vlTOPp->reset) {
        __Vdly__rsp_payload_outputs_0 = 0U;
        __Vdly__rsp_valid = 0U;
    } else {
        if (vlTOPp->rsp_valid) {
            __Vdly__rsp_valid = (1U & (~ (IData)(vlTOPp->rsp_ready)));
        } else {
            if (vlTOPp->cmd_valid) {
                __Vdly__rsp_payload_outputs_0 = ((0U 
                                                  != 
                                                  (0x7fU 
                                                   & ((IData)(vlTOPp->cmd_payload_function_id) 
                                                      >> 3U)))
                                                  ? 0U
                                                  : 
                                                 (vlTOPp->rsp_payload_outputs_0 
                                                  + 
                                                  (((VL_EXTENDS_II(32,16, 
                                                                   (0xffffU 
                                                                    & VL_MULS_III(16,16,16, 
                                                                                (0xffffU 
                                                                                & ((IData)(0x80U) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_0)))), 
                                                                                (0xffffU 
                                                                                & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_1)))))) 
                                                     + 
                                                     VL_EXTENDS_II(32,16, 
                                                                   (0xffffU 
                                                                    & VL_MULS_III(16,16,16, 
                                                                                (0xffffU 
                                                                                & ((IData)(0x80U) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 8U))))), 
                                                                                (0xffffU 
                                                                                & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 8U)))))))) 
                                                    + 
                                                    VL_EXTENDS_II(32,16, 
                                                                  (0xffffU 
                                                                   & VL_MULS_III(16,16,16, 
                                                                                (0xffffU 
                                                                                & ((IData)(0x80U) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x10U))))), 
                                                                                (0xffffU 
                                                                                & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x10U)))))))) 
                                                   + 
                                                   VL_EXTENDS_II(32,16, 
                                                                 (0xffffU 
                                                                  & VL_MULS_III(16,16,16, 
                                                                                (0xffffU 
                                                                                & ((IData)(0x80U) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x18U))))), 
                                                                                (0xffffU 
                                                                                & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x18U))))))))));
                __Vdly__rsp_valid = 1U;
            }
        }
    }
    vlTOPp->rsp_payload_outputs_0 = __Vdly__rsp_payload_outputs_0;
    vlTOPp->rsp_valid = __Vdly__rsp_valid;
    vlTOPp->cmd_ready = (1U & (~ (IData)(vlTOPp->rsp_valid)));
}

void Vcfu::_settle__TOP__2(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_settle__TOP__2\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->cmd_ready = (1U & (~ (IData)(vlTOPp->rsp_valid)));
}

void Vcfu::_eval(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    if (((IData)(vlTOPp->clk) & (~ (IData)(vlTOPp->__Vclklast__TOP__clk)))) {
        vlTOPp->_sequent__TOP__1(vlSymsp);
    }
    // Final
    vlTOPp->__Vclklast__TOP__clk = vlTOPp->clk;
}

void Vcfu::_eval_initial(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval_initial\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->__Vclklast__TOP__clk = vlTOPp->clk;
}

void Vcfu::final() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::final\n"); );
    // Variables
    Vcfu__Syms* __restrict vlSymsp = this->__VlSymsp;
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
}

void Vcfu::_eval_settle(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval_settle\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_settle__TOP__2(vlSymsp);
}

VL_INLINE_OPT QData Vcfu::_change_request(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_change_request\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    // Change detection
    QData __req = false;  // Logically a bool
    return __req;
}

#ifdef VL_DEBUG
void Vcfu::_eval_debug_assertions() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval_debug_assertions\n"); );
    // Body
    if (VL_UNLIKELY((cmd_valid & 0xfeU))) {
        Verilated::overWidthError("cmd_valid");}
    if (VL_UNLIKELY((cmd_payload_function_id & 0xfc00U))) {
        Verilated::overWidthError("cmd_payload_function_id");}
    if (VL_UNLIKELY((rsp_ready & 0xfeU))) {
        Verilated::overWidthError("rsp_ready");}
    if (VL_UNLIKELY((reset & 0xfeU))) {
        Verilated::overWidthError("reset");}
    if (VL_UNLIKELY((clk & 0xfeU))) {
        Verilated::overWidthError("clk");}
}
#endif  // VL_DEBUG

void Vcfu::_ctor_var_reset() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_ctor_var_reset\n"); );
    // Body
    cmd_valid = VL_RAND_RESET_I(1);
    cmd_ready = VL_RAND_RESET_I(1);
    cmd_payload_function_id = VL_RAND_RESET_I(10);
    cmd_payload_inputs_0 = VL_RAND_RESET_I(32);
    cmd_payload_inputs_1 = VL_RAND_RESET_I(32);
    rsp_valid = VL_RAND_RESET_I(1);
    rsp_ready = VL_RAND_RESET_I(1);
    rsp_payload_outputs_0 = VL_RAND_RESET_I(32);
    reset = VL_RAND_RESET_I(1);
    clk = VL_RAND_RESET_I(1);
}
