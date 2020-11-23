#include "tflite.h"

#include "tensorflow/lite/micro/examples/person_detection_experimental/detection_responder.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/image_provider.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/model_settings.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/person_detect_model_data.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/person_image_data.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"


// For e
void * __dso_handle = &__dso_handle;


//
// Setup TFLM
// Globals, used for compatibility with Arduino-style sketches.
namespace {
tflite::ErrorReporter* error_reporter = nullptr;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;

// In order to use optimized tensorflow lite kernels, a signed int8_t quantized
// model is preferred over the legacy unsigned model format. This means that
// throughout this project, input images must be converted from unisgned to
// signed format. The easiest and quickest way to convert from unsigned to
// signed 8-bit integers is to subtract 128 from the unsigned value to get a
// signed value.

// An area of memory to use for input, output, and intermediate arrays.
constexpr int kTensorArenaSize = 136 * 1024;
static uint8_t tensor_arena[kTensorArenaSize];
}  // namespace

// The name of this function is important for Arduino compatibility.
void initTfLite() {
  // Set up logging. Google style is to avoid globals or statics because of
  // lifetime uncertainty, but since this has a trivial destructor it's okay.
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;

  printf("g_no_person_data_size: %d\n", g_no_person_data_size);
  printf("g_person_data_size: %d\n", g_person_data_size);

  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(g_person_detect_model_data);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  // Pull in only the operation implementations we need.
  // This relies on a complete list of all the ops needed by this graph.
  // An easier approach is to just use the AllOpsResolver, but this will
  // incur some penalty in code space for op implementations that are not
  // needed by this graph.
  //
  // tflite::AllOpsResolver resolver;
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::MicroMutableOpResolver<5> micro_op_resolver;
  micro_op_resolver.AddAveragePool2D();
  micro_op_resolver.AddConv2D();
  micro_op_resolver.AddDepthwiseConv2D();
  micro_op_resolver.AddReshape();
  micro_op_resolver.AddSoftmax();

  // Build an interpreter to run the model with.
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::MicroInterpreter static_interpreter(
      model, micro_op_resolver, tensor_arena, kTensorArenaSize, error_reporter);
  interpreter = &static_interpreter;

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed");
    return;
  }

  // Get information about the memory area to use for the model's input.
  input = interpreter->input(0);
  auto dims = input->dims;
  printf("Input ?, %d bytes, %d dims:", input->bytes, dims->size);
  for (int ii=0; ii<dims->size; ++ii) {
    printf(" %d", dims->data[ii]);
  }
  puts("\n");
}

int8_t *get_input() {
  return input->data.int8;
}

void load_person() {
  memcpy(input->data.int8, g_person_data, g_person_data_size);
  printf("Copy %x bytes from %p to %p\n", g_person_data_size, g_person_data, input->data.int8);
  printf("kNumCols %d, kNumRows %d, kNumChannels %d, kMaxImageSize %d\n", kNumCols, kNumRows, kNumChannels, kMaxImageSize);
}

void load_no_person() {
  memcpy(input->data.int8, g_no_person_data, g_no_person_data_size);
  printf("Copy %x bytes from %p to %p\n", g_no_person_data_size,g_no_person_data, input->data.int8);
  printf("kNumCols %d, kNumRows %d, kNumChannels %d, kMaxImageSize %d\n", kNumCols, kNumRows, kNumChannels, kMaxImageSize);
}

void load_zeros() {
  memset(input->data.int8, 0, kMaxImageSize);
  printf("Zero %x bytes at %p\n", kMaxImageSize, input->data.int8);
}

void classify(int8_t *person_score, int8_t *no_person_score) {
  // image ought to be loaded already
  printf(">>%d\n", input->data.int8[0]);

  // Run the model on this input and make sure it succeeds.
  if (kTfLiteOk != interpreter->Invoke()) {
    TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed.");
  }

  TfLiteTensor* output = interpreter->output(0);

  // Process the inference results.
  *person_score = output->data.int8[kPersonIndex];
  *no_person_score = output->data.int8[kNotAPersonIndex];
}
