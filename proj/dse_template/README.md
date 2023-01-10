# Design Space Exploration in CFU Playground
This project template is intended for performing architectural design space exploration (DSE) in CFU Playground. 

## Prerequisites & Setup
*NOTE: This has been tested and verified on Ubuntu 18.04 LTS.*

1. Playground Installation
- Make sure you have run `$CFU_ROOT/scripts/setup`
- Make sure you have installed and entered the Symbiflow environment via `make install-sf` & `make enter-sf`
- Test this with `which symbiflow_synth`

2. Install the VexRiscv Build Tools
- Run `$CFU_ROOT/scripts/setup_vexriscv_build.sh`

3. Install Vizier 
- Run `$CFU_ROOT/scripts/setup_vizier.sh`

4. Test DSE 
- In `proj/dse_template` run `python vizier_dse.py`
- Depending on your machine, this could take somewhere between 40-60 min to run
- Sample output should look like this (with different raw values):
```
EXITING DSE...

Optimal Trial Suggestion and Objective: ParameterDict(_items={'bypass': True, 'cfu': False, 'hardwareDiv': True, 'mulDiv': False, 'singleCycleShift': False, 'singleCycleMulDiv': True, 'safe': False, 'prediction': dynamic_target, 'iCacheSize': 4096.0, 'dCacheSize': 512.0}) Measurement(metrics={'cycles': Metric(value=16638.0, std=None), 'cells': Metric(value=1152797428.0, std=None)}, elapsed_secs=0.0, steps=0)
Optimal Trial Suggestion and Objective: ParameterDict(_items={'bypass': False, 'cfu': True, 'hardwareDiv': False, 'mulDiv': False, 'singleCycleShift': True, 'singleCycleMulDiv': True, 'safe': True, 'prediction': dynamic, 'iCacheSize': 4096.0, 'dCacheSize': 8192.0}) Measurement(metrics={'cycles': Metric(value=17932.0, std=None), 'cells': Metric(value=911708646.0, std=None)}, elapsed_secs=0.0, steps=0)
```

## Developer Flow
Similar to the typical Playground flow, developers should first profile the workload they would like to accelerate and then design a CFU to speedup the intended operation. After designing your CFU in the project, you can now perform design space exploration between your CFU and CPU. This is especially interesting if you are considering different versions of a CFU. It is also useful simply for optimizing the soft-CPU for your workload after you are happy with your CFU.

### Running Automated DSE with Vizier

This repository comes packaged with OSS Vizier, a black-box optimization service provided by Google. We expose various architectural parameters to Vizier in `vizier_dse.py`. Vizier uses these parameters to construct a search space from which it samples. These samples (set of parameters) are then fed to the Playground via calls to `dse_framework.py`. This call first generates the Verilog based on the architectural parameters and then runs synthesis (via F4PGA) & simulation (via Verilator) to return performance of this sample on a given workload. In this context, performance refers to latency (i.e. cycle count) and resource usage (i.e. FPGA cell count). Vizier takes these values and accordingly returns more sample suggestions, optimizing for these two metrics. 

![Alt text](../../docs/source/images/Vizier_+_Playground.png?raw=true "Title")

The algorithm and number of samples Vizier uses can be modified in `vizier_dse.py`. The workload can be changed via the project [Makefile](https://github.com/google/CFU-Playground/blob/1a7a8d58bb10fe9118cc280bb9ff7ea3217cd474/proj/dse_template/Makefile#L44) which provides a sequence of characters that are fed to the Playground's interactive menu. 


### Parameters 
Below are some of the available, configurable parameters for tuning of the VexRiscv CPU exposed to Vizier in `vizier_dse.py`. True or False means to either include the component in the CPU or not respectively. You can swap in different CFU desings you may have by replacing your `cfu.v` or `cfu.py` accordingly. Cache sizes are powers of 2.

|Parameter               | Value |
|------------------------|-------|
|Bypass                  | True, False
|Branch Prediction       | None, Static, Dynamic, Dynamic Target
|Custom Function Unit    | True, False
|Instruction Cache Size  | 0-16KiB
|Data Cache Size         | 0-16KiB
|Hardware Multiplier     | True, False
|Hardware Divider        | True, False
|Single Cycle Multiplier | True, False
|Single Cycle Shifter    | True, False
|Safe                    | True, False

### CFU vs CPU

This framework allows users to explore a unique architectural design space that exists between a CPU and tightly coupled accelerator (CFU). The configurable nature of the soft-CPU allows for users to tradeoff CPU resources for accelerator resources. The figure below shows that CPU + CFU is a large design spectrum that can lie anywhere in between a simple MCU to full-blown accelerator.

![Alt text](../../docs/source/images/CFU_VS_CPU.png?raw=true "Title")

We hope you have fun exploring this large, unique design space enabled by CFU Playground!

