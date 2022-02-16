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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_nn_svhn/cfu.v", 2, "",
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
            VL_FATAL_MT("/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_nn_svhn/cfu.v", 2, "",
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
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack;
    CData/*3:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__state;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__a_s;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__b_s;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__z_s;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__guard;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__round_bit;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__sticky;
    CData/*0:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb;
    SData/*9:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__a_e;
    SData/*9:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__b_e;
    SData/*9:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__z_e;
    IData/*31:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__a;
    IData/*31:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__b;
    IData/*23:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__a_m;
    IData/*23:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__b_m;
    IData/*31:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__z;
    IData/*23:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__z_m;
    QData/*47:0*/ __Vdly__Cfu__DOT__fp_mul__DOT__product;
    // Body
    __Vdly__Cfu__DOT__fp_mul__DOT__sticky = vlTOPp->Cfu__DOT__fp_mul__DOT__sticky;
    __Vdly__Cfu__DOT__fp_mul__DOT__round_bit = vlTOPp->Cfu__DOT__fp_mul__DOT__round_bit;
    __Vdly__Cfu__DOT__fp_mul__DOT__guard = vlTOPp->Cfu__DOT__fp_mul__DOT__guard;
    __Vdly__Cfu__DOT__fp_mul__DOT__z_m = vlTOPp->Cfu__DOT__fp_mul__DOT__z_m;
    __Vdly__Cfu__DOT__fp_mul__DOT__product = vlTOPp->Cfu__DOT__fp_mul__DOT__product;
    __Vdly__Cfu__DOT__fp_mul__DOT__z_e = vlTOPp->Cfu__DOT__fp_mul__DOT__z_e;
    __Vdly__Cfu__DOT__fp_mul__DOT__z_s = vlTOPp->Cfu__DOT__fp_mul__DOT__z_s;
    __Vdly__Cfu__DOT__fp_mul__DOT__z = vlTOPp->Cfu__DOT__fp_mul__DOT__z;
    __Vdly__Cfu__DOT__fp_mul__DOT__b_s = vlTOPp->Cfu__DOT__fp_mul__DOT__b_s;
    __Vdly__Cfu__DOT__fp_mul__DOT__a_s = vlTOPp->Cfu__DOT__fp_mul__DOT__a_s;
    __Vdly__Cfu__DOT__fp_mul__DOT__b_e = vlTOPp->Cfu__DOT__fp_mul__DOT__b_e;
    __Vdly__Cfu__DOT__fp_mul__DOT__a_e = vlTOPp->Cfu__DOT__fp_mul__DOT__a_e;
    __Vdly__Cfu__DOT__fp_mul__DOT__b_m = vlTOPp->Cfu__DOT__fp_mul__DOT__b_m;
    __Vdly__Cfu__DOT__fp_mul__DOT__a_m = vlTOPp->Cfu__DOT__fp_mul__DOT__a_m;
    __Vdly__Cfu__DOT__fp_mul__DOT__b = vlTOPp->Cfu__DOT__fp_mul__DOT__b;
    __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack = vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_b_ack;
    __Vdly__Cfu__DOT__fp_mul__DOT__state = vlTOPp->Cfu__DOT__fp_mul__DOT__state;
    __Vdly__Cfu__DOT__fp_mul__DOT__a = vlTOPp->Cfu__DOT__fp_mul__DOT__a;
    __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb = vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z_stb;
    __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack = vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_a_ack;
    if (vlTOPp->reset) {
        vlTOPp->rsp_payload_outputs_0 = 0U;
    } else {
        if (vlTOPp->rsp_valid) {
            vlTOPp->rsp_payload_outputs_0 = ((0U != 
                                              (0x7fU 
                                               & ((IData)(vlTOPp->cmd_payload_function_id) 
                                                  >> 3U)))
                                              ? 0U : vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z);
        }
    }
    if (((((((((0U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state)) 
               | (1U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
              | (2U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
             | (3U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
            | (4U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
           | (5U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
          | (6U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) 
         | (7U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state)))) {
        if ((0U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
            __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack = 1U;
            if (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_a_ack) 
                 & (IData)(vlTOPp->Cfu__DOT__input_a_stb))) {
                __Vdly__Cfu__DOT__fp_mul__DOT__a = vlTOPp->cmd_payload_inputs_0;
                __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack = 0U;
                __Vdly__Cfu__DOT__fp_mul__DOT__state = 1U;
            }
        } else {
            if ((1U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack = 1U;
                if (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_b_ack) 
                     & (IData)(vlTOPp->Cfu__DOT__input_b_stb))) {
                    __Vdly__Cfu__DOT__fp_mul__DOT__b 
                        = vlTOPp->cmd_payload_inputs_1;
                    __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack = 0U;
                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 2U;
                }
            } else {
                if ((2U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                    __Vdly__Cfu__DOT__fp_mul__DOT__a_m 
                        = (0x7fffffU & vlTOPp->Cfu__DOT__fp_mul__DOT__a);
                    __Vdly__Cfu__DOT__fp_mul__DOT__b_m 
                        = (0x7fffffU & vlTOPp->Cfu__DOT__fp_mul__DOT__b);
                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 3U;
                    __Vdly__Cfu__DOT__fp_mul__DOT__a_e 
                        = (0x3ffU & ((0xffU & (vlTOPp->Cfu__DOT__fp_mul__DOT__a 
                                               >> 0x17U)) 
                                     - (IData)(0x7fU)));
                    __Vdly__Cfu__DOT__fp_mul__DOT__b_e 
                        = (0x3ffU & ((0xffU & (vlTOPp->Cfu__DOT__fp_mul__DOT__b 
                                               >> 0x17U)) 
                                     - (IData)(0x7fU)));
                    __Vdly__Cfu__DOT__fp_mul__DOT__a_s 
                        = (1U & (vlTOPp->Cfu__DOT__fp_mul__DOT__a 
                                 >> 0x1fU));
                    __Vdly__Cfu__DOT__fp_mul__DOT__b_s 
                        = (1U & (vlTOPp->Cfu__DOT__fp_mul__DOT__b 
                                 >> 0x1fU));
                } else {
                    if ((3U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                        if ((((0x80U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e)) 
                              & (0U != vlTOPp->Cfu__DOT__fp_mul__DOT__a_m)) 
                             | ((0x80U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e)) 
                                & (0U != vlTOPp->Cfu__DOT__fp_mul__DOT__b_m)))) {
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0x80000000U | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                            __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0x7f800000U | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0x400000U | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0xffc00000U & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                        } else {
                            if ((0x80U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e))) {
                                if (((0xffffff81U == 
                                      VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e))) 
                                     & (0U == vlTOPp->Cfu__DOT__fp_mul__DOT__b_m))) {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0x80000000U 
                                           | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0x400000U 
                                           | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0xffc00000U 
                                           & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0x7f800000U 
                                           | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                } else {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = ((0x7fffffffU 
                                            & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                                           | (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_s) 
                                               ^ (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_s)) 
                                              << 0x1fU));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0x7f800000U 
                                           | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                        = (0xff800000U 
                                           & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                }
                                __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                            } else {
                                if ((0x80U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e))) {
                                    if (((0xffffff81U 
                                          == VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e))) 
                                         & (0U == vlTOPp->Cfu__DOT__fp_mul__DOT__a_m))) {
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0x80000000U 
                                               | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0x400000U 
                                               | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0xffc00000U 
                                               & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0x7f800000U 
                                               | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    } else {
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = ((0x7fffffffU 
                                                & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                                               | (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_s) 
                                                   ^ (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_s)) 
                                                  << 0x1fU));
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0x7f800000U 
                                               | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0xff800000U 
                                               & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    }
                                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                                } else {
                                    if (((0xffffff81U 
                                          == VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e))) 
                                         & (0U == vlTOPp->Cfu__DOT__fp_mul__DOT__a_m))) {
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = ((0x7fffffffU 
                                                & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                                               | (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_s) 
                                                   ^ (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_s)) 
                                                  << 0x1fU));
                                        __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0x807fffffU 
                                               & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                            = (0xff800000U 
                                               & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                    } else {
                                        if (((0xffffff81U 
                                              == VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e))) 
                                             & (0U 
                                                == vlTOPp->Cfu__DOT__fp_mul__DOT__b_m))) {
                                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                                = (
                                                   (0x7fffffffU 
                                                    & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                                                   | (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_s) 
                                                       ^ (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_s)) 
                                                      << 0x1fU));
                                            __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                                = (0x807fffffU 
                                                   & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                                = (0xff800000U 
                                                   & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                                        } else {
                                            if ((0xffffff81U 
                                                 == 
                                                 VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e)))) {
                                                __Vdly__Cfu__DOT__fp_mul__DOT__a_e = 0x382U;
                                            } else {
                                                __Vdly__Cfu__DOT__fp_mul__DOT__a_m 
                                                    = 
                                                    (0x800000U 
                                                     | __Vdly__Cfu__DOT__fp_mul__DOT__a_m);
                                            }
                                            if ((0xffffff81U 
                                                 == 
                                                 VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e)))) {
                                                __Vdly__Cfu__DOT__fp_mul__DOT__b_e = 0x382U;
                                            } else {
                                                __Vdly__Cfu__DOT__fp_mul__DOT__b_m 
                                                    = 
                                                    (0x800000U 
                                                     | __Vdly__Cfu__DOT__fp_mul__DOT__b_m);
                                            }
                                            __Vdly__Cfu__DOT__fp_mul__DOT__state = 4U;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        if ((4U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                            if ((0x800000U & vlTOPp->Cfu__DOT__fp_mul__DOT__a_m)) {
                                __Vdly__Cfu__DOT__fp_mul__DOT__state = 5U;
                            } else {
                                __Vdly__Cfu__DOT__fp_mul__DOT__a_m 
                                    = (0xffffffU & 
                                       (vlTOPp->Cfu__DOT__fp_mul__DOT__a_m 
                                        << 1U));
                                __Vdly__Cfu__DOT__fp_mul__DOT__a_e 
                                    = (0x3ffU & ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e) 
                                                 - (IData)(1U)));
                            }
                        } else {
                            if ((5U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                                if ((0x800000U & vlTOPp->Cfu__DOT__fp_mul__DOT__b_m)) {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 6U;
                                } else {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__b_m 
                                        = (0xffffffU 
                                           & (vlTOPp->Cfu__DOT__fp_mul__DOT__b_m 
                                              << 1U));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__b_e 
                                        = (0x3ffU & 
                                           ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e) 
                                            - (IData)(1U)));
                                }
                            } else {
                                if ((6U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z_s 
                                        = ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_s) 
                                           ^ (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_s));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z_e 
                                        = (0x3ffU & 
                                           ((IData)(1U) 
                                            + ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_e) 
                                               + (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_e))));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__product 
                                        = (VL_ULL(0xffffffffffff) 
                                           & ((QData)((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__a_m)) 
                                              * (QData)((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__b_m))));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 7U;
                                } else {
                                    __Vdly__Cfu__DOT__fp_mul__DOT__z_m 
                                        = (0xffffffU 
                                           & (IData)(
                                                     (vlTOPp->Cfu__DOT__fp_mul__DOT__product 
                                                      >> 0x18U)));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 8U;
                                    __Vdly__Cfu__DOT__fp_mul__DOT__guard 
                                        = (1U & (IData)(
                                                        (vlTOPp->Cfu__DOT__fp_mul__DOT__product 
                                                         >> 0x17U)));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__round_bit 
                                        = (1U & (IData)(
                                                        (vlTOPp->Cfu__DOT__fp_mul__DOT__product 
                                                         >> 0x16U)));
                                    __Vdly__Cfu__DOT__fp_mul__DOT__sticky 
                                        = (0U != (0x3fffffU 
                                                  & (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__product)));
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        if ((8U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
            if ((0x800000U & vlTOPp->Cfu__DOT__fp_mul__DOT__z_m)) {
                __Vdly__Cfu__DOT__fp_mul__DOT__state = 9U;
            } else {
                __Vdly__Cfu__DOT__fp_mul__DOT__z_e 
                    = (0x3ffU & ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e) 
                                 - (IData)(1U)));
                __Vdly__Cfu__DOT__fp_mul__DOT__z_m 
                    = (0xffffffU & (vlTOPp->Cfu__DOT__fp_mul__DOT__z_m 
                                    << 1U));
                __Vdly__Cfu__DOT__fp_mul__DOT__z_m 
                    = ((0xfffffeU & __Vdly__Cfu__DOT__fp_mul__DOT__z_m) 
                       | (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__guard));
                __Vdly__Cfu__DOT__fp_mul__DOT__guard 
                    = vlTOPp->Cfu__DOT__fp_mul__DOT__round_bit;
                __Vdly__Cfu__DOT__fp_mul__DOT__round_bit = 0U;
            }
        } else {
            if ((9U == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                if (VL_GTS_III(1,32,32, 0xffffff82U, 
                               VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e)))) {
                    __Vdly__Cfu__DOT__fp_mul__DOT__z_e 
                        = (0x3ffU & ((IData)(1U) + (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e)));
                    __Vdly__Cfu__DOT__fp_mul__DOT__z_m 
                        = (0xffffffU & (vlTOPp->Cfu__DOT__fp_mul__DOT__z_m 
                                        >> 1U));
                    __Vdly__Cfu__DOT__fp_mul__DOT__sticky 
                        = ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__sticky) 
                           | (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__round_bit));
                    __Vdly__Cfu__DOT__fp_mul__DOT__round_bit 
                        = vlTOPp->Cfu__DOT__fp_mul__DOT__guard;
                    __Vdly__Cfu__DOT__fp_mul__DOT__guard 
                        = (1U & vlTOPp->Cfu__DOT__fp_mul__DOT__z_m);
                } else {
                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xaU;
                }
            } else {
                if ((0xaU == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                    if (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__guard) 
                         & (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__round_bit) 
                             | (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__sticky)) 
                            | vlTOPp->Cfu__DOT__fp_mul__DOT__z_m))) {
                        __Vdly__Cfu__DOT__fp_mul__DOT__z_m 
                            = (0xffffffU & ((IData)(1U) 
                                            + vlTOPp->Cfu__DOT__fp_mul__DOT__z_m));
                        if ((0xffffffU == vlTOPp->Cfu__DOT__fp_mul__DOT__z_m)) {
                            __Vdly__Cfu__DOT__fp_mul__DOT__z_e 
                                = (0x3ffU & ((IData)(1U) 
                                             + (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e)));
                        }
                    }
                    __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xbU;
                } else {
                    if ((0xbU == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                            = ((0xff800000U & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                               | (0x7fffffU & vlTOPp->Cfu__DOT__fp_mul__DOT__z_m));
                        __Vdly__Cfu__DOT__fp_mul__DOT__state = 0xcU;
                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                            = ((0x807fffffU & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                               | (0x7f800000U & (((IData)(0x7fU) 
                                                  + (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e)) 
                                                 << 0x17U)));
                        __Vdly__Cfu__DOT__fp_mul__DOT__z 
                            = ((0x7fffffffU & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                               | ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_s) 
                                  << 0x1fU));
                        if (((0xffffff82U == VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e))) 
                             & (~ (vlTOPp->Cfu__DOT__fp_mul__DOT__z_m 
                                   >> 0x17U)))) {
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0x807fffffU & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                        }
                        if (VL_LTS_III(1,32,32, 0x7fU, 
                                       VL_EXTENDS_II(32,10, (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_e)))) {
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = ((0x7fffffffU & __Vdly__Cfu__DOT__fp_mul__DOT__z) 
                                   | ((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__z_s) 
                                      << 0x1fU));
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0x7f800000U | __Vdly__Cfu__DOT__fp_mul__DOT__z);
                            __Vdly__Cfu__DOT__fp_mul__DOT__z 
                                = (0xff800000U & __Vdly__Cfu__DOT__fp_mul__DOT__z);
                        }
                    } else {
                        if ((0xcU == (IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__state))) {
                            __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb = 1U;
                            vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z 
                                = vlTOPp->Cfu__DOT__fp_mul__DOT__z;
                            if (((IData)(vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z_stb) 
                                 & (IData)(vlTOPp->Cfu__DOT__output_z_ack))) {
                                __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb = 0U;
                                __Vdly__Cfu__DOT__fp_mul__DOT__state = 0U;
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlTOPp->reset) {
        __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack = 0U;
        __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack = 0U;
        __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb = 0U;
        __Vdly__Cfu__DOT__fp_mul__DOT__state = 0U;
    }
    vlTOPp->Cfu__DOT__fp_mul__DOT__a = __Vdly__Cfu__DOT__fp_mul__DOT__a;
    vlTOPp->Cfu__DOT__fp_mul__DOT__state = __Vdly__Cfu__DOT__fp_mul__DOT__state;
    vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_b_ack = __Vdly__Cfu__DOT__fp_mul__DOT__s_input_b_ack;
    vlTOPp->Cfu__DOT__fp_mul__DOT__b = __Vdly__Cfu__DOT__fp_mul__DOT__b;
    vlTOPp->Cfu__DOT__fp_mul__DOT__a_m = __Vdly__Cfu__DOT__fp_mul__DOT__a_m;
    vlTOPp->Cfu__DOT__fp_mul__DOT__b_m = __Vdly__Cfu__DOT__fp_mul__DOT__b_m;
    vlTOPp->Cfu__DOT__fp_mul__DOT__a_e = __Vdly__Cfu__DOT__fp_mul__DOT__a_e;
    vlTOPp->Cfu__DOT__fp_mul__DOT__b_e = __Vdly__Cfu__DOT__fp_mul__DOT__b_e;
    vlTOPp->Cfu__DOT__fp_mul__DOT__a_s = __Vdly__Cfu__DOT__fp_mul__DOT__a_s;
    vlTOPp->Cfu__DOT__fp_mul__DOT__b_s = __Vdly__Cfu__DOT__fp_mul__DOT__b_s;
    vlTOPp->Cfu__DOT__fp_mul__DOT__z = __Vdly__Cfu__DOT__fp_mul__DOT__z;
    vlTOPp->Cfu__DOT__fp_mul__DOT__z_s = __Vdly__Cfu__DOT__fp_mul__DOT__z_s;
    vlTOPp->Cfu__DOT__fp_mul__DOT__z_e = __Vdly__Cfu__DOT__fp_mul__DOT__z_e;
    vlTOPp->Cfu__DOT__fp_mul__DOT__product = __Vdly__Cfu__DOT__fp_mul__DOT__product;
    vlTOPp->Cfu__DOT__fp_mul__DOT__z_m = __Vdly__Cfu__DOT__fp_mul__DOT__z_m;
    vlTOPp->Cfu__DOT__fp_mul__DOT__guard = __Vdly__Cfu__DOT__fp_mul__DOT__guard;
    vlTOPp->Cfu__DOT__fp_mul__DOT__round_bit = __Vdly__Cfu__DOT__fp_mul__DOT__round_bit;
    vlTOPp->Cfu__DOT__fp_mul__DOT__sticky = __Vdly__Cfu__DOT__fp_mul__DOT__sticky;
    vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_a_ack = __Vdly__Cfu__DOT__fp_mul__DOT__s_input_a_ack;
    vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z_stb = __Vdly__Cfu__DOT__fp_mul__DOT__s_output_z_stb;
    vlTOPp->cmd_ready = vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_a_ack;
    if ((1U & (~ (IData)(vlTOPp->reset)))) {
        if (vlTOPp->rsp_valid) {
            vlTOPp->Cfu__DOT__output_z_ack = 1U;
        }
    }
    if (vlTOPp->reset) {
        vlTOPp->Cfu__DOT__input_a_stb = 0U;
    } else {
        if ((1U & (~ (IData)(vlTOPp->rsp_valid)))) {
            if (vlTOPp->cmd_valid) {
                vlTOPp->Cfu__DOT__input_a_stb = 1U;
            }
        }
    }
    if (vlTOPp->reset) {
        vlTOPp->Cfu__DOT__input_b_stb = 0U;
    } else {
        if ((1U & (~ (IData)(vlTOPp->rsp_valid)))) {
            if (vlTOPp->cmd_valid) {
                vlTOPp->Cfu__DOT__input_b_stb = 1U;
            }
        }
    }
    vlTOPp->rsp_valid = vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z_stb;
}

void Vcfu::_settle__TOP__2(Vcfu__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcfu::_settle__TOP__2\n"); );
    Vcfu* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->cmd_ready = vlTOPp->Cfu__DOT__fp_mul__DOT__s_input_a_ack;
    vlTOPp->rsp_valid = vlTOPp->Cfu__DOT__fp_mul__DOT__s_output_z_stb;
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
    Cfu__DOT__input_a_stb = VL_RAND_RESET_I(1);
    Cfu__DOT__input_b_stb = VL_RAND_RESET_I(1);
    Cfu__DOT__output_z_ack = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__s_output_z_stb = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__s_output_z = VL_RAND_RESET_I(32);
    Cfu__DOT__fp_mul__DOT__s_input_a_ack = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__s_input_b_ack = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__state = VL_RAND_RESET_I(4);
    Cfu__DOT__fp_mul__DOT__a = VL_RAND_RESET_I(32);
    Cfu__DOT__fp_mul__DOT__b = VL_RAND_RESET_I(32);
    Cfu__DOT__fp_mul__DOT__z = VL_RAND_RESET_I(32);
    Cfu__DOT__fp_mul__DOT__a_m = VL_RAND_RESET_I(24);
    Cfu__DOT__fp_mul__DOT__b_m = VL_RAND_RESET_I(24);
    Cfu__DOT__fp_mul__DOT__z_m = VL_RAND_RESET_I(24);
    Cfu__DOT__fp_mul__DOT__a_e = VL_RAND_RESET_I(10);
    Cfu__DOT__fp_mul__DOT__b_e = VL_RAND_RESET_I(10);
    Cfu__DOT__fp_mul__DOT__z_e = VL_RAND_RESET_I(10);
    Cfu__DOT__fp_mul__DOT__a_s = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__b_s = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__z_s = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__guard = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__round_bit = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__sticky = VL_RAND_RESET_I(1);
    Cfu__DOT__fp_mul__DOT__product = VL_RAND_RESET_Q(48);
}
