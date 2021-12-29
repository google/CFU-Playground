#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
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

"""Interface to test data.

We store data in pickle files rather than referrring to it directly, as the
large .py files containing the raw data are slow and inconvenient to use in
IDEs.
"""

from collections import namedtuple
from pathlib import Path
import pickle

Conv2DData = namedtuple('Conv2DData', [
    'input_dims',
    'output_dims',
    'filter_dims',
    'input_offset',
    'output_offset',
    'output_min',
    'output_max',
    'stride',
    'output_multipliers',
    'output_shifts',
    'output_biases',
    'raw_input_data',        # as bytes
    'input_data',            # as words
    'filter_data',           # as words
    'expected_output_data',  # as words
])


def fetch_data(name):
    """Fetches data with the given name.

    Data is stored in a file namemed name.pickle in the current directory.
    """
    filename = Path(__file__).parent / (name + ".pickle")
    with open(filename, 'rb') as f:
        return pickle.load(f)


def save_data(name, data):
    """Saves data into a pickle file."""
    with open(Path(__file__).parent / (name + '.pickle'), 'wb') as f:
        pickle.dump(data, f)
