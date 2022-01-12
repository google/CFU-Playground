/* Copyright 2020 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "tensorflow/lite/micro/micro_allocator.h"

#include <cstddef>
#include <cstdint>

#include "flatbuffers/flatbuffers.h"  // from @flatbuffers
#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/core/api/error_reporter.h"
#include "tensorflow/lite/core/api/flatbuffer_conversions.h"
#include "tensorflow/lite/core/api/op_resolver.h"
#include "tensorflow/lite/core/api/tensor_utils.h"
#include "tensorflow/lite/kernels/internal/compatibility.h"
#include "tensorflow/lite/micro/compatibility.h"
#include "tensorflow/lite/micro/flatbuffer_utils.h"
#include "tensorflow/lite/micro/memory_helpers.h"
#include "tensorflow/lite/micro/memory_planner/greedy_memory_planner.h"
#include "tensorflow/lite/micro/memory_planner/micro_memory_planner.h"
#include "tensorflow/lite/micro/micro_arena_constants.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/simple_memory_allocator.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/schema/schema_utils.h"

namespace tflite {

namespace {

// Maximum number of scratch buffer requests per operator. Operator kernels that
// request more than this value will receive an exception.
constexpr size_t kMaxScratchBuffersPerOp = 12;

// Sentinel value used as a placeholder to mark a ScratchBufferRequest request
// needs a node id assignment.
constexpr int kUnassignedScratchBufferRequestIndex = -1;

// Used to hold information used during allocation calculations.
struct AllocationInfo {
  size_t bytes;
  void** output_ptr;
  int first_created;
  int last_used;
  int32_t offline_offset;
  bool needs_allocating;
};

constexpr char kOfflineMemAllocMetadata[] = "OfflineMemoryAllocation";
const TfLiteIntArray kZeroLengthIntArray = {};

class MicroBuiltinDataAllocator : public BuiltinDataAllocator {
 public:
  explicit MicroBuiltinDataAllocator(SimpleMemoryAllocator* memory_allocator)
      : memory_allocator_(memory_allocator) {}

  void* Allocate(size_t size, size_t alignment_hint) override {
    return memory_allocator_->AllocateFromTail(size, alignment_hint);
  }
  void Deallocate(void* data) override {
    // Do not deallocate, builtin data needs to be available for the life time
    // of the model.
  }

  TF_LITE_REMOVE_VIRTUAL_DELETE

 private:
  SimpleMemoryAllocator* memory_allocator_;
};

// A helper class to construct AllocationInfo array. This array contains the
// lifetime of tensors / scratch_buffer and will be used to calculate the memory
// plan. Methods need to be called in order from `Init`, `Add*`, to `Finish`.
class AllocationInfoBuilder {
 public:
  AllocationInfoBuilder(AllocationInfo* info, size_t tensor_count,
                        size_t scratch_buffer_count, ErrorReporter* reporter)
      : info_(info),
        tensor_count_(tensor_count),
        buffer_count_(scratch_buffer_count),
        reporter_(reporter) {}

  // Check if model contains offline planned buffer offsets.
  //  - If there's no metadata available, offline_planner_offsets is not set
  //  - If there's metadata available, offline_planner_offsets will point to the
  //    first offset in the metadata buffer list.
  TfLiteStatus GetOfflinePlannedOffsets(
      const Model* model, const int32_t** offline_planner_offsets);

  // Add allocaiton information for the tensors.
  TfLiteStatus AddTensors(const SubGraph* subgraph,
                          const int32_t* offline_offsets,
                          TfLiteEvalTensor* eval_tensors);

  // Add allocation information for the scratch buffers.
  TfLiteStatus AddScratchBuffers(
      internal::ScratchBufferRequest* scratch_buffer_requests,
      ScratchBufferHandle* scratch_buffer_handles);

  // Returns a pointer to the built AllocationInfo array.
  const AllocationInfo* Finish() const { return info_; }

 private:
  AllocationInfo* info_ = nullptr;
  size_t tensor_count_ = 0;
  size_t buffer_count_ = 0;
  ErrorReporter* reporter_ = nullptr;
};

TfLiteStatus AllocationInfoBuilder::AddTensors(const SubGraph* subgraph,
                                               const int32_t* offline_offsets,
                                               TfLiteEvalTensor* eval_tensors) {
  TFLITE_DCHECK(eval_tensors != nullptr);

  // Set up allocation info for all tensors.
  for (size_t i = 0; i < tensor_count_; ++i) {
    AllocationInfo* current = &info_[i];
    current->output_ptr = &(eval_tensors[i].data.data);

    TF_LITE_ENSURE_STATUS(
        TfLiteEvalTensorByteLength(&eval_tensors[i], &current->bytes));

    current->first_created = -1;
    current->last_used = -1;
    current->needs_allocating = (eval_tensors[i].data.data == nullptr) &&
                                (!subgraph->tensors()->Get(i)->is_variable());
    if (offline_offsets) {
      current->offline_offset = offline_offsets[i];
    } else {
      current->offline_offset = kOnlinePlannedBuffer;
    }
  }

  uint32_t operators_size = NumSubgraphOperators(subgraph);

  for (size_t i = 0;
       subgraph->inputs() != nullptr && i < subgraph->inputs()->size(); ++i) {
    const int tensor_index = subgraph->inputs()->Get(i);
    AllocationInfo* current = &info_[tensor_index];
    current->first_created = 0;
  }

  // Mark all outputs as persistent to the end of the invocation.
  for (size_t i = 0;
       subgraph->outputs() != nullptr && i < subgraph->outputs()->size(); ++i) {
    const int tensor_index = subgraph->outputs()->Get(i);
    AllocationInfo* current = &info_[tensor_index];
    current->last_used = operators_size - 1;
  }

  // Figure out when the first and last use of each tensor is.
  for (int i = (operators_size - 1); i >= 0; --i) {
    const auto* op = subgraph->operators()->Get(i);
    for (size_t n = 0; op->inputs() != nullptr && n < op->inputs()->size();
         ++n) {
      const int tensor_index = op->inputs()->Get(n);
      AllocationInfo* current = &info_[tensor_index];
      if (((current->last_used == -1) || (current->last_used < i))) {
        current->last_used = i;
      }
    }
    for (size_t n = 0; op->outputs() != nullptr && n < op->outputs()->size();
         ++n) {
      const int tensor_index = op->outputs()->Get(n);
      AllocationInfo* current = &info_[tensor_index];
      if ((current->first_created == -1) || (current->first_created > i)) {
        current->first_created = i;
      }
      // Since operator outputs are written to, they must be marked as used.
      if ((current->last_used == -1) || (current->last_used < i)) {
        current->last_used = i;
      }
    }
  }
  return kTfLiteOk;
}

// Get offline tensors allocation plan. See
// micro/docs/memory_management.md for more info.
TfLiteStatus AllocationInfoBuilder::GetOfflinePlannedOffsets(
    const Model* model, const int32_t** offline_planner_offsets) {
  if (model->metadata()) {
    for (size_t i = 0; i < model->metadata()->size(); ++i) {
      auto metadata = model->metadata()->Get(i);
      if (strncmp(metadata->name()->c_str(), kOfflineMemAllocMetadata,
                  strlen(kOfflineMemAllocMetadata)) == 0) {
        const flatbuffers::Vector<flatbuffers::Offset<Buffer>>* buffers =
            model->buffers();
        auto* buffer = (*buffers)[metadata->buffer()];
        auto* array = buffer->data();
        const uint32_t* metadata_buffer =
            reinterpret_cast<const uint32_t*>(array->data());
        const size_t nbr_tensors = static_cast<size_t>(metadata_buffer[2]);
        *offline_planner_offsets =
            reinterpret_cast<const int32_t*>(&metadata_buffer[3]);

        if (tensor_count_ != nbr_tensors) {
          TF_LITE_REPORT_ERROR(reporter_,
                               "Nbr of offline buffer offsets (%d) in metadata "
                               "not equal nbr tensors (%d)\n",
                               nbr_tensors, tensor_count_);
          return kTfLiteError;
        }
      }
    }
  }
  return kTfLiteOk;
}

TfLiteStatus AllocationInfoBuilder::AddScratchBuffers(
    internal::ScratchBufferRequest* scratch_buffer_requests,
    ScratchBufferHandle* scratch_buffer_handles) {
  // Set up allocation info for buffers.
  for (size_t i = tensor_count_; i < tensor_count_ + buffer_count_; ++i) {
    internal::ScratchBufferRequest* current_request =
        &(scratch_buffer_requests[i - tensor_count_]);
    ScratchBufferHandle* current_handle =
        &(scratch_buffer_handles[i - tensor_count_]);

    AllocationInfo* current = &info_[i];
    current->output_ptr = reinterpret_cast<void**>(&current_handle->data);
    current->bytes = current_request->bytes;
    current->first_created = current_request->node_idx;
    current->last_used = current_request->node_idx;
    current->offline_offset = kOnlinePlannedBuffer;
    current->needs_allocating = true;
  }
  return kTfLiteOk;
}

TfLiteStatus CreatePlan(ErrorReporter* error_reporter,
                        MicroMemoryPlanner* planner,
                        const AllocationInfo* allocation_info,
                        size_t allocation_info_size) {
  // Add the tensors to our allocation plan.
  for (size_t i = 0; i < allocation_info_size; ++i) {
    const AllocationInfo* current = &allocation_info[i];
    if (current->needs_allocating) {
      size_t aligned_bytes_required =
          AlignSizeUp(current->bytes, MicroArenaBufferAlignment());
      if (current->offline_offset == kOnlinePlannedBuffer) {
        TF_LITE_ENSURE_STATUS(
            planner->AddBuffer(error_reporter, aligned_bytes_required,
                               current->first_created, current->last_used));
      } else {
        TF_LITE_ENSURE_STATUS(planner->AddBuffer(
            error_reporter, aligned_bytes_required, current->first_created,
            current->last_used, current->offline_offset));
      }
    }
  }
  return kTfLiteOk;
}

TfLiteStatus CommitPlan(ErrorReporter* error_reporter,
                        MicroMemoryPlanner* planner, uint8_t* starting_point,
                        const AllocationInfo* allocation_info,
                        size_t allocation_info_size) {
  // Figure out the actual memory addresses for each buffer, based on the plan.
  int planner_index = 0;
  for (size_t i = 0; i < allocation_info_size; ++i) {
    const AllocationInfo* current = &allocation_info[i];
    if (current->needs_allocating) {
      int offset = -1;
      TF_LITE_ENSURE_STATUS(
          planner->GetOffsetForBuffer(error_reporter, planner_index, &offset));
      *current->output_ptr = reinterpret_cast<void*>(starting_point + offset);
      ++planner_index;
    }
  }
  return kTfLiteOk;
}
}  // namespace

namespace internal {

// Returns a pointer to any buffer associated with the flatbuffer tensor. Can
// return nullptr if no buffer is found.
void* GetFlatbufferTensorBuffer(
    const tflite::Tensor& flatbuffer_tensor,
    const flatbuffers::Vector<flatbuffers::Offset<Buffer>>* buffers) {
  // We need to figure out where the actual contents of this tensor are stored
  // in memory. We'll check to see if there's a serialized buffer (pretty much
  // the same as a constant op in TensorFlow) associated with this tensor first,
  // and if there is update the runtime structure to point to its location in
  // memory.
  // First see if there's any buffer information in the serialized tensor.
  // TODO(b/170379532): Add better unit tests to validate flatbuffer values.
  void* out_buffer = nullptr;
  if (auto* buffer = (*buffers)[flatbuffer_tensor.buffer()]) {
    // If we've found a buffer, does it have any data?
    if (auto* array = buffer->data()) {
      // If it has any data, is the data size larger than zero?
      if (array->size()) {
        // We've found a buffer with valid data, so update the runtime tensor
        // data structure to point to it.
        out_buffer = const_cast<void*>(static_cast<const void*>(array->data()));
      }
    }
    // TODO(petewarden): It's not clear in what circumstances we could have a
    // buffer in the serialized tensor, but it doesn't have any data in it. Is
    // that a validly-generated file, and if so what does it mean, or is it an
    // error condition? It would be good to tighten up the specification to make
    // it less ambiguous.
  }
  return out_buffer;
}

TfLiteStatus InitializeTfLiteTensorFromFlatbuffer(
    SimpleMemoryAllocator* allocator, bool allocate_temp,
    const tflite::Tensor& flatbuffer_tensor,
    const flatbuffers::Vector<flatbuffers::Offset<Buffer>>* buffers,
    ErrorReporter* error_reporter, TfLiteTensor* result) {
  TFLITE_DCHECK(result != nullptr);

  *result = {};
  // Make sure the serialized type is one we know how to deal with, and convert
  // it from a flatbuffer enum into a constant used by the kernel C API.
  TF_LITE_ENSURE_STATUS(ConvertTensorType(flatbuffer_tensor.type(),
                                          &result->type, error_reporter));
  // Make sure we remember if the serialized tensor is designated as a variable.
  result->is_variable = flatbuffer_tensor.is_variable();

  result->data.data = GetFlatbufferTensorBuffer(flatbuffer_tensor, buffers);

  // TODO(petewarden): Some of these paths aren't getting enough testing
  // coverage, so we should figure out some tests that exercise them.
  if (result->data.data == nullptr) {
    // The tensor contents haven't been set from a serialized buffer, so
    // make a note that they will be allocated from memory. The actual
    // allocation won't happen until later.
    result->allocation_type = kTfLiteArenaRw;
  } else {
    // We set the data from a serialized buffer, so record tha.
    result->allocation_type = kTfLiteMmapRo;
  }

  // Figure out what the size in bytes of the buffer is and store it.
  size_t type_size;
  TF_LITE_ENSURE_STATUS(BytesRequiredForTensor(
      flatbuffer_tensor, &result->bytes, &type_size, error_reporter));

  if (flatbuffer_tensor.shape() == nullptr) {
    // flatbuffer_tensor.shape() can return a nullptr in the case of a scalar
    // tensor.
    // TODO(b/188459715): figure out why const_cast is required here.
    result->dims = const_cast<TfLiteIntArray*>(&kZeroLengthIntArray);
  } else {
    // TFLM doesn't allow reshaping the tensor which requires dynamic memory
    // allocation so it is safe to drop the const qualifier. In the future, if
    // we really want to update the tensor shape, we can always pass in a new
    // TfLiteIntArray - especially we have to do so if the dimension is
    result->dims = FlatBufferVectorToTfLiteTypeArray(flatbuffer_tensor.shape());
  }

  // Copy the quantization information from the serialized data.
  const auto* src_quantization = flatbuffer_tensor.quantization();
  if (src_quantization && src_quantization->scale() &&
      (src_quantization->scale()->size() > 0) &&
      src_quantization->zero_point() &&
      (src_quantization->zero_point()->size() > 0)) {
    // Always populate the TfLiteTensor.params field, even if there are
    // per-channel quantization parameters.
    result->params.scale = src_quantization->scale()->Get(0);
    // Note that the zero_point field in the FlatBuffers schema is a 64-bit
    // integer, but the zero_point field in the TfLiteQuantizationParams struct
    // is a 32-bit integer.
    result->params.zero_point =
        static_cast<int32_t>(src_quantization->zero_point()->Get(0));

    // Populate per-channel quantization params.
    int channels = src_quantization->scale()->size();
    TfLiteAffineQuantization* quantization =
        allocate_temp
            ? reinterpret_cast<TfLiteAffineQuantization*>(
                  allocator->AllocateTemp(sizeof(TfLiteAffineQuantization),
                                          alignof(TfLiteAffineQuantization)))
            : reinterpret_cast<TfLiteAffineQuantization*>(
                  allocator->AllocateFromTail(
                      sizeof(TfLiteAffineQuantization),
                      alignof(TfLiteAffineQuantization)));
    if (quantization == nullptr) {
      TF_LITE_REPORT_ERROR(error_reporter,
                           "Unable to allocate TfLiteAffineQuantization.\n");
      return kTfLiteError;
    }

    // TODO(b/153688719): Reduce tail allocation by using a global zero-point
    // buffer. This value can not be reused from the flatbuffer since the
    // zero_point is stored as a int64_t.
    quantization->zero_point =
        allocate_temp
            ? reinterpret_cast<TfLiteIntArray*>(allocator->AllocateTemp(
                  TfLiteIntArrayGetSizeInBytes(channels),
                  alignof(TfLiteIntArray)))
            : reinterpret_cast<TfLiteIntArray*>(allocator->AllocateFromTail(
                  TfLiteIntArrayGetSizeInBytes(channels),
                  alignof(TfLiteIntArray)));
    if (quantization->zero_point == nullptr) {
      TF_LITE_REPORT_ERROR(error_reporter,
                           "Unable to allocate quantization->zero_point.\n");
      return kTfLiteError;
    }

    quantization->scale =
        FlatBufferVectorToTfLiteTypeArray(src_quantization->scale());

    quantization->zero_point->size = channels;
    int* zero_point_data = quantization->zero_point->data;
    for (int i = 0; i < channels; i++) {
      // As a space-saving optimization, zero point arrays for weights can be
      // reduced to a single value, since all zero points for weights are 0.
      zero_point_data[i] = src_quantization->zero_point()->size() ==
                                   src_quantization->scale()->size()
                               ? src_quantization->zero_point()->Get(i)
                               : src_quantization->zero_point()->Get(0);
    }
    // TODO(rocky): Need to add a micro_allocator test case that fails when
    // this is not copied:
    quantization->quantized_dimension = src_quantization->quantized_dimension();

    result->quantization = {kTfLiteAffineQuantization, quantization};
  }
  return kTfLiteOk;
}

TfLiteStatus InitializeTfLiteEvalTensorFromFlatbuffer(
    SimpleMemoryAllocator* allocator, const tflite::Tensor& flatbuffer_tensor,
    const flatbuffers::Vector<flatbuffers::Offset<Buffer>>* buffers,
    ErrorReporter* error_reporter, TfLiteEvalTensor* result) {
  *result = {};
  // Make sure the serialized type is one we know how to deal with, and convert
  // it from a flatbuffer enum into a constant used by the kernel C API.
  TF_LITE_ENSURE_STATUS(ConvertTensorType(flatbuffer_tensor.type(),
                                          &result->type, error_reporter));

  result->data.data = GetFlatbufferTensorBuffer(flatbuffer_tensor, buffers);

  if (flatbuffer_tensor.shape() == nullptr) {
    // flatbuffer_tensor.shape() can return a nullptr in the case of a scalar
    // tensor.
    result->dims = const_cast<TfLiteIntArray*>(&kZeroLengthIntArray);
  } else {
    result->dims = FlatBufferVectorToTfLiteTypeArray(flatbuffer_tensor.shape());
  }
  return kTfLiteOk;
}

}  // namespace internal

size_t MicroAllocator::GetDefaultTailUsage(bool is_memory_planner_given) {
  // TODO(b/208703041): a template version of AlignSizeUp to make expression
  // shorter.
  size_t total_size =
      AlignSizeUp(sizeof(SimpleMemoryAllocator),
                  alignof(SimpleMemoryAllocator)) +
      AlignSizeUp(sizeof(MicroAllocator), alignof(MicroAllocator)) +
      AlignSizeUp(sizeof(MicroBuiltinDataAllocator),
                  alignof(MicroBuiltinDataAllocator)) +
      AlignSizeUp(sizeof(SubgraphAllocations), alignof(SubgraphAllocations));
  if (!is_memory_planner_given) {
    total_size +=
        AlignSizeUp(sizeof(GreedyMemoryPlanner), alignof(GreedyMemoryPlanner));
  }
  return total_size;
}

MicroAllocator::MicroAllocator(SimpleMemoryAllocator* memory_allocator,
                               MicroMemoryPlanner* memory_planner,
                               ErrorReporter* error_reporter)
    : memory_allocator_(memory_allocator),
      memory_planner_(memory_planner),
      error_reporter_(error_reporter),
      model_is_allocating_(false) {}

MicroAllocator::~MicroAllocator() {}

MicroAllocator* MicroAllocator::Create(uint8_t* tensor_arena, size_t arena_size,
                                       MicroMemoryPlanner* memory_planner,
                                       ErrorReporter* error_reporter) {
  uint8_t* aligned_arena =
      AlignPointerUp(tensor_arena, MicroArenaBufferAlignment());
  size_t aligned_arena_size = tensor_arena + arena_size - aligned_arena;
  SimpleMemoryAllocator* memory_allocator = SimpleMemoryAllocator::Create(
      error_reporter, aligned_arena, aligned_arena_size);

  return Create(memory_allocator, memory_planner, error_reporter);
}

MicroAllocator* MicroAllocator::Create(uint8_t* tensor_arena, size_t arena_size,
                                       ErrorReporter* error_reporter) {
  uint8_t* aligned_arena =
      AlignPointerUp(tensor_arena, MicroArenaBufferAlignment());
  size_t aligned_arena_size = tensor_arena + arena_size - aligned_arena;
  SimpleMemoryAllocator* memory_allocator = SimpleMemoryAllocator::Create(
      error_reporter, aligned_arena, aligned_arena_size);

  // By default create GreedyMemoryPlanner.
  // If a different MemoryPlanner is needed, use the other api.
  uint8_t* memory_planner_buffer = memory_allocator->AllocateFromTail(
      sizeof(GreedyMemoryPlanner), alignof(GreedyMemoryPlanner));
  GreedyMemoryPlanner* memory_planner =
      new (memory_planner_buffer) GreedyMemoryPlanner();

  return Create(memory_allocator, memory_planner, error_reporter);
}

MicroAllocator* MicroAllocator::Create(SimpleMemoryAllocator* memory_allocator,
                                       MicroMemoryPlanner* memory_planner,
                                       ErrorReporter* error_reporter) {
  TFLITE_DCHECK(memory_allocator != nullptr);
  TFLITE_DCHECK(error_reporter != nullptr);
  TFLITE_DCHECK(memory_planner != nullptr);

  uint8_t* allocator_buffer = memory_allocator->AllocateFromTail(
      sizeof(MicroAllocator), alignof(MicroAllocator));
  MicroAllocator* allocator = new (allocator_buffer)
      MicroAllocator(memory_allocator, memory_planner, error_reporter);
  return allocator;
}

SubgraphAllocations* MicroAllocator::StartModelAllocation(const Model* model) {
  TFLITE_DCHECK(model != nullptr);

  if (model_is_allocating_) {
    TF_LITE_REPORT_ERROR(error_reporter_,
                         "MicroAllocator: Model allocation started before "
                         "finishing previously allocated model");
    return nullptr;
  }

  model_is_allocating_ = true;

  uint8_t* data_allocator_buffer = memory_allocator_->AllocateFromTail(
      sizeof(MicroBuiltinDataAllocator), alignof(MicroBuiltinDataAllocator));
  builtin_data_allocator_ =
      new (data_allocator_buffer) MicroBuiltinDataAllocator(memory_allocator_);

  if (InitScratchBufferData() != kTfLiteOk) {
    return nullptr;
  }

  // Allocate struct to store eval tensors, nodes and registrations.
  SubgraphAllocations* output = reinterpret_cast<SubgraphAllocations*>(
      memory_allocator_->AllocateFromTail(
          sizeof(SubgraphAllocations) * model->subgraphs()->size(),
          alignof(SubgraphAllocations)));
  if (output == nullptr) {
    MicroPrintf("Failed to allocate memory for model metadata.");
    return nullptr;
  }

  if (AllocateTfLiteEvalTensors(model, output) != kTfLiteOk ||
      AllocateNodeAndRegistrations(model, output) != kTfLiteOk) {
    return nullptr;
  }
  return output;
}

TfLiteStatus MicroAllocator::FinishModelAllocation(
    const Model* model, SubgraphAllocations* subgraph_allocations,
    ScratchBufferHandle** scratch_buffer_handles) {
  if (!model_is_allocating_) {
    TF_LITE_REPORT_ERROR(error_reporter_,
                         "MicroAllocator: Model allocation finished before "
                         "starting allocating model");
    return kTfLiteError;
  }

  // TODO(b/187993197): Track scratch buffers for each subgraph.
  for (size_t subgraph_idx = 0; subgraph_idx < model->subgraphs()->size();
       subgraph_idx++) {
    const SubGraph* subgraph = model->subgraphs()->Get(subgraph_idx);
    TFLITE_DCHECK(subgraph != nullptr);

    TF_LITE_ENSURE_STATUS(AllocateScratchBufferHandles(
        scratch_buffer_handles, scratch_buffer_request_count_));
    TF_LITE_ENSURE_STATUS(CommitStaticMemoryPlan(
        model, subgraph_allocations[subgraph_idx].tensors,
        *scratch_buffer_handles, subgraph_idx));
    TF_LITE_ENSURE_STATUS(AllocateVariables(
        subgraph, subgraph_allocations[subgraph_idx].tensors));
  }
  model_is_allocating_ = false;
  return kTfLiteOk;
}

void* MicroAllocator::AllocatePersistentBuffer(size_t bytes) {
  return memory_allocator_->AllocateFromTail(bytes,
                                             MicroArenaBufferAlignment());
}

TfLiteStatus MicroAllocator::RequestScratchBufferInArena(size_t bytes,
                                                         int subgraph_idx,
                                                         int* buffer_idx) {
  // All scratch buffer requests are stored in the head section of the arena
  // when a model is in the prepare phase. First align a scratch buffer request
  // pointer to the start of the head:
  internal::ScratchBufferRequest* requests = GetScratchBufferRequests();

  // Count the number of requested scratch buffers for the current node:
  size_t current_node_request_count = 0;
  for (size_t i = 0; i < scratch_buffer_request_count_; ++i) {
    if (requests[i].node_idx == kUnassignedScratchBufferRequestIndex) {
      ++current_node_request_count;
    }
  }

  // First, ensure that the per-kernel request has not exceeded the limit:
  if (current_node_request_count >= kMaxScratchBuffersPerOp) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Scratch buffer request exeeds limit per operator (%d)",
        kMaxScratchBuffersPerOp);
    return kTfLiteError;
  }

  // Initialize and assign values for the request at the current index:
  internal::ScratchBufferRequest* current_request =
      &requests[scratch_buffer_request_count_];
  *current_request = {};
  // Assign -1 as a sentinel value that will be updated when the node finishes
  // allocating:
  current_request->bytes = bytes;
  current_request->node_idx = kUnassignedScratchBufferRequestIndex;

  // Assign the current request index to the out-param:
  *buffer_idx = scratch_buffer_request_count_;

  // Bump the request count to prepare for the next request:
  ++scratch_buffer_request_count_;
  return kTfLiteOk;
}

TfLiteStatus MicroAllocator::FinishPrepareNodeAllocations(int node_id) {
  // When a node has finished preparing, all temp allocations performed by the
  // kernel should be cleaned up:
  ResetTempAllocations();

  // Find and update any new scratch buffer requests for the current node:
  internal::ScratchBufferRequest* requests = GetScratchBufferRequests();

  for (size_t i = 0; i < scratch_buffer_request_count_; ++i) {
    // A request with a node_idx of -1 is a sentinel value used to indicate this
    // was a new request for the current node. The allocator finally knows the
    // node index at this point. Assign the value and update the list of new
    // requests so the head section can be adjusted to allow for the next kernel
    // to allocate at most kMaxScratchBuffersPerOp requests:
    if (requests[i].node_idx == kUnassignedScratchBufferRequestIndex) {
      requests[i].node_idx = node_id;
    }
  }

  // Ensure that the head is re-adjusted to allow for another at-most
  // kMaxScratchBuffersPerOp scratch buffer requests in the next operator:
  TF_LITE_ENSURE_STATUS(memory_allocator_->SetHeadBufferSize(
      sizeof(internal::ScratchBufferRequest) *
          (scratch_buffer_request_count_ + kMaxScratchBuffersPerOp),
      alignof(internal::ScratchBufferRequest)));

  return kTfLiteOk;
}

size_t MicroAllocator::used_bytes() const {
  return memory_allocator_->GetUsedBytes();
}

TfLiteStatus MicroAllocator::AllocateNodeAndRegistrations(
    const Model* model, SubgraphAllocations* subgraph_allocations) {
  TFLITE_DCHECK(subgraph_allocations != nullptr);

  for (size_t subgraph_idx = 0; subgraph_idx < model->subgraphs()->size();
       subgraph_idx++) {
    const SubGraph* subgraph = model->subgraphs()->Get(subgraph_idx);
    TFLITE_DCHECK(subgraph != nullptr);

    uint32_t operators_size = NumSubgraphOperators(subgraph);

    // Initialize NodeAndRegistrations for the subgraph.
    NodeAndRegistration* output = reinterpret_cast<NodeAndRegistration*>(
        memory_allocator_->AllocateFromTail(
            sizeof(NodeAndRegistration) * operators_size,
            alignof(NodeAndRegistration)));
    if (output == nullptr) {
      TF_LITE_REPORT_ERROR(
          error_reporter_,
          "Failed to allocate memory for node_and_registrations.");
      return kTfLiteError;
    }
    subgraph_allocations[subgraph_idx].node_and_registrations = output;
  }
  return kTfLiteOk;
}
TfLiteTensor* MicroAllocator::AllocatePersistentTfLiteTensor(
    const Model* model, const SubgraphAllocations* subgraph_allocations,
    int tensor_index, int subgraph_index) {
  const SubGraph* subgraph = model->subgraphs()->Get(subgraph_index);
  TFLITE_DCHECK(subgraph != nullptr);

  // This value is allocated from persistent arena space. It is guaranteed to be
  // around for the lifetime of the application.
  TfLiteTensor* tensor = AllocatePersistentTfLiteTensorInternal();

  // Populate any fields from the flatbuffer, since this TfLiteTensor struct is
  // allocated in the persistent section of the arena, ensure that additional
  // allocations also take place in that section of the arena.
  if (PopulateTfLiteTensorFromFlatbuffer(
          model, tensor, tensor_index, subgraph_index,
          /*allocate_temp=*/false) != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter_,
                         "Failed to populate a persistent TfLiteTensor struct "
                         "from flatbuffer data!");
    return nullptr;
  }

  if (subgraph_allocations != nullptr) {
    // Tensor buffers that are allocated at runtime (e.g. non-weight buffers)
    // and not located in the flatbuffer are stored on the pre-allocated list of
    // TfLiteEvalTensors structs. These structs are the source of truth, simply
    // point the corresponding buffer to the new TfLiteTensor data value.
    tensor->data.data =
        subgraph_allocations[subgraph_index].tensors[tensor_index].data.data;
    // TfLiteEvalTensor structs must also be the source of truth for the
    // TfLiteTensor dims.
    tensor->dims =
        subgraph_allocations[subgraph_index].tensors[tensor_index].dims;
  }
  return tensor;
}

TfLiteTensor* MicroAllocator::AllocateTempTfLiteTensor(
    const Model* model, const SubgraphAllocations* subgraph_allocations,
    int tensor_index, int subgraph_index) {
  const SubGraph* subgraph = model->subgraphs()->Get(subgraph_index);
  TFLITE_DCHECK(subgraph != nullptr);

  // This value is allocated from temporary arena space. It is guaranteed to be
  // around for at least the scope of the calling function. Since this struct
  // allocation takes place in temp space, no need to own or cleanup.
  TfLiteTensor* tensor =
      reinterpret_cast<TfLiteTensor*>(memory_allocator_->AllocateTemp(
          sizeof(TfLiteTensor), alignof(TfLiteTensor)));

  // Populate any fields from the flatbuffer, since this TfLiteTensor struct is
  // allocated in the temp section of the arena, ensure that additional
  // allocations also take place in that section of the arena.
  if (PopulateTfLiteTensorFromFlatbuffer(model, tensor, tensor_index,
                                         subgraph_index,
                                         /*allocate_temp=*/true) != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Failed to populate a temp TfLiteTensor struct from flatbuffer data!");
    return nullptr;
  }

  if (subgraph_allocations != nullptr) {
    // Tensor buffers that are allocated at runtime (e.g. non-weight buffers)
    // and not located in the flatbuffer are stored on the pre-allocated list of
    // TfLiteEvalTensors structs. These structs are the source of truth, simply
    // point the corresponding buffer to the new TfLiteTensor data value.
    tensor->data.data =
        subgraph_allocations[subgraph_index].tensors[tensor_index].data.data;
    // TfLiteEvalTensor structs must also be the source of truth for the
    // TfLiteTensor dims.
    tensor->dims =
        subgraph_allocations[subgraph_index].tensors[tensor_index].dims;
  }
  return tensor;
}

void MicroAllocator::ResetTempAllocations() {
  memory_allocator_->ResetTempAllocations();
}

TfLiteStatus MicroAllocator::AllocateTfLiteEvalTensors(
    const Model* model, SubgraphAllocations* subgraph_allocations) {
  TFLITE_DCHECK(subgraph_allocations != nullptr);

  for (size_t subgraph_idx = 0; subgraph_idx < model->subgraphs()->size();
       subgraph_idx++) {
    const SubGraph* subgraph = model->subgraphs()->Get(subgraph_idx);
    TFLITE_DCHECK(subgraph != nullptr);

    size_t alloc_count = subgraph->tensors()->size();
    TfLiteEvalTensor* tensors =
        reinterpret_cast<TfLiteEvalTensor*>(memory_allocator_->AllocateFromTail(
            sizeof(TfLiteEvalTensor) * alloc_count, alignof(TfLiteEvalTensor)));
    if (tensors == nullptr) {
      TF_LITE_REPORT_ERROR(
          error_reporter_,
          "Failed to allocate memory for context->eval_tensors, "
          "%d bytes required",
          sizeof(TfLiteEvalTensor) * alloc_count);
      return kTfLiteError;
    }

    for (size_t i = 0; i < alloc_count; ++i) {
      TfLiteStatus status = internal::InitializeTfLiteEvalTensorFromFlatbuffer(
          memory_allocator_, *subgraph->tensors()->Get(i), model->buffers(),
          error_reporter_, &tensors[i]);
      if (status != kTfLiteOk) {
        TF_LITE_REPORT_ERROR(error_reporter_, "Failed to initialize tensor %d",
                             i);
        return kTfLiteError;
      }
    }
    subgraph_allocations[subgraph_idx].tensors = tensors;
  }
  return kTfLiteOk;
}
TfLiteStatus MicroAllocator::AllocateVariables(const SubGraph* subgraph,
                                               TfLiteEvalTensor* eval_tensors) {
  for (size_t i = 0; i < subgraph->tensors()->size(); ++i) {
    auto* tensor = subgraph->tensors()->Get(i);
    if (tensor->is_variable()) {
      size_t buffer_size;
      TF_LITE_ENSURE_STATUS(
          TfLiteEvalTensorByteLength(&eval_tensors[i], &buffer_size));

      eval_tensors[i].data.data = memory_allocator_->AllocateFromTail(
          buffer_size, MicroArenaBufferAlignment());

      if (eval_tensors[i].data.data == nullptr) {
        TF_LITE_REPORT_ERROR(error_reporter_,
                             "Failed to allocate variable tensor of size %d",
                             buffer_size);
        return kTfLiteError;
      }
    }
  }
  return kTfLiteOk;
}

TfLiteTensor* MicroAllocator::AllocatePersistentTfLiteTensorInternal() {
  return reinterpret_cast<TfLiteTensor*>(memory_allocator_->AllocateFromTail(
      sizeof(TfLiteTensor), alignof(TfLiteTensor)));
}

TfLiteStatus MicroAllocator::PopulateTfLiteTensorFromFlatbuffer(
    const Model* model, TfLiteTensor* tensor, int tensor_index,
    int subgraph_idx, bool allocate_temp) {
  // TODO(b/162311891): This method serves as a stub to ensure quantized
  // allocations in the tail can be recorded. Once the interpreter has APIs for
  // accessing buffers on TfLiteEvalTensor this method can be dropped.
  return internal::InitializeTfLiteTensorFromFlatbuffer(
      memory_allocator_, allocate_temp,
      *model->subgraphs()->Get(subgraph_idx)->tensors()->Get(tensor_index),
      model->buffers(), error_reporter_, tensor);
}

ErrorReporter* MicroAllocator::error_reporter() const {
  return error_reporter_;
}

TfLiteStatus MicroAllocator::CommitStaticMemoryPlan(
    const Model* model, TfLiteEvalTensor* eval_tensors,
    ScratchBufferHandle* scratch_buffer_handles, int subgraph_idx) {
  size_t head_usage = 0;
  // Create static memory plan
  // 1. Calculate AllocationInfo to know the lifetime of each tensor/buffer.
  // 2. Add them into the planner (such as the GreedyMemoryPlanner).
  // 3. Static memory planning using the planner.
  // 4. Set tensor/buffer pointers based on the offsets from the previous step.
  //
  // Note that AllocationInfo is only needed for creating the plan. It will be
  // allocated from the temp section and cleaned up at the bottom of this
  // function.

  const SubGraph* subgraph = model->subgraphs()->Get(subgraph_idx);
  size_t allocation_info_count =
      subgraph->tensors()->size() + scratch_buffer_request_count_;
  size_t bytes = sizeof(AllocationInfo) * allocation_info_count;

  // Allocate an array of AllocationInfo structs from the temp section. This
  // struct will be used by AllocationInfoBuilder to find buffer usage.
  AllocationInfo* allocation_info = reinterpret_cast<AllocationInfo*>(
      memory_allocator_->AllocateTemp(bytes, alignof(AllocationInfo)));
  if (allocation_info == nullptr) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Failed to allocate memory for allocation_info, %d bytes required",
        bytes);
    return kTfLiteError;
  }

  // Use the AllocationInfoBuilder class to help determine where buffers are
  // used in the subgraph.
  AllocationInfoBuilder builder(allocation_info, subgraph->tensors()->size(),
                                scratch_buffer_request_count_, error_reporter_);

  const int32_t* offline_planner_offsets = nullptr;
  TF_LITE_ENSURE_STATUS(
      builder.GetOfflinePlannedOffsets(model, &offline_planner_offsets));
  TF_LITE_ENSURE_STATUS(
      builder.AddTensors(subgraph, offline_planner_offsets, eval_tensors));

  internal::ScratchBufferRequest* scratch_buffer_requests =
      GetScratchBufferRequests();

  TF_LITE_ENSURE_STATUS(builder.AddScratchBuffers(scratch_buffer_requests,
                                                  scratch_buffer_handles));

  // Remaining arena size that memory planner can use for calculating offsets.
  size_t remaining_arena_size =
      memory_allocator_->GetAvailableMemory(MicroArenaBufferAlignment());
  uint8_t* planner_arena = memory_allocator_->AllocateTemp(
      remaining_arena_size, MicroArenaBufferAlignment());
  TF_LITE_ENSURE(error_reporter_, planner_arena != nullptr);
  memory_planner_->Init(planner_arena, remaining_arena_size);
  TF_LITE_ENSURE_STATUS(CreatePlan(error_reporter_, memory_planner_,
                                   allocation_info, allocation_info_count));

  // Reset all temp allocations used above:
  memory_allocator_->ResetTempAllocations();

  size_t actual_available_arena_size =
      memory_allocator_->GetAvailableMemory(MicroArenaBufferAlignment());

  // Make sure we have enough arena size.
  if (memory_planner_->GetMaximumMemorySize() > actual_available_arena_size) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Arena size is too small for all buffers. Needed %u but only "
        "%u was available.",
        memory_planner_->GetMaximumMemorySize(), actual_available_arena_size);
    return kTfLiteError;
  }
  // Commit the plan.
  TF_LITE_ENSURE_STATUS(CommitPlan(error_reporter_, memory_planner_,
                                   memory_allocator_->GetHeadBuffer(),
                                   allocation_info, allocation_info_count));
#ifdef TF_LITE_SHOW_MEMORY_USE
  memory_planner_->PrintMemoryPlan();
#endif
  head_usage = memory_planner_->GetMaximumMemorySize();

  // The head is used to store memory plans for one model at a time during the
  // model preparation stage, and is re-purposed to store scratch buffer handles
  // during model invocation. The head must be as large as the greater of the
  // largest model memory plan's size and the total space required for all
  // scratch buffer handles.
  if (max_head_buffer_usage_ < head_usage) {
    max_head_buffer_usage_ = head_usage;
  }

  // The head is used for storing scratch buffer allocations before finalizing a
  // memory plan in this function. Ensure that the head is set to the largest
  // memory plan sent through the allocator:
  TF_LITE_ENSURE_STATUS(memory_allocator_->SetHeadBufferSize(
      max_head_buffer_usage_, MicroArenaBufferAlignment()));
  return kTfLiteOk;
}

TfLiteStatus MicroAllocator::AllocateScratchBufferHandles(
    ScratchBufferHandle** scratch_buffer_handles, size_t handle_count) {
  TFLITE_DCHECK(scratch_buffer_handles != nullptr);

  if (scratch_buffer_request_count_ == 0) {
    // No scratch buffer requests were requested during model allocation.
    return kTfLiteOk;
  }

  // Allocate a consecutive block of memory store the scratch buffer handles.
  // This alignment ensures quick lookup during inference time for the model:
  *scratch_buffer_handles = reinterpret_cast<ScratchBufferHandle*>(
      memory_allocator_->AllocateFromTail(
          sizeof(ScratchBufferHandle) * handle_count,
          alignof(ScratchBufferHandle)));

  return kTfLiteOk;
}

TfLiteStatus MicroAllocator::InitScratchBufferData() {
  // A model is preparing to allocate resources, ensure that scratch buffer
  // request counter is cleared:
  scratch_buffer_request_count_ = 0;

  // All requests will be stored in the head section. Each kernel is allowed at
  // most kMaxScratchBuffersPerOp requests. Adjust the head to reserve at most
  // that many requests to begin:
  TF_LITE_ENSURE_STATUS(memory_allocator_->SetHeadBufferSize(
      sizeof(internal::ScratchBufferRequest) * kMaxScratchBuffersPerOp,
      alignof(internal::ScratchBufferRequest)));

  return kTfLiteOk;
}

internal::ScratchBufferRequest* MicroAllocator::GetScratchBufferRequests() {
  return reinterpret_cast<internal::ScratchBufferRequest*>(
      AlignPointerUp(memory_allocator_->GetHeadBuffer(),
                     alignof(internal::ScratchBufferRequest)));
}

BuiltinDataAllocator* MicroAllocator::GetBuiltinDataAllocator() {
  return builtin_data_allocator_;
}

}  // namespace tflite
