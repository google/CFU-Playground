#pragma once

#ifndef CFU_CONV1d_V12_PARAMS
#define CFU_CONV1d_V12_PARAMS

#define CFU_INITIALIZE 0
#define CFU_WRITE_INPUT_BUFFER 1
#define CFU_WRITE_KERNEL_BUFFER 2
#define CFU_WRITE_INPUT_OFFSET 3
#define CFU_WRITE_INPUT_OUTPUT_WIDTH 4
#define CFU_WRITE_INPUT_DEPTH 5
#define CFU_START_COMPUTATION 6
#define CFU_READ_ACCUMULATOR 7
#define CFU_WRITE_START_FILTER_X 8
#define CFU_FINISHED 9

#define CFU_READ_INPUT_BUFFER 10
#define CFU_READ_FILTER_BUFFER 11

#define CFU_WRITE_BIAS 12
#define CFU_WRITE_OUTPUT_MULTIPLIER 13
#define CFU_WRITE_OUTPUT_SHIFT 14
#define CFU_WRITE_OUTPUT_ACTIVATION_MIN 15
#define CFU_WRITE_OUTPUT_ACTIVATION_MAX 16
#define CFU_WRITE_OUTPUT_OFFSET 17

#endif  // CFU_CONV1d_V12_PARAMS