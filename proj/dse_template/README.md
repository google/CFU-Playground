# Design Space Exploration in CFU Playground

## Prerequisites
1. Playground Installation
- Make sure you have run `$CFU_ROOT/scripts/setup`
- Make sure you have installed and entered Symbiflow env via `make enter-sf`
- Test this with `which symbiflow_synth`

2. Install the VexRiscv Build Tools
- Run `$CFU_ROOT/scripts/setup_vexriscv_build.sh`

3. Install Vizier 
- Run `$CFU_ROOT/scripts/setup_vizier.sh`

4. Test DSE
- In `proj/dse_template` run `python vizier_dse.py`

## More info coming soon
- DSE Developer flow
- Changing number of Trials
- Build your own custom VexRiscv
- CPU vs CFU
