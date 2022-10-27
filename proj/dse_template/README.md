# Design Space Exploration in CFU Playground
This project template is intended for performing architectural design space exploration (DSE) in CFU Playground. 

## Prerequisites & Setup
1. Playground Installation
- Make sure you have run `$CFU_ROOT/scripts/setup`
- Make sure you have installed and entered Symbiflow env via `make install-sf` & `make enter-sf`
- Test this with `which symbiflow_synth`

2. Install the VexRiscv Build Tools
- Run `$CFU_ROOT/scripts/setup_vexriscv_build.sh`

3. Install Vizier 
- Run `$CFU_ROOT/scripts/setup_vizier.sh`

4. Test DSE 
- In `proj/dse_template` run `python vizier_dse.py`
- Sample output at end will look something like this:
```
EXITING DSE...

Optimal Trial Suggestion and Objective: ParameterDict(_items={'bypass': True, 'cfu': False, 'hardwareDiv': True, 'mulDiv': False, 'singleCycleShift': False, 'singleCycleMulDiv': True, 'safe': False, 'prediction': dynamic_target, 'iCacheSize': 4096.0, 'dCacheSize': 512.0}) Measurement(metrics={'cycles': Metric(value=16638.0, std=None), 'cells': Metric(value=1152797428.0, std=None)}, elapsed_secs=0.0, steps=0)
Optimal Trial Suggestion and Objective: ParameterDict(_items={'bypass': False, 'cfu': True, 'hardwareDiv': False, 'mulDiv': False, 'singleCycleShift': True, 'singleCycleMulDiv': True, 'safe': True, 'prediction': dynamic, 'iCacheSize': 4096.0, 'dCacheSize': 8192.0}) Measurement(metrics={'cycles': Metric(value=17932.0, std=None), 'cells': Metric(value=911708646.0, std=None)}, elapsed_secs=0.0, steps=0)
```

## Developer Flow
Similar to the typical Playground flow, developers should first profile the workload they would like to accelerate and then design a CFU to speedup the intended operation. After designing your CFU in the project, you can now perform design space exploration between your CFU and CPU. This is especially interesting if you are considering different versions of a CFU. It is also useful simply for optimizing the soft-CPU for your workload after you are happy with your CFU.

### Running Automated DSE with Vizier
- Diagram
- Changing number of Trials
- Build your own custom VexRiscv

### Parameters 
- Table

### CFU vs CPU
- Include picture of spectrum

