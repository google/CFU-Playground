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

import argparse
from litex.build.xilinx.vivado import vivado_build_args
from litex.soc.integration.builder import builder_args
from litex.soc.integration.soc_core import soc_core_args
from typing import List


def parse_workflow_args(input: List[str] = None) -> argparse.Namespace:
    """Parses command-line style flags for the workflow.

    All unknown args are discarded to allow multiple parses on args. 

    Args:
        input: An optional list of strings in the style of sys.argv. Will
          default to argparse's interpretation of sys.argv if omitted.
    
    Returns:
        An argparse Namespace with the parsed, known arguments.
    """
    parser = argparse.ArgumentParser(description='LiteX SoC')
    parser.add_argument('--build', action='store_true', help='Build bitstream')
    parser.add_argument('--load', action='store_true', help='Load bitstream')
    parser.add_argument('--toolchain',
                        help=('Specify toolchain for implementing '
                              'gateware (\'vivado\' or \'symbiflow\')'))
    builder_args(parser)
    soc_core_args(parser)
    vivado_build_args(parser)
    parser.add_argument('--with-ethernet',
                        action='store_true',
                        help='Enable Ethernet support')
    parser.add_argument('--with-etherbone',
                        action='store_true',
                        help='Enable Etherbone support')
    parser.add_argument('--with-mapped-flash',
                        action='store_true',
                        help='Add litespi SPI flash')
    parser.add_argument('--target',
                        default='digilent_arty',
                        help='Specify target board')
    parser.set_defaults(csr_csv='csr.csv',
                        uart_name='serial',
                        uart_baudrate=921600,
                        cpu_variant='full+cfu+debug',
                        with_etherbone=False)
    # Return only the known args
    if input:
        return parser.parse_known_args(input)[0]
    else:
        return parser.parse_known_args()[0]
