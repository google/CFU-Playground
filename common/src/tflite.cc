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
#include "playground_util/random.h"
#include "proj_tflite.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_profiler.h"
#include "tensorflow/lite/schema/schema_generated.h"

#ifdef TF_LITE_SHOW_MEMORY_USE
#include "tensorflow/lite/micro/recording_micro_interpreter.h"
#define INTERPRETER_TYPE RecordingMicroInterpreter
#else
#define INTERPRETER_TYPE MicroInterpreter
#endif

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

// C++ 11 does not have a constexpr std::max.
// For this reason, a small implementation is written.
template <typename T>
constexpr T const& const_max(const T& x) {
  return x;
}

template <typename T, typename... Args>
constexpr T const& const_max(const T& x, const T& y, const Args&... rest) {
  return const_max(x > y ? x : y, rest...);
}

// Get the smallest kTensorArenaSize possible.
constexpr int kTensorArenaSize = const_max<int>(
#ifdef INCLUDE_MODEL_PDTI8
    81 * 1024,
#endif
#ifdef INCLUDE_MODEL_MICRO_SPEECH
    7 * 1024,
#endif
#ifdef INCLUDE_MODEL_MAGIC_WAND
    5 * 1024,
#endif
#ifdef INCLUDE_MODEL_MNV2
    800 * 1024,
#endif
#ifdef INCLUDE_MODEL_HPS
    1024 * 1024,
#endif
#ifdef INLCUDE_MODEL_MLCOMMONS_TINY_V01_ANOMD
    3 * 1024,
#endif
#ifdef INLCUDE_MODEL_MLCOMMONS_TINY_V01_IMGC
    53 * 1024,
#endif
#ifdef INLCUDE_MODEL_MLCOMMONS_TINY_V01_KWS
    23 * 1024,
#endif
#ifdef INLCUDE_MODEL_MLCOMMONS_TINY_V01_VWW
    99 * 1024,
#endif
    0 /* When no models defined, we don't need a tensor arena. */
);

static uint8_t tensor_arena[kTensorArenaSize];
}  // anonymous namespace

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
  static tflite::MicroProfiler micro_profiler;
  profiler = &micro_profiler;
}

void tflite_load_model(const unsigned char* model_data,
                       unsigned int model_length) {
  tflite_init();
  tflite_preload(model_data, model_length);
  if (interpreter) {
    interpreter->~INTERPRETER_TYPE();
    interpreter = nullptr;
  }

  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(model_data);

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

#ifdef TF_LITE_SHOW_MEMORY_USE
  interpreter->GetMicroAllocator().PrintAllocations();
#endif

  // Get information about the memory area to use for the model's input.
  auto input = interpreter->input(0);
  auto dims = input->dims;
  printf("Input: %d bytes, %d dims:", input->bytes, dims->size);
  for (int ii = 0; ii < dims->size; ++ii) {
    printf(" %d", dims->data[ii]);
  }
  puts("\n");
}

void tflite_set_input_zeros(void) {
  auto input = interpreter->input(0);
  memset(input->data.int8, 0, input->bytes);
  printf("Zeroed %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

void tflite_set_input_zeros_float() {
  auto input = interpreter->input(0);
  memset(input->data.f, 0, input->bytes);
  printf("Zeroed %d bytes at 0x%p\n", input->bytes, input->data.f);
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

void tflite_set_input_float(const float* data) {
  auto input = interpreter->input(0);
  memcpy(input->data.f, data, input->bytes);
  printf("Copied %d bytes at 0x%p\n", input->bytes, input->data.f);
}

void tflite_randomize_input(int64_t seed) {
  int64_t r = seed;
  auto input = interpreter->input(0);
  for (size_t i = 0; i < input->bytes; i++) {
    input->data.int8[i] = static_cast<int8_t>(next_pseudo_random(&r));
  }
  printf("Set %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

void tflite_set_grid_input(void) {
  auto input = interpreter->input(0);
  size_t height = input->dims->data[1];
  size_t width = input->dims->data[2];
  for (size_t y = 0; y < height; y++) {
    for (size_t x = 0; x < width; x++) {
      int8_t val = (y & 0x20) & (x & 0x20) ? -128 : 127;
      input->data.int8[x + y * width] = val;
    }
  }
  printf("Set %d bytes at 0x%p\n", input->bytes, input->data.int8);
}

int8_t* tflite_get_output() { return interpreter->output(0)->data.int8; }

float* tflite_get_output_float() { return interpreter->output(0)->data.f; }

void tflite_classify() {
  // Run the model on this input and make sure it succeeds.
  profiler->ClearEvents();
  perf_reset_all_counters();
  perf_set_mcycle(0);
  if (kTfLiteOk != interpreter->Invoke()) {
    puts("Invoke failed.");
  }
  unsigned int cyc = perf_get_mcycle();
#ifndef NPROFILE
  profiler->Log();
#endif
  perf_print_all_counters();
  perf_print_value(cyc);
  printf(" cycles total\n");
}

int8_t* get_input() { return interpreter->input(0)->data.int8; }
