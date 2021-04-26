// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "tflite.h"

#include "perf.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_profiler.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

#ifdef SHOW_MEMORY_USE
#include "tensorflow/lite/micro/recording_micro_interpreter.h"
#define INTERPRETER_TYPE RecordingMicroInterpreter
#else
#define INTERPRETER_TYPE MicroInterpreter
#endif

//
// Unit test prototypes. Because of the way these names are generated, they are
// not defined in any include file. The actual tests are in test_name.cc - e.g
// conv_test is defined in conv_test.cc.
extern int conv_test(int argc, char** argv);
extern int depthwise_conv_test(int argc, char** argv);

// Run tflite unit tests
void tflite_do_tests() {
  // conv test from conv_test.cc
  puts("\nCONV TEST:");
  conv_test(0, NULL);
  // depthwise conv test from depthwise_conv_test.cc
  puts("DEPTHWISE_CONV TEST:");
  depthwise_conv_test(0, NULL);
}

// For C++ exceptions
void* __dso_handle = &__dso_handle;

//
// TfLM global objects
namespace {
tflite::ErrorReporter* error_reporter = nullptr;
tflite::MicroOpResolver* op_resolver = nullptr;
tflite::MicroProfiler* profiler = nullptr;

const tflite::Model* model = nullptr;
tflite::INTERPRETER_TYPE* interpreter = nullptr;

// An area of memory to use for input, output, and intermediate arrays.
// constexpr int kTensorArenaSize = 136 * 1024;
#ifdef INCLUDE_MODEL_MNV2
constexpr int kTensorArenaSize = 800 * 1024;
#else
constexpr int kTensorArenaSize = 81 * 1024;
#endif
static uint8_t tensor_arena[kTensorArenaSize];
}  // namespace

static void tflite_init() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  // Sets up error reporting etc
  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;
  TF_LITE_REPORT_ERROR(error_reporter, "Error_reporter OK!");

  // Pull in only the operation implementations we need.
  // This relies on a complete list of all the ops needed by this graph.
  // An easier approach is to just use the AllOpsResolver, but this will
  // incur some penalty in code space for op implementations that are not
  // needed by this graph.
  //
  static tflite::AllOpsResolver resolver;
  op_resolver = &resolver;
  // // NOLINTNEXTLINE(runtime-global-variables)
  // static tflite::MicroMutableOpResolver<8> micro_op_resolver;
  // micro_op_resolver.AddAveragePool2D();
  // micro_op_resolver.AddConv2D();
  // micro_op_resolver.AddDepthwiseConv2D();
  // micro_op_resolver.AddReshape();
  // micro_op_resolver.AddSoftmax();

  // // needed for jon's model conv2d/relu, maxpool2d, reshape, fullyconnected,
  // logistic micro_op_resolver.AddMaxPool2D();
  // micro_op_resolver.AddFullyConnected();
  // micro_op_resolver.AddLogistic();

  // // needed for MODEL=magic_wand_full_i8
  // // micro_op_resolver.AddQuantize();
  // op_resolver = &micro_op_resolver;

  // profiler
  static tflite::MicroProfiler micro_profiler(error_reporter);
  profiler = &micro_profiler;
}

void tflite_load_model(const unsigned char* model_data) {
  tflite_init();
  if (interpreter) {
    interpreter->~INTERPRETER_TYPE();
    interpreter = nullptr;
  }

  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(model_data);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  // Build an interpreter to run the model with.
  // NOLINTNEXTLINE(runtime-global-variables)
  alignas(tflite::INTERPRETER_TYPE) static unsigned char
      buf[sizeof(tflite::INTERPRETER_TYPE)];
  interpreter = new (buf)
      tflite::INTERPRETER_TYPE(model, *op_resolver, tensor_arena,
                               kTensorArenaSize, error_reporter, profiler);

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed");
    return;
  }

  // Get information about the memory area to use for the model's input.
  auto input = interpreter->input(0);
  auto dims = input->dims;
  printf("Input: %d bytes, %d dims:", input->bytes, dims->size);
  for (int ii = 0; ii < dims->size; ++ii) {
    printf(" %d", dims->data[ii]);
  }
  puts("\n");

#ifdef SHOW_MEMORY_USE
  interpreter->GetMicroAllocator().PrintAllocations();
#endif

}

void tflite_set_input_zeros() {
  auto input = interpreter->input(0);
  memset(input->data.int8, 0, input->bytes);
  printf("Zeroed %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

void tflite_set_input(const void* data) {
  auto input = interpreter->input(0);
  memcpy(input->data.int8, data, input->bytes);
  printf("Copied %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

void tflite_set_input_unsigned(const unsigned char* data) {
  auto input = interpreter->input(0);
  for (size_t i = 0; i < input->bytes; i++) {
    input->data.int8[i] = (int)data[i] - 127;
  }
  printf("Set %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

int8_t* tflite_get_output() { return interpreter->output(0)->data.int8; }

void tflite_classify() {
  // Run the model on this input and make sure it succeeds.
  perf_reset_all_counters();
  perf_set_mcycle(0);
  if (kTfLiteOk != interpreter->Invoke()) {
    TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed.");
  }
  unsigned int cyc = perf_get_mcycle();
  perf_print_all_counters();
  perf_print_value(cyc);
  printf(" cycles total\n");

  printf("Arena used bytes: %llu\n",
         (long long unsigned)(interpreter->arena_used_bytes()));
}

int8_t* get_input() { return interpreter->input(0)->data.int8; }
