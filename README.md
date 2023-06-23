# RISC-V SIMD extension for the AI workload

This project is a fork of CFU-Playground framework, that allows AI workload running in TFLM acceleration with FPGA and CFU for RISC-V architecture 

## CFU Playground

[Link to original README](https://github.com/google/CFU-Playground)

## Docs
This project is my bachelor's thesis project. It is planned to submit it as IEEE conference paper in the future.

- Final thesis pdf can be found [here](/docs/Bachelor_Thesis_Pavlo_Hilei.pdf)
- Read-only link to the overleaf of thesis pdf [here](https://www.overleaf.com/read/sfmhvtrpgxpn)
- Also, some project documentation and reports are found in the Notion

## Model

### Datasets
2 different datasets where tried:
- [RadioML 2016(A,B)](https://www.deepsig.ai/datasets)
- Based on the following matlab [generation code](https://www.mathworks.com/help/deeplearning/ug/modulation-classification-with-deep-learning.html). Matlab dataset was generated with SNR in ranges \[0:29\]dB and \[-30:29\]dB to compare models performance. 

Difference between different characteristics of datasets can be found in Table 4.1 of thesis. 
Model that is trained on only good data (SNR > 0) performs better on good data, then dataset trained on good and bad data. But model trained on good and bad data performs much better on bad data.


### Models architectures
Generally two models architecture were trained:
- Transformer Encoder
- CNN

Models vizualizations are shown in thesis in Figures 4.2 and 4.3

Different hyper parameters where fine-tuned:
**CNN**
- Filter size
- Model width (number of channels)
- Model depth

**Encoder**
- Filter size
- Depth (number of encoder layers)
- Width

For acceleration `CNN_1` was chosen
![](/media/CNN_1_5.svg)

## Accelerator
Accelerator for developed iteratively, as CFU-Playground ideology suggests. 
All modifications and evolution overall is described in thesis. Final design (for bachelors) does multiply-accumulate between input and filter. At the end, quantization is performed to fit accumulated value back to int8. Input buffer is ring buffer, number of elements accumulated per clock is configurable. Due to limitations of CFU, data must be copied into temporary buffer. 

![](/media/cfu_v8_6.svg)