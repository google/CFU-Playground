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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/kws_micro_accel/cfu.sv", 19, "",
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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/kws_micro_accel/cfu.sv", 19, "",
                "Verilated model didn't DC converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

VL_INLINE_OPT void Vcfu::_combo__TOP__1(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_combo__TOP__1\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    IData/*31:0*/ __Vtemp1;
    // Body
    vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods = VL_EXTENDS_II(32,16, 
                                                              (0xffffU 
                                                               & VL_MULS_III(16,16,16, 
                                                                             (0xffffU 
                                                                              & (VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_0)) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,9, 
                                                                                ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                                             (0xffffU 
                                                                              & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_1))))));
    if ((8U & (IData)(vlTOPp->cmd_payload_function_id))) {
        __Vtemp1 = (vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods 
                    + ((VL_EXTENDS_II(32,16, (0xffffU 
                                              & VL_MULS_III(16,16,16, 
                                                            (0xffffU 
                                                             & (VL_EXTENDS_II(16,8, 
                                                                              (0xffU 
                                                                               & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 8U))) 
                                                                + 
                                                                VL_EXTENDS_II(16,9, 
                                                                              ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                ? 0x1adU
                                                                                : 0x80U)))), 
                                                            (0xffffU 
                                                             & VL_EXTENDS_II(16,8, 
                                                                             (0xffU 
                                                                              & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 8U))))))) 
                        + VL_EXTENDS_II(32,16, (0xffffU 
                                                & VL_MULS_III(16,16,16, 
                                                              (0xffffU 
                                                               & (VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x10U))) 
                                                                  + 
                                                                  VL_EXTENDS_II(16,9, 
                                                                                ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                              (0xffffU 
                                                               & VL_EXTENDS_II(16,8, 
                                                                               (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x10U)))))))) 
                       + VL_EXTENDS_II(32,16, (0xffffU 
                                               & VL_MULS_III(16,16,16, 
                                                             (0xffffU 
                                                              & (VL_EXTENDS_II(16,8, 
                                                                               (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x18U))) 
                                                                 + 
                                                                 VL_EXTENDS_II(16,9, 
                                                                               ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                             (0xffffU 
                                                              & VL_EXTENDS_II(16,8, 
                                                                              (0xffU 
                                                                               & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x18U)))))))));
        vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods = __Vtemp1;
    }
}

void Vcfu::_settle__TOP__2(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_settle__TOP__2\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    IData/*31:0*/ __Vtemp2;
    // Body
    vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods = VL_EXTENDS_II(32,16, 
                                                              (0xffffU 
                                                               & VL_MULS_III(16,16,16, 
                                                                             (0xffffU 
                                                                              & (VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_0)) 
                                                                                + 
                                                                                VL_EXTENDS_II(16,9, 
                                                                                ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                                             (0xffffU 
                                                                              & VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & vlTOPp->cmd_payload_inputs_1))))));
    if ((8U & (IData)(vlTOPp->cmd_payload_function_id))) {
        __Vtemp2 = (vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods 
                    + ((VL_EXTENDS_II(32,16, (0xffffU 
                                              & VL_MULS_III(16,16,16, 
                                                            (0xffffU 
                                                             & (VL_EXTENDS_II(16,8, 
                                                                              (0xffU 
                                                                               & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 8U))) 
                                                                + 
                                                                VL_EXTENDS_II(16,9, 
                                                                              ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                ? 0x1adU
                                                                                : 0x80U)))), 
                                                            (0xffffU 
                                                             & VL_EXTENDS_II(16,8, 
                                                                             (0xffU 
                                                                              & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 8U))))))) 
                        + VL_EXTENDS_II(32,16, (0xffffU 
                                                & VL_MULS_III(16,16,16, 
                                                              (0xffffU 
                                                               & (VL_EXTENDS_II(16,8, 
                                                                                (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x10U))) 
                                                                  + 
                                                                  VL_EXTENDS_II(16,9, 
                                                                                ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                              (0xffffU 
                                                               & VL_EXTENDS_II(16,8, 
                                                                               (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x10U)))))))) 
                       + VL_EXTENDS_II(32,16, (0xffffU 
                                               & VL_MULS_III(16,16,16, 
                                                             (0xffffU 
                                                              & (VL_EXTENDS_II(16,8, 
                                                                               (0xffU 
                                                                                & (vlTOPp->cmd_payload_inputs_0 
                                                                                >> 0x18U))) 
                                                                 + 
                                                                 VL_EXTENDS_II(16,9, 
                                                                               ((0x10U 
                                                                                & (IData)(vlTOPp->cmd_payload_function_id))
                                                                                 ? 0x1adU
                                                                                 : 0x80U)))), 
                                                             (0xffffU 
                                                              & VL_EXTENDS_II(16,8, 
                                                                              (0xffU 
                                                                               & (vlTOPp->cmd_payload_inputs_1 
                                                                                >> 0x18U)))))))));
        vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods = __Vtemp2;
    }
    vlTOPp->cmd_ready = (1U & (~ (IData)(vlTOPp->rsp_valid)));
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift = ((4U 
                                                  & vlTOPp->cmd_payload_inputs_1)
                                                  ? 
                                                 ((2U 
                                                   & vlTOPp->cmd_payload_inputs_1)
                                                   ? 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 9U
                                                    : 6U)
                                                   : 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 7U
                                                    : 8U))
                                                  : 
                                                 ((2U 
                                                   & vlTOPp->cmd_payload_inputs_1)
                                                   ? 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 5U
                                                    : 6U)
                                                   : 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 7U
                                                    : 8U)));
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask = (~ ((IData)(0xffffffffU) 
                                                   << (IData)(vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift)));
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__remainder = 
        (vlTOPp->rsp_payload_outputs_0 & vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask);
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__threshold = 
        ((vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask 
          >> 1U) + (1U & (vlTOPp->rsp_payload_outputs_0 
                          >> 0x1fU)));
    vlTOPp->Cfu__DOT__rcdbpot_output = VL_SHIFTRS_III(32,32,4, vlTOPp->rsp_payload_outputs_0, (IData)(vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift));
    if (VL_GTS_III(1,32,32, vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__remainder, vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__threshold)) {
        vlTOPp->Cfu__DOT__rcdbpot_output = ((IData)(1U) 
                                            + vlTOPp->Cfu__DOT__rcdbpot_output);
    }
    if ((0x80000000U & vlTOPp->Cfu__DOT__rcdbpot_output)) {
        vlTOPp->Cfu__DOT__rcdbpot_output = 0U;
    } else {
        if ((0U != (0xffffffU & (vlTOPp->Cfu__DOT__rcdbpot_output 
                                 >> 8U)))) {
            vlTOPp->Cfu__DOT__rcdbpot_output = 0xffU;
        }
    }
    vlTOPp->Cfu__DOT__rcdbpot_output = (vlTOPp->Cfu__DOT__rcdbpot_output 
                                        - (IData)(0x80U));
    vlTOPp->Cfu__DOT__mac_output = (vlTOPp->rsp_payload_outputs_0 
                                    + vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods);
}

VL_INLINE_OPT void Vcfu::_sequent__TOP__3(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_sequent__TOP__3\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    CData/*0:0*/ __Vdly__rsp_valid;
    // Body
    __Vdly__rsp_valid = vlTOPp->rsp_valid;
    if (vlTOPp->reset) {
        __Vdly__rsp_valid = 0U;
    } else {
        if (vlTOPp->rsp_valid) {
            __Vdly__rsp_valid = (1U & (~ (IData)(vlTOPp->rsp_ready)));
        } else {
            if (vlTOPp->cmd_valid) {
                __Vdly__rsp_valid = 1U;
            }
        }
    }
    if (vlTOPp->cmd_valid) {
        vlTOPp->rsp_payload_outputs_0 = ((1U == (1U 
                                                 & (IData)(vlTOPp->cmd_payload_function_id)))
                                          ? vlTOPp->Cfu__DOT__mac_output
                                          : ((2U == 
                                              (2U & (IData)(vlTOPp->cmd_payload_function_id)))
                                              ? (IData)(
                                                        ((VL_ULL(0x40000000) 
                                                          + 
                                                          (((QData)((IData)(vlTOPp->cmd_payload_inputs_0)) 
                                                            << 0x20U) 
                                                           | (QData)((IData)(vlTOPp->cmd_payload_inputs_1)))) 
                                                         >> 0x1fU))
                                              : ((4U 
                                                  == 
                                                  (4U 
                                                   & (IData)(vlTOPp->cmd_payload_function_id)))
                                                  ? vlTOPp->Cfu__DOT__rcdbpot_output
                                                  : 0U)));
    }
    vlTOPp->rsp_valid = __Vdly__rsp_valid;
    vlTOPp->cmd_ready = (1U & (~ (IData)(vlTOPp->rsp_valid)));
}

VL_INLINE_OPT void Vcfu::_combo__TOP__4(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_combo__TOP__4\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->Cfu__DOT__mac_output = (vlTOPp->rsp_payload_outputs_0 
                                    + vlTOPp->Cfu__DOT__kws_mac__DOT__sum_prods);
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift = ((4U 
                                                  & vlTOPp->cmd_payload_inputs_1)
                                                  ? 
                                                 ((2U 
                                                   & vlTOPp->cmd_payload_inputs_1)
                                                   ? 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 9U
                                                    : 6U)
                                                   : 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 7U
                                                    : 8U))
                                                  : 
                                                 ((2U 
                                                   & vlTOPp->cmd_payload_inputs_1)
                                                   ? 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 5U
                                                    : 6U)
                                                   : 
                                                  ((1U 
                                                    & vlTOPp->cmd_payload_inputs_1)
                                                    ? 7U
                                                    : 8U)));
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask = (~ ((IData)(0xffffffffU) 
                                                   << (IData)(vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift)));
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__remainder = 
        (vlTOPp->rsp_payload_outputs_0 & vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask);
    vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__threshold = 
        ((vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__mask 
          >> 1U) + (1U & (vlTOPp->rsp_payload_outputs_0 
                          >> 0x1fU)));
    vlTOPp->Cfu__DOT__rcdbpot_output = VL_SHIFTRS_III(32,32,4, vlTOPp->rsp_payload_outputs_0, (IData)(vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__shift));
    if (VL_GTS_III(1,32,32, vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__remainder, vlTOPp->Cfu__DOT__kws_rcdbpot__DOT__threshold)) {
        vlTOPp->Cfu__DOT__rcdbpot_output = ((IData)(1U) 
                                            + vlTOPp->Cfu__DOT__rcdbpot_output);
    }
    if ((0x80000000U & vlTOPp->Cfu__DOT__rcdbpot_output)) {
        vlTOPp->Cfu__DOT__rcdbpot_output = 0U;
    } else {
        if ((0U != (0xffffffU & (vlTOPp->Cfu__DOT__rcdbpot_output 
                                 >> 8U)))) {
            vlTOPp->Cfu__DOT__rcdbpot_output = 0xffU;
        }
    }
    vlTOPp->Cfu__DOT__rcdbpot_output = (vlTOPp->Cfu__DOT__rcdbpot_output 
                                        - (IData)(0x80U));
}

void Vcfu::_eval(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_combo__TOP__1(vlSymsp);
    if (((IData)(vlTOPp->clk) & (~ (IData)(vlTOPp->__Vclklast__TOP__clk)))) {
        vlTOPp->_sequent__TOP__3(vlSymsp);
    }
    vlTOPp->_combo__TOP__4(vlSymsp);
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
    if (VL_UNLIKELY((clk & 0xfeU))) {
        Verilated::overWidthError("clk");}
    if (VL_UNLIKELY((reset & 0xfeU))) {
        Verilated::overWidthError("reset");}
    if (VL_UNLIKELY((cmd_payload_function_id & 0xfc00U))) {
        Verilated::overWidthError("cmd_payload_function_id");}
    if (VL_UNLIKELY((cmd_valid & 0xfeU))) {
        Verilated::overWidthError("cmd_valid");}
    if (VL_UNLIKELY((rsp_ready & 0xfeU))) {
        Verilated::overWidthError("rsp_ready");}
}
#endif  // VL_DEBUG

void Vcfu::_ctor_var_reset() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_ctor_var_reset\n"); );
    // Body
    clk = VL_RAND_RESET_I(1);
    reset = VL_RAND_RESET_I(1);
    cmd_payload_function_id = VL_RAND_RESET_I(10);
    cmd_payload_inputs_0 = VL_RAND_RESET_I(32);
    cmd_payload_inputs_1 = VL_RAND_RESET_I(32);
    rsp_payload_outputs_0 = VL_RAND_RESET_I(32);
    cmd_valid = VL_RAND_RESET_I(1);
    cmd_ready = VL_RAND_RESET_I(1);
    rsp_valid = VL_RAND_RESET_I(1);
    rsp_ready = VL_RAND_RESET_I(1);
    Cfu__DOT__mac_output = VL_RAND_RESET_I(32);
    Cfu__DOT__rcdbpot_output = VL_RAND_RESET_I(32);
    Cfu__DOT__kws_mac__DOT__sum_prods = VL_RAND_RESET_I(32);
    Cfu__DOT__kws_rcdbpot__DOT__shift = VL_RAND_RESET_I(4);
    Cfu__DOT__kws_rcdbpot__DOT__mask = VL_RAND_RESET_I(32);
    Cfu__DOT__kws_rcdbpot__DOT__remainder = VL_RAND_RESET_I(32);
    Cfu__DOT__kws_rcdbpot__DOT__threshold = VL_RAND_RESET_I(32);
}
