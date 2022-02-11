/*
 * Copyright 2021 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "tensorflow/lite/micro/testing/micro_test.h"

// Global variables normally defined in the TF_LITE_MICRO_TESTS_BEGIN macro.

namespace micro_test {
int tests_passed;
int tests_failed;
bool is_test_complete;
bool did_test_fail;
}  // namespace micro_test