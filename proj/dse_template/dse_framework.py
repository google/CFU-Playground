#!/bin/python3

import os
import random
import subprocess
import time


def make_variant_string(csrPluginConfig="mcycle", bypass=True, cfu=False, dCacheSize=4096, hardwareDiv=False, 
                 iCacheSize=4096, mulDiv=True, prediction="none", safe=True, singleCycleShift=True, singleCycleMulDiv=True):

    CPU_PARAMS = {
        "csrPluginConfig":    csrPluginConfig,
        "bypass":             bypass,
        "cfu":                cfu,
        "dCacheSize":         dCacheSize,  
        "hardwareDiv":        hardwareDiv,
        "iCacheSize":         iCacheSize, 
        "mulDiv":             mulDiv, 
        "prediction":         prediction, 
        "safe":               safe, 
        "singleCycleShift":   singleCycleShift, 
        "singleCycleMulDiv":  singleCycleMulDiv 
    }
    
    # Variant string must begin with 'generate' keyword
    variant = "generate"
    for param_name, val in sorted(CPU_PARAMS.items()):
        if param_name == "cfu":
            if val is True:
                variant = variant + "+cfu"
        else:
            variant = variant + "+" + param_name + ":" + str(val).lower()
    
    return variant
    

def get_resource_util(target):
    
    # Open gateware file with synthesis stats from Yosys
    gw_file = None
    if target == "digilent_arty":
        gw_file = open('../../soc/build/digilent_arty.dse_template/gateware/digilent_arty_synth.log', 'r')
    elif target == "1bitsquared_icebreaker":
        gw_file = open('../../soc/build/1bitsquared_icebreaker.dse_template/gateware/_1bitsquared_icebreaker.rpt', 'r')
    lines = gw_file.readlines()
    
    # Find number of cells used after synthesis 
    cells = 0
    for line in lines:
        if 'Number of cells:' in line: 
            cells = int(line.strip().split(' ')[-1])

    return cells


def get_cycle_count():

    # Open output of simulation and find max cycle count
    cycle_file = open('./cycle_counts.rpt', 'r')
    lines = cycle_file.readlines()
     
    cycles = float('inf')
    cycles_found = False
    for line in lines:
        if 'cycles total' in line:
            cur_cycles = int(line.strip().split(' ')[4][:-1])
            if not cycles_found:
                cycles = cur_cycles
                cycles_found = True
            else:
                cycles = cur_cycles if cur_cycles > cycles else cycles

    return cycles

            
def run_config(variant, target):
    
    # Generate bitstream and run simulation for given CPU variant and return metric results
    EXTRA_LITEX_ARGS = 'EXTRA_LITEX_ARGS="--cpu-variant=' + variant +'"'
    subprocess.run(['make', 'clean']) 
    subprocess.run(['make', 'bitstream', 'TARGET=' + target, EXTRA_LITEX_ARGS, "USE_SYMBIFLOW=1"])
    workload_cmd = ['make', 'load', 'PLATFORM=sim', EXTRA_LITEX_ARGS]
    outfile = open("cycle_counts.rpt", "w")
    workload = subprocess.Popen(workload_cmd, stdout=outfile)
    time.sleep(2100)
    workload.terminate()
    cycles = get_cycle_count()
    cells  = get_resource_util(target)

    return (cycles, cells)

    
def dse(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, 
        iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv, target):

    variant = make_variant_string(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, 
        iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv)
    cycles, cells = run_config(variant, target)
   
    print("NUMBER OF CYCLES: "  + str(cycles))
    print("NUMBER OF CELLS:  "  + str(cells))
    print("\nEXITING DSE...\n")
    
    return (cycles, cells) 


if __name__ == "__main__":
    # Sample example of how to use dse framework
    csrPluginConfig="mcycle"
    bypass=True
    cfu=False
    dCacheSize=4096
    hardwareDiv=True
    iCacheSize=4096 
    mulDiv=True
    prediction="none"
    safe=True
    singleCycleShift=True
    singleCycleMulDiv=True
    TARGET = "digilent_arty"  
    dse(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, 
        mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv, TARGET)
