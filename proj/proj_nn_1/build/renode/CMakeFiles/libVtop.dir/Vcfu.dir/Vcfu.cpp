// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcfu.h for the primary calling header

#include "Vcfu.h"
#include "Vcfu__Syms.h"

//==========
CData/*0:0*/ Vcfu::__Vtable1_Cfu__DOT____024signal__0242[64];
CData/*0:0*/ Vcfu::__Vtable2_rsp_valid[16];
CData/*1:0*/ Vcfu::__Vtable3_Cfu__DOT__fsm_state__024next[64];

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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_nn_1/cfu.v", 6, "",
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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_nn_1/cfu.v", 6, "",
                "Verilated model didn't DC converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

void Vcfu::_initial__TOP__1(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_initial__TOP__1\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->Cfu__DOT__stored_output = 0U;
    vlTOPp->Cfu__DOT__fn0_output = 0U;
    vlTOPp->Cfu__DOT__fn0_done = 0U;
    vlTOPp->Cfu__DOT__stored_function_id = 0U;
    vlTOPp->Cfu__DOT__fsm_state = 0U;
}

VL_INLINE_OPT void Vcfu::_combo__TOP__2(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_combo__TOP__2\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->rst = 0U;
    vlTOPp->rst = vlTOPp->reset;
}

void Vcfu::_settle__TOP__3(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_settle__TOP__3\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->rst = 0U;
    vlTOPp->rst = vlTOPp->reset;
    vlTOPp->cmd_ready = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->cmd_ready = 1U;
    }
    vlTOPp->Cfu__DOT__current_function_id = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->Cfu__DOT__current_function_id = (7U 
                                                 & (IData)(vlTOPp->cmd_payload_function_id));
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            vlTOPp->Cfu__DOT__current_function_id = vlTOPp->Cfu__DOT__stored_function_id;
        }
    }
    vlTOPp->Cfu__DOT__stored_function_id__024next = vlTOPp->Cfu__DOT__stored_function_id;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            vlTOPp->Cfu__DOT__stored_function_id__024next 
                = (7U & (IData)(vlTOPp->cmd_payload_function_id));
        }
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__stored_function_id__024next = 0U;
    }
    vlTOPp->__Vtableidx1 = (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                             << 3U) | (((IData)(vlTOPp->cmd_valid) 
                                        << 2U) | (IData)(vlTOPp->Cfu__DOT__fsm_state)));
    vlTOPp->Cfu__DOT____024signal__0242 = vlTOPp->__Vtable1_Cfu__DOT____024signal__0242
        [vlTOPp->__Vtableidx1];
    vlTOPp->Cfu__DOT__current_function_done = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->Cfu__DOT__current_function_done = (1U 
                                                   & (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                       >> 2U) 
                                                      | (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                          >> 1U) 
                                                         | ((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                            | (IData)(vlTOPp->Cfu__DOT__fn0_done)))));
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            vlTOPp->Cfu__DOT__current_function_done 
                = (1U & (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                          >> 2U) | (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                     >> 1U) | ((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                               | (IData)(vlTOPp->Cfu__DOT__fn0_done)))));
        }
    }
    vlTOPp->Cfu__DOT__fn0__DOT__done__024next = vlTOPp->Cfu__DOT____024signal__0242;
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__fn0__DOT__done__024next = 0U;
    }
    vlTOPp->Cfu__DOT__fn0__DOT__output__024next = vlTOPp->Cfu__DOT__fn0_output;
    if (vlTOPp->Cfu__DOT____024signal__0242) {
        vlTOPp->Cfu__DOT__fn0__DOT__output__024next 
            = (vlTOPp->cmd_payload_inputs_0 + vlTOPp->cmd_payload_inputs_1);
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__fn0__DOT__output__024next = 0U;
    }
    vlTOPp->__Vtableidx2 = (((IData)(vlTOPp->Cfu__DOT__current_function_done) 
                             << 3U) | (((IData)(vlTOPp->cmd_valid) 
                                        << 2U) | (IData)(vlTOPp->Cfu__DOT__fsm_state)));
    vlTOPp->rsp_valid = vlTOPp->__Vtable2_rsp_valid
        [vlTOPp->__Vtableidx2];
    vlTOPp->rsp_payload_outputs_0 = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                vlTOPp->rsp_payload_outputs_0 = ((4U 
                                                  & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                  ? vlTOPp->cmd_payload_inputs_0
                                                  : 
                                                 ((2U 
                                                   & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                   ? vlTOPp->cmd_payload_inputs_0
                                                   : 
                                                  ((1U 
                                                    & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                    ? vlTOPp->cmd_payload_inputs_0
                                                    : vlTOPp->Cfu__DOT__fn0_output)));
            }
        }
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                vlTOPp->rsp_payload_outputs_0 = ((4U 
                                                  & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                  ? vlTOPp->cmd_payload_inputs_0
                                                  : 
                                                 ((2U 
                                                   & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                   ? vlTOPp->cmd_payload_inputs_0
                                                   : 
                                                  ((1U 
                                                    & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                    ? vlTOPp->cmd_payload_inputs_0
                                                    : vlTOPp->Cfu__DOT__fn0_output)));
            }
        } else {
            if ((1U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
                vlTOPp->rsp_payload_outputs_0 = vlTOPp->Cfu__DOT__stored_output;
            }
        }
    }
    vlTOPp->__Vtableidx3 = (((IData)(vlTOPp->rst) << 5U) 
                            | (((IData)(vlTOPp->rsp_ready) 
                                << 4U) | (((IData)(vlTOPp->Cfu__DOT__current_function_done) 
                                           << 3U) | 
                                          (((IData)(vlTOPp->cmd_valid) 
                                            << 2U) 
                                           | (IData)(vlTOPp->Cfu__DOT__fsm_state)))));
    vlTOPp->Cfu__DOT__fsm_state__024next = vlTOPp->__Vtable3_Cfu__DOT__fsm_state__024next
        [vlTOPp->__Vtableidx3];
    vlTOPp->Cfu__DOT__stored_output__024next = vlTOPp->Cfu__DOT__stored_output;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                if ((1U & (~ (IData)(vlTOPp->rsp_ready)))) {
                    vlTOPp->Cfu__DOT__stored_output__024next 
                        = ((4U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                            ? vlTOPp->cmd_payload_inputs_0
                            : ((2U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                ? vlTOPp->cmd_payload_inputs_0
                                : ((1U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                    ? vlTOPp->cmd_payload_inputs_0
                                    : vlTOPp->Cfu__DOT__fn0_output)));
                }
            }
        }
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                if ((1U & (~ (IData)(vlTOPp->rsp_ready)))) {
                    vlTOPp->Cfu__DOT__stored_output__024next 
                        = ((4U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                            ? vlTOPp->cmd_payload_inputs_0
                            : ((2U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                ? vlTOPp->cmd_payload_inputs_0
                                : ((1U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                    ? vlTOPp->cmd_payload_inputs_0
                                    : vlTOPp->Cfu__DOT__fn0_output)));
                }
            }
        }
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__stored_output__024next = 0U;
    }
}

VL_INLINE_OPT void Vcfu::_sequent__TOP__4(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_sequent__TOP__4\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->Cfu__DOT__stored_output = vlTOPp->Cfu__DOT__stored_output__024next;
    vlTOPp->Cfu__DOT__fn0_output = vlTOPp->Cfu__DOT__fn0__DOT__output__024next;
    vlTOPp->Cfu__DOT__fn0_done = vlTOPp->Cfu__DOT__fn0__DOT__done__024next;
    vlTOPp->Cfu__DOT__stored_function_id = vlTOPp->Cfu__DOT__stored_function_id__024next;
    vlTOPp->Cfu__DOT__fsm_state = vlTOPp->Cfu__DOT__fsm_state__024next;
    vlTOPp->cmd_ready = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->cmd_ready = 1U;
    }
}

VL_INLINE_OPT void Vcfu::_combo__TOP__5(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_combo__TOP__5\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->Cfu__DOT__stored_function_id__024next = vlTOPp->Cfu__DOT__stored_function_id;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            vlTOPp->Cfu__DOT__stored_function_id__024next 
                = (7U & (IData)(vlTOPp->cmd_payload_function_id));
        }
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__stored_function_id__024next = 0U;
    }
    vlTOPp->Cfu__DOT__current_function_id = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->Cfu__DOT__current_function_id = (7U 
                                                 & (IData)(vlTOPp->cmd_payload_function_id));
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            vlTOPp->Cfu__DOT__current_function_id = vlTOPp->Cfu__DOT__stored_function_id;
        }
    }
    vlTOPp->__Vtableidx1 = (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                             << 3U) | (((IData)(vlTOPp->cmd_valid) 
                                        << 2U) | (IData)(vlTOPp->Cfu__DOT__fsm_state)));
    vlTOPp->Cfu__DOT____024signal__0242 = vlTOPp->__Vtable1_Cfu__DOT____024signal__0242
        [vlTOPp->__Vtableidx1];
    vlTOPp->Cfu__DOT__current_function_done = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        vlTOPp->Cfu__DOT__current_function_done = (1U 
                                                   & (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                       >> 2U) 
                                                      | (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                          >> 1U) 
                                                         | ((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                                            | (IData)(vlTOPp->Cfu__DOT__fn0_done)))));
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            vlTOPp->Cfu__DOT__current_function_done 
                = (1U & (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                          >> 2U) | (((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                     >> 1U) | ((IData)(vlTOPp->Cfu__DOT__current_function_id) 
                                               | (IData)(vlTOPp->Cfu__DOT__fn0_done)))));
        }
    }
    vlTOPp->Cfu__DOT__fn0__DOT__done__024next = vlTOPp->Cfu__DOT____024signal__0242;
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__fn0__DOT__done__024next = 0U;
    }
    vlTOPp->Cfu__DOT__fn0__DOT__output__024next = vlTOPp->Cfu__DOT__fn0_output;
    if (vlTOPp->Cfu__DOT____024signal__0242) {
        vlTOPp->Cfu__DOT__fn0__DOT__output__024next 
            = (vlTOPp->cmd_payload_inputs_0 + vlTOPp->cmd_payload_inputs_1);
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__fn0__DOT__output__024next = 0U;
    }
    vlTOPp->__Vtableidx2 = (((IData)(vlTOPp->Cfu__DOT__current_function_done) 
                             << 3U) | (((IData)(vlTOPp->cmd_valid) 
                                        << 2U) | (IData)(vlTOPp->Cfu__DOT__fsm_state)));
    vlTOPp->rsp_valid = vlTOPp->__Vtable2_rsp_valid
        [vlTOPp->__Vtableidx2];
    vlTOPp->rsp_payload_outputs_0 = 0U;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                vlTOPp->rsp_payload_outputs_0 = ((4U 
                                                  & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                  ? vlTOPp->cmd_payload_inputs_0
                                                  : 
                                                 ((2U 
                                                   & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                   ? vlTOPp->cmd_payload_inputs_0
                                                   : 
                                                  ((1U 
                                                    & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                    ? vlTOPp->cmd_payload_inputs_0
                                                    : vlTOPp->Cfu__DOT__fn0_output)));
            }
        }
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                vlTOPp->rsp_payload_outputs_0 = ((4U 
                                                  & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                  ? vlTOPp->cmd_payload_inputs_0
                                                  : 
                                                 ((2U 
                                                   & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                   ? vlTOPp->cmd_payload_inputs_0
                                                   : 
                                                  ((1U 
                                                    & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                                    ? vlTOPp->cmd_payload_inputs_0
                                                    : vlTOPp->Cfu__DOT__fn0_output)));
            }
        } else {
            if ((1U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
                vlTOPp->rsp_payload_outputs_0 = vlTOPp->Cfu__DOT__stored_output;
            }
        }
    }
    vlTOPp->__Vtableidx3 = (((IData)(vlTOPp->rst) << 5U) 
                            | (((IData)(vlTOPp->rsp_ready) 
                                << 4U) | (((IData)(vlTOPp->Cfu__DOT__current_function_done) 
                                           << 3U) | 
                                          (((IData)(vlTOPp->cmd_valid) 
                                            << 2U) 
                                           | (IData)(vlTOPp->Cfu__DOT__fsm_state)))));
    vlTOPp->Cfu__DOT__fsm_state__024next = vlTOPp->__Vtable3_Cfu__DOT__fsm_state__024next
        [vlTOPp->__Vtableidx3];
    vlTOPp->Cfu__DOT__stored_output__024next = vlTOPp->Cfu__DOT__stored_output;
    if ((0U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
        if (vlTOPp->cmd_valid) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                if ((1U & (~ (IData)(vlTOPp->rsp_ready)))) {
                    vlTOPp->Cfu__DOT__stored_output__024next 
                        = ((4U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                            ? vlTOPp->cmd_payload_inputs_0
                            : ((2U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                ? vlTOPp->cmd_payload_inputs_0
                                : ((1U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                    ? vlTOPp->cmd_payload_inputs_0
                                    : vlTOPp->Cfu__DOT__fn0_output)));
                }
            }
        }
    } else {
        if ((2U == (IData)(vlTOPp->Cfu__DOT__fsm_state))) {
            if (vlTOPp->Cfu__DOT__current_function_done) {
                if ((1U & (~ (IData)(vlTOPp->rsp_ready)))) {
                    vlTOPp->Cfu__DOT__stored_output__024next 
                        = ((4U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                            ? vlTOPp->cmd_payload_inputs_0
                            : ((2U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                ? vlTOPp->cmd_payload_inputs_0
                                : ((1U & (IData)(vlTOPp->Cfu__DOT__current_function_id))
                                    ? vlTOPp->cmd_payload_inputs_0
                                    : vlTOPp->Cfu__DOT__fn0_output)));
                }
            }
        }
    }
    if (vlTOPp->rst) {
        vlTOPp->Cfu__DOT__stored_output__024next = 0U;
    }
}

void Vcfu::_eval(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_combo__TOP__2(vlSymsp);
    if (((IData)(vlTOPp->clk) & (~ (IData)(vlTOPp->__Vclklast__TOP__clk)))) {
        vlTOPp->_sequent__TOP__4(vlSymsp);
    }
    vlTOPp->_combo__TOP__5(vlSymsp);
    // Final
    vlTOPp->__Vclklast__TOP__clk = vlTOPp->clk;
}

void Vcfu::_eval_initial(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_eval_initial\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_initial__TOP__1(vlSymsp);
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
    vlTOPp->_settle__TOP__3(vlSymsp);
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
    if (VL_UNLIKELY((cmd_payload_function_id & 0xfc00U))) {
        Verilated::overWidthError("cmd_payload_function_id");}
    if (VL_UNLIKELY((cmd_valid & 0xfeU))) {
        Verilated::overWidthError("cmd_valid");}
    if (VL_UNLIKELY((reset & 0xfeU))) {
        Verilated::overWidthError("reset");}
    if (VL_UNLIKELY((rsp_ready & 0xfeU))) {
        Verilated::overWidthError("rsp_ready");}
}
#endif  // VL_DEBUG

void Vcfu::_ctor_var_reset() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_ctor_var_reset\n"); );
    // Body
    clk = VL_RAND_RESET_I(1);
    cmd_payload_function_id = VL_RAND_RESET_I(10);
    cmd_payload_inputs_0 = VL_RAND_RESET_I(32);
    cmd_payload_inputs_1 = VL_RAND_RESET_I(32);
    cmd_ready = VL_RAND_RESET_I(1);
    cmd_valid = VL_RAND_RESET_I(1);
    port0_addr = VL_RAND_RESET_I(32);
    port0_din = VL_RAND_RESET_I(32);
    port1_addr = VL_RAND_RESET_I(32);
    port1_din = VL_RAND_RESET_I(32);
    port2_addr = VL_RAND_RESET_I(32);
    port2_din = VL_RAND_RESET_I(32);
    port3_addr = VL_RAND_RESET_I(32);
    port3_din = VL_RAND_RESET_I(32);
    reset = VL_RAND_RESET_I(1);
    rsp_payload_outputs_0 = VL_RAND_RESET_I(32);
    rsp_ready = VL_RAND_RESET_I(1);
    rsp_valid = VL_RAND_RESET_I(1);
    rst = VL_RAND_RESET_I(1);
    Cfu__DOT____024signal__0242 = VL_RAND_RESET_I(1);
    Cfu__DOT__current_function_done = VL_RAND_RESET_I(1);
    Cfu__DOT__current_function_id = VL_RAND_RESET_I(3);
    Cfu__DOT__fn0_done = VL_RAND_RESET_I(1);
    Cfu__DOT__fn0_output = VL_RAND_RESET_I(32);
    Cfu__DOT__fsm_state = VL_RAND_RESET_I(2);
    Cfu__DOT__fsm_state__024next = VL_RAND_RESET_I(2);
    Cfu__DOT__stored_function_id = VL_RAND_RESET_I(3);
    Cfu__DOT__stored_function_id__024next = VL_RAND_RESET_I(3);
    Cfu__DOT__stored_output = VL_RAND_RESET_I(32);
    Cfu__DOT__stored_output__024next = VL_RAND_RESET_I(32);
    Cfu__DOT__fn0__DOT__done__024next = VL_RAND_RESET_I(1);
    Cfu__DOT__fn0__DOT__output__024next = VL_RAND_RESET_I(32);
    __Vtableidx1 = 0;
    __Vtable1_Cfu__DOT____024signal__0242[0] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[1] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[2] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[3] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[4] = 1U;
    __Vtable1_Cfu__DOT____024signal__0242[5] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[6] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[7] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[8] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[9] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[10] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[11] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[12] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[13] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[14] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[15] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[16] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[17] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[18] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[19] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[20] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[21] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[22] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[23] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[24] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[25] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[26] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[27] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[28] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[29] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[30] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[31] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[32] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[33] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[34] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[35] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[36] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[37] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[38] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[39] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[40] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[41] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[42] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[43] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[44] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[45] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[46] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[47] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[48] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[49] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[50] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[51] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[52] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[53] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[54] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[55] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[56] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[57] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[58] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[59] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[60] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[61] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[62] = 0U;
    __Vtable1_Cfu__DOT____024signal__0242[63] = 0U;
    __Vtableidx2 = 0;
    __Vtable2_rsp_valid[0] = 0U;
    __Vtable2_rsp_valid[1] = 1U;
    __Vtable2_rsp_valid[2] = 0U;
    __Vtable2_rsp_valid[3] = 0U;
    __Vtable2_rsp_valid[4] = 0U;
    __Vtable2_rsp_valid[5] = 1U;
    __Vtable2_rsp_valid[6] = 0U;
    __Vtable2_rsp_valid[7] = 0U;
    __Vtable2_rsp_valid[8] = 0U;
    __Vtable2_rsp_valid[9] = 1U;
    __Vtable2_rsp_valid[10] = 1U;
    __Vtable2_rsp_valid[11] = 0U;
    __Vtable2_rsp_valid[12] = 1U;
    __Vtable2_rsp_valid[13] = 1U;
    __Vtable2_rsp_valid[14] = 1U;
    __Vtable2_rsp_valid[15] = 0U;
    __Vtableidx3 = 0;
    __Vtable3_Cfu__DOT__fsm_state__024next[0] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[1] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[2] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[3] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[4] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[5] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[6] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[7] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[8] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[9] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[10] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[11] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[12] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[13] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[14] = 1U;
    __Vtable3_Cfu__DOT__fsm_state__024next[15] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[16] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[17] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[18] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[19] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[20] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[21] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[22] = 2U;
    __Vtable3_Cfu__DOT__fsm_state__024next[23] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[24] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[25] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[26] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[27] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[28] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[29] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[30] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[31] = 3U;
    __Vtable3_Cfu__DOT__fsm_state__024next[32] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[33] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[34] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[35] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[36] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[37] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[38] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[39] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[40] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[41] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[42] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[43] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[44] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[45] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[46] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[47] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[48] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[49] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[50] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[51] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[52] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[53] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[54] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[55] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[56] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[57] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[58] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[59] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[60] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[61] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[62] = 0U;
    __Vtable3_Cfu__DOT__fsm_state__024next[63] = 0U;
}
