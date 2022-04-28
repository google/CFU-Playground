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

#include "util_tests.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

#include "menu.h"
#include "murmurhash.h"

namespace {
struct MurmurTestCase {
  uint32_t expected;
  uint8_t data[20];
  int len;
  bool check() const;
};

bool MurmurTestCase::check() const {
  uint32_t hash = murmurhash3_32(data, len);
  bool ok = hash == expected;
  printf("murmurhash3_32(data, %d) expected %08lx, got %08lx %s\n", len,
         expected, hash, ok ? "OK" : "FAIL");
  return ok;
}

void do_murmur_tests(void) {
  // Cases generated from a colab notebook:
  // https://colab.research.google.com/drive/1P2TEGItZUumPTaQkHYDP5MMd8_hxnSNm?usp=sharing
  MurmurTestCase cases[] = {
      {0x00000000, {}, 0},
      {0x63c05906, {0x44}, 1},
      {0x68880912, {0x20, 0x82}, 2},
      {0x84077cd7, {0x3c, 0xfd, 0xe6}, 3},
      {0x5ee237f9, {0xf1, 0xc2, 0x6b, 0x30}, 4},
      {0x7bccc201, {0xf9, 0x0e, 0xc7, 0xdd, 0x01}, 5},
      {0xe9c33985, {0xe4, 0x88, 0x75, 0x34, 0xa2, 0x0f}, 6},
      {0xd03bf07f, {0x0b, 0x0d, 0x04, 0xc3, 0x6e, 0xd8, 0x0e}, 7},
      {0x921bb379, {0x71, 0xe0, 0xfd, 0x77, 0xb0, 0x76, 0x70, 0xeb}, 8},
      {0x77f840fd, {0x94, 0x0b, 0xd5, 0x33, 0x5f, 0x97, 0x3d, 0xaa, 0xd8}, 9},
      {0xbf193078,
       {0x61, 0x9b, 0x91, 0xff, 0xc9, 0x11, 0xf5, 0x7c, 0xce, 0xd4},
       10},
      {0x83199728,
       {0x58, 0xbb, 0xbf, 0x2c, 0xe0, 0x37, 0x53, 0xc9, 0xbd, 0xfa, 0x0f},
       11},
      {0x9be731ac,
       {0xf0, 0x16, 0x9d, 0xc9, 0x57, 0x56, 0x74, 0x06, 0x66, 0x76, 0xcf, 0xb0},
       12},
      {0xd6bf5284,
       {0xb4, 0xeb, 0x89, 0x02, 0xc4, 0x42, 0x69, 0xda, 0x1c, 0xf6, 0xba, 0x66,
        0xd3},
       13},
      {0xf38ae6b6,
       {0xf8, 0xb6, 0xd4, 0xb1, 0x00, 0xa9, 0xea, 0x0e, 0x75, 0x5a, 0x5c, 0x2e,
        0x82, 0x10},
       14},
      {0xfe3882d0,
       {0x24, 0x2a, 0x08, 0xe7, 0x07, 0x8f, 0x7f, 0x89, 0x38, 0x5e, 0xb0, 0x94,
        0x23, 0x55, 0x51},
       15},
      {0xedd89b4f,
       {0x82, 0x56, 0x8b, 0x96, 0xe8, 0xa4, 0xfe, 0xf2, 0x3a, 0x0c, 0x9f, 0xc5,
        0xaf, 0xd7, 0x60, 0x84},
       16},
      {0xe3431423,
       {0x37, 0x81, 0x6b, 0xdd, 0x0a, 0x73, 0x09, 0xcb, 0x4a, 0x12, 0x52, 0xe4,
        0xda, 0x70, 0xe6, 0x72, 0x0f},
       17},
      {0xa2d24eec,
       {0xca, 0xa4, 0xda, 0x1e, 0x98, 0x40, 0x6c, 0x18, 0x9c, 0x24, 0x27, 0x9e,
        0x98, 0x51, 0xd5, 0x81, 0x42, 0x04},
       18},
      {0xf829d142,
       {0x13, 0x6f, 0xeb, 0x57, 0x13, 0xc1, 0x66, 0xb1, 0x32, 0x69, 0xdd, 0x63,
        0xfc, 0x35, 0xc7, 0x97, 0xff, 0x08, 0xa6},
       19},
      {0, {}, -1},
  };
  int passed = 0;
  int count = 0;
  for (; cases[count].len != -1; count++) {
    printf("%2d: ", count);
    if (cases[count].check()) {
      passed++;
    }
  }
  printf("%d out of %d passed\n", passed, count);
}


void print_float(const char *name, float x)
{
  char m = ' ';
  if (x < 0.0f) {
      m = '-';
      x = -x;
  }
  int i_i = (int)x;
  float r = x - (float)(i_i);
  printf("%s: %c%d.%03d\n", name, m, i_i, (int)(r * 1000.0f));
}

void do_fpu(void) {
  for (int j = 0; j < 10; j++) {
      float a = ((float)j) + 0.51f;
      float b = 4.91f;
      //printf("%f + %f = %f\n", (double)a, (double)b, (double)(a+b));
      print_float("a  ", a);
      print_float("b  ", b);
      print_float("a+b", a+b);
      print_float("a*b", a*b);
      print_float("a-b", a-b);
      print_float("a/b", a/b);
      printf("\n");
  }
}


struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('1', "murmurhash tests", do_murmur_tests),
        MENU_ITEM('f', "FPU tests", do_fpu),
        MENU_END,
    },
};

}  // end anonymous namespace

// Menu-based tests for playground_util classes
void do_util_tests_menu(void) { menu_run(&MENU); }
