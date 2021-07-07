#!/bin/bash
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Add menu items that correspond to the model menu item that causes the 
# model to be loaded.
MENU_ITEMS="1 1"
MODEL=pdti8

THIS_DIR=$(dirname "${BASH_SOURCE[0]}")
cd "${THIS_DIR}"
CFU_ROOT=$(realpath "${THIS_DIR}/../..")
SCRIPTS="${CFU_ROOT}/scripts"
TMP=$(mktemp /tmp/tailrom.XXXXXX)

# capture the output
make run TAIL_CAPTURE=1 RUN_MENU_ITEMS="${MENU_ITEMS} x x"| tee ${TMP}

# Make a .cc file
"${SCRIPTS}/pyrun" "${THIS_DIR}/extract_captured_data.py" \
    --model-name "${MODEL}" "${TMP}" "src/${MODEL}_cache.cc" "src/${MODEL}_cache.h"

rm "${TMP}"
