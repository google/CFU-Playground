#!/usr/bin/env bash
# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR=${SCRIPT_DIR}/../../../../..
cd "${ROOT_DIR}"
pwd

source tensorflow/lite/micro/tools/ci_build/helper_functions.sh

readable_run make -f tensorflow/lite/micro/tools/make/Makefile clean

# TODO(b/143904317): downloading first to allow for parallel builds.
readable_run make -f tensorflow/lite/micro/tools/make/Makefile third_party_downloads

# optional command line parameter "INTERNAL" uses internal test code
if [[ ${1} == "INTERNAL" ]]; then
  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4_internal \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    build -j$(nproc)

  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4_internal \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    test -j$(nproc)

  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4_internal \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    test_integration_tests_seanet_conv -j$(nproc)

  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4_internal \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    test_integration_tests_seanet_add_test -j$(nproc)

  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4_internal \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    test_integration_tests_seanet_leaky_relu_test -j$(nproc)
else
  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4 \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    build -j$(nproc)

  readable_run make -f tensorflow/lite/micro/tools/make/Makefile \
    TARGET=xtensa \
    TARGET_ARCH=hifi4 \
    OPTIMIZED_KERNEL_DIR=xtensa \
    XTENSA_CORE=HIFI_190304_swupgrade \
    test -j$(nproc)
fi