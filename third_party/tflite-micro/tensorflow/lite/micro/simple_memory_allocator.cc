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

#include "tensorflow/lite/micro/simple_memory_allocator.h"

#include <cstddef>
#include <cstdint>
#include <new>

#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/core/api/error_reporter.h"
#include "tensorflow/lite/kernels/internal/compatibility.h"
#include "tensorflow/lite/micro/memory_helpers.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"

namespace tflite {

SimpleMemoryAllocator::SimpleMemoryAllocator(ErrorReporter* error_reporter,
                                             uint8_t* buffer_head,
                                             uint8_t* buffer_tail)
    : error_reporter_(error_reporter),
      buffer_head_(buffer_head),
      buffer_tail_(buffer_tail),
      head_(buffer_head),
      tail_(buffer_tail),
      temp_(buffer_head_) {}

SimpleMemoryAllocator::SimpleMemoryAllocator(ErrorReporter* error_reporter,
                                             uint8_t* buffer,
                                             size_t buffer_size)
    : SimpleMemoryAllocator(error_reporter, buffer, buffer + buffer_size) {}

/* static */
SimpleMemoryAllocator* SimpleMemoryAllocator::Create(
    ErrorReporter* error_reporter, uint8_t* buffer_head, size_t buffer_size) {
  TFLITE_DCHECK(error_reporter != nullptr);
  TFLITE_DCHECK(buffer_head != nullptr);
  SimpleMemoryAllocator tmp =
      SimpleMemoryAllocator(error_reporter, buffer_head, buffer_size);

  // Allocate enough bytes from the buffer to create a SimpleMemoryAllocator.
  // The new instance will use the current adjusted tail buffer from the tmp
  // allocator instance.
  uint8_t* allocator_buffer = tmp.AllocateFromTail(
      sizeof(SimpleMemoryAllocator), alignof(SimpleMemoryAllocator));
  // Use the default copy constructor to populate internal states.
  return new (allocator_buffer) SimpleMemoryAllocator(tmp);
}

SimpleMemoryAllocator::~SimpleMemoryAllocator() {}

TfLiteStatus SimpleMemoryAllocator::SetHeadBufferSize(size_t size,
                                                      size_t alignment) {
  if (head_ != temp_) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Internal error: SetHeadBufferSize() needs to be called "
        "after ResetTempAllocations().");
    return kTfLiteError;
  }

  uint8_t* const aligned_result = AlignPointerUp(buffer_head_, alignment);
  const size_t available_memory = tail_ - aligned_result;
  if (available_memory < size) {
    TF_LITE_REPORT_ERROR(
        error_reporter_,
        "Failed to set head size. Requested: %u, available %u, missing: %u",
        size, available_memory, size - available_memory);
    return kTfLiteError;
  }
  head_ = aligned_result + size;
  temp_ = head_;

  return kTfLiteOk;
}

uint8_t* SimpleMemoryAllocator::AllocateFromTail(size_t size,
                                                 size_t alignment) {
  uint8_t* const aligned_result = AlignPointerDown(tail_ - size, alignment);
  if (aligned_result < head_) {
#ifndef TF_LITE_STRIP_ERROR_STRINGS
    const size_t missing_memory = head_ - aligned_result;
    TF_LITE_REPORT_ERROR(error_reporter_,
                         "Failed to allocate tail memory. Requested: %u, "
                         "available %u, missing: %u",
                         size, size - missing_memory, missing_memory);
#endif
    return nullptr;
  }
  tail_ = aligned_result;
  return aligned_result;
}

uint8_t* SimpleMemoryAllocator::AllocateTemp(size_t size, size_t alignment) {
  uint8_t* const aligned_result = AlignPointerUp(temp_, alignment);
  const size_t available_memory = tail_ - aligned_result;
  if (available_memory < size) {
    TF_LITE_REPORT_ERROR(error_reporter_,
                         "Failed to allocate temp memory. Requested: %u, "
                         "available %u, missing: %u",
                         size, available_memory, size - available_memory);
    return nullptr;
  }
  temp_ = aligned_result + size;
  temp_buffer_ptr_check_sum_ ^= (reinterpret_cast<intptr_t>(aligned_result));
  temp_buffer_count_++;
  return aligned_result;
}

void SimpleMemoryAllocator::DeallocateTemp(uint8_t* temp_buf) {
  temp_buffer_ptr_check_sum_ ^= (reinterpret_cast<intptr_t>(temp_buf));
  temp_buffer_count_--;
}

bool SimpleMemoryAllocator::IsAllTempDeallocated() {
  if (temp_buffer_count_ != 0 || temp_buffer_ptr_check_sum_ != 0) {
    MicroPrintf(
        "Number of allocated temp buffers: %d. Checksum passing status: %d",
        temp_buffer_count_, !temp_buffer_ptr_check_sum_);
    return false;
  }
  return true;
}

void SimpleMemoryAllocator::ResetTempAllocations() {
  // TODO(b/209453859): enable error check based on IsAllTempDeallocated after
  // all AllocateTemp have been paird with DeallocateTemp
  temp_ = head_;
}

uint8_t* SimpleMemoryAllocator::GetHeadBuffer() const { return buffer_head_; }

size_t SimpleMemoryAllocator::GetHeadUsedBytes() const {
  return head_ - buffer_head_;
}

size_t SimpleMemoryAllocator::GetTailUsedBytes() const {
  return buffer_tail_ - tail_;
}

size_t SimpleMemoryAllocator::GetAvailableMemory(size_t alignment) const {
  uint8_t* const aligned_temp = AlignPointerUp(temp_, alignment);
  uint8_t* const aligned_tail = AlignPointerDown(tail_, alignment);
  return aligned_tail - aligned_temp;
}

size_t SimpleMemoryAllocator::GetUsedBytes() const {
  return GetBufferSize() - (tail_ - temp_);
}

size_t SimpleMemoryAllocator::GetBufferSize() const {
  return buffer_tail_ - buffer_head_;
}

uint8_t* SimpleMemoryAllocator::head() const { return head_; }

uint8_t* SimpleMemoryAllocator::tail() const { return tail_; }

}  // namespace tflite
