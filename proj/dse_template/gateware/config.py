#!/bin/env python
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Depth of an EBRAM in 32 bit words
EBRAM_DEPTH_WORDS = 512

# Output channel parameters
OUTPUT_CHANNEL_PARAM_DEPTH = EBRAM_DEPTH_WORDS

# Output FIFO depth
OUTPUT_QUEUE_DEPTH = EBRAM_DEPTH_WORDS

# This is the depth of each EBRAM that makes up the filter data memory
FILTER_DATA_MEM_DEPTH = EBRAM_DEPTH_WORDS
FILTER_DATA_TOTAL_WORDS = FILTER_DATA_MEM_DEPTH * 4

# Input store consists of 4 EBRAMS, divided into 2 groups of 2
MAX_PER_PIXEL_INPUT_WORDS = EBRAM_DEPTH_WORDS * 2