#!/bin/python3

import os
import sys
import random
import subprocess
import time
import datetime


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
            if val is True or val == "True":
                variant = variant + "+cfu"
                # Copy optimized kernel invoking CFU to src dir
                subprocess.run(['cp', '-r', './tensorflow', './src/.'])
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
    cycle_file = open('cycle_count.rpt', 'r')
    lines = cycle_file.readlines()
     
    cycles = sys.float_info.max 
    cycles_found = False
    test_passing = True
    for line in lines:
        if 'FAIL' in line and 'test' in line and 'failed' in line:
            test_passing = False
        if 'cycles total' in line:
            cycles_list = [float(s) for s in line.split() if s.isdigit()]
            cur_cycles = cycles_list[0] 
            if not cycles_found:
                cycles = cur_cycles
                cycles_found = True
            else:
                cycles = cur_cycles if cur_cycles > cycles else cycles

    return (test_passing, cycles)

            
def run_config(variant, target="digilent_arty", workload="pdti8"):
    
    # Generate bitstream and run simulation for given CPU variant and return metric results
    cycles = None
    cells  = None
    run_succeeds = False 
    test_passed = False
    update_workload(workload)
    while not run_succeeds:
        EXTRA_LITEX_ARGS = 'EXTRA_LITEX_ARGS="--cpu-variant=' + variant +'"'
        subprocess.run(['make', 'clean']) 
        subprocess.run(['make', 'bitstream', 'TARGET=' + target, EXTRA_LITEX_ARGS, "USE_SYMBIFLOW=1"])
        workload_cmd = ['make', 'load', 'PLATFORM=sim', EXTRA_LITEX_ARGS]
        filename = 'cycle_count.rpt'
        outfile  = open(filename, "w")
        workload = subprocess.run(workload_cmd, stdout=outfile)
        try:
            test_passed, cycles = get_cycle_count()
            run_succeeds = True
        except UnicodeDecodeError:
            run_succeeds = False
        cells  = get_resource_util(target)
        
    # Remove any copied tf source overlay for next run
    if os.path.exists("./src/tensorflow"):
        subprocess.run(['rm', '-rf', './src/tensorflow'])
    
    # Check to see if the workload / benchmark test still passing (i.e. hw and sw are both functionally correct)
    if test_passed:
        return (cycles, cells)
    else: # if test failing return large number to make sample invalid
        print("Simulation completed but program test failed! Modifications need to be made to CFU HW or SW.")
        return (float('inf'), float('inf'))


def update_workload(workload="pdti8", makefile_path="./Makefile"):
    if not os.path.isfile(makefile_path):
        print("Makefile not found.")
        exit() 

    with open(makefile_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    embench_workload = False
    for line in lines:
        if workload.lower() in line.lower():
            embench_workload = "EMBENCH" in line
            if "#DEFINES" in line:
                line = line.replace("#DEFINES", "DEFINES") 
        elif ("INCLUDE_MODEL_" in line or "INCLUDE_EMBENCH_" in line) and "#DEFINES" not in line:
            line = line.replace("DEFINES", "#DEFINES") 
        elif "MENU_CHAR_SEQUENCE" in line:
            if embench_workload:
                line = "DEFINES += MENU_CHAR_SEQUENCE='\"81xQ\"'\n"  
            else: # TinyML model workload golden tests
                line = "DEFINES += MENU_CHAR_SEQUENCE='\"11gxxQ\"'\n"  
        new_lines.append(line)

    with open(makefile_path, "w") as file:
        file.writelines(new_lines)

    
def dse(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, 
        iCacheSize, mulDiv, prediction, safe, singleCycleShift, 
        singleCycleMulDiv, target="digilent_arty", workload="pdti8"):

    variant = make_variant_string(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, 
        iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv)
    cycles, cells = run_config(variant, target, workload)
   
    print("NUMBER OF CYCLES: "  + str(cycles))
    print("NUMBER OF CELLS:  "  + str(cells))
    print("\nEXITING DSE...\n")
    
    return (cycles, cells) 


if __name__ == "__main__":
    if len(sys.argv) > 1 :
        # Used for running dse via cmd line
        # Sample command that would be equivalent to default params:
        # ./dse_framework.py mcycle True False 4096 True 4096 True none True True True 
        csrPluginConfig   = sys.argv[1]
        bypass            = True if sys.argv[2] == "True" else False
        cfu               = True if sys.argv[3] == "True" else False
        dCacheSize        = int(sys.argv[4])
        hardwareDiv       = True if sys.argv[5] == "True" else False
        iCacheSize        = int(sys.argv[6])
        mulDiv            = True if sys.argv[7] == "True" else False
        prediction        = sys.argv[8] 
        safe              = True if sys.argv[9] == "True" else False
        singleCycleShift  = True if sys.argv[10] == "True" else False
        singleCycleMulDiv = True if sys.argv[11] == "True" else False
        TARGET            = "digilent_arty"  
        WORKLOAD          = "pdti8"
    else:
        # Sample example of how to use dse framework
        csrPluginConfig="mcycle"
        bypass=True
        cfu=False
        dCacheSize=4096
        hardwareDiv=True
        iCacheSize=4096 
        mulDiv=True
        prediction="static"
        safe=True
        singleCycleShift=True
        singleCycleMulDiv=True
        TARGET = "digilent_arty"  
        WORKLOAD = "pdti8"
    
    dse(csrPluginConfig, bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, 
        mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv, TARGET, WORKLOAD)
