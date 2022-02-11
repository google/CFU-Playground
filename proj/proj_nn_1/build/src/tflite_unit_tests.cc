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

#include "tflite_unit_tests.h"

#include <cstdio>

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
