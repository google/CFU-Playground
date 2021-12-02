#!/usr/bin/env bash
# Copyright 2021 The CFU-Playground Authors
# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Inspiried by https://github.com/tensorflow/tflite-micro-arduino-examples/blob/main/scripts/sync_from_tflite_micro.sh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -ex

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFU_ROOT="$(dirname $(dirname $(realpath ${BASH_SOURCE[0]})))"
cd "${ROOT_DIR}"

TEMP_DIR=$(mktemp -d)
cd "${TEMP_DIR}"

echo Cloning tflite-micro repo to "${TEMP_DIR}"
git clone --depth 1 --single-branch "https://github.com/tensorflow/tflite-micro.git"
cd tflite-micro
git rev-parse --short HEAD >| ${CFU_ROOT}/conf/tflite-micro.version

make -f tensorflow/lite/micro/tools/make/Makefile clean_downloads

OUTPUT_DIR="${TEMP_DIR}/tflm_tree"

# Create the TFLM base tree, get person_detection for its models
python3 tensorflow/lite/micro/tools/project_generation/create_tflm_tree.py "${OUTPUT_DIR}"

# Download person_model_int8 third party. URL taken from tflite-micro:
# https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/tools/make/third_party_downloads.inc
PERSON_MODEL_INT8_ZIP="tf_lite_micro_person_data_int8_grayscale_2020_12_1.zip"
PERSON_MODEL_INT8_URL="https://storage.googleapis.com/download.tensorflow.org/data/${PERSON_MODEL_INT8_ZIP}"
PERSON_MODEL_INT8_MD5="e765cc76889db8640cfe876a37e4ec00"

# source bash_helpers fot `check_md5`
source tensorflow/lite/micro/tools/make/bash_helpers.sh
wget ${PERSON_MODEL_INT8_URL} -O ${PERSON_MODEL_INT8_ZIP}
check_md5 ${PERSON_MODEL_INT8_ZIP} ${PERSON_MODEL_INT8_MD5}
mkdir person_model_int8
unzip -a ${PERSON_MODEL_INT8_ZIP}

# Generate keyword benchmark models
make -f tensorflow/lite/micro/tools/make/Makefile run_keyword_benchmark

# Copy files used by CFU Playground that are not present in TFLM base tree
cp -r tensorflow/lite/micro/examples ${OUTPUT_DIR}/tensorflow/lite/micro/
cp tensorflow/lite/micro/kernels/conv_test* ${OUTPUT_DIR}/tensorflow/lite/micro/kernels
cp tensorflow/lite/micro/kernels/depthwise_conv_test* ${OUTPUT_DIR}/tensorflow/lite/micro/kernels
cp -r tensorflow/lite/micro/kernels/testdata ${OUTPUT_DIR}/tensorflow/lite/micro/kernels/
cp -r tensorflow/lite/micro/models ${OUTPUT_DIR}/tensorflow/lite/micro/
cp -r tensorflow/lite/micro/tools ${OUTPUT_DIR}/tensorflow/lite/micro/
cp -r person_model_int8/* ${OUTPUT_DIR}/tensorflow/lite/micro/examples/person_detection/

# copy ${OUTPUT_DIR} to the repo
cp -aT "${OUTPUT_DIR}" "${CFU_ROOT}/third_party/tflite-micro"

rm -rf "${TEMP_DIR}"
