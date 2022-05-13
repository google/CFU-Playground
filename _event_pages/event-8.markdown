---
layout: page
title:  "Navigating CFU Playground"
---

CFU Playground is a collection of many different packages. 
Below we have outlined where some of the commonly asked for files are outside of developing a CFU.
All paths specified begin from your local CFU-Playground root. 

<div id="toc_container" style="position: absolute" markdown="1">
<p class="toc_title">Contents</p>

* TOC
{:toc}
</div>

### Software
* TFLM Models:`common/src/models`
* RISC-V Compiler: `CFU-Playground/env/conda/envs/cfu-common/bin`

### Gateware
* VexRiscv CPU RTL:`soc/vexriscv`
* Litex SoC:
* Synthesis Stats:  
`soc/build/[board].[project_name]/gateware/[board].rpt`
* Bitstream:

### Hardware
* Renode: `third_party/renode`
* Workflow for each board:`soc/board_specific_workflows` 

### Misc
* Third Party: `third_party/` contains src for Renode, TFLM, and other python packages, etc. needed and used in CFU-Playground 
