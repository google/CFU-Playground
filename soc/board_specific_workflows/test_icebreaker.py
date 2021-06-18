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

import icebreaker
import unittest
from litex.build.lattice import programmer as lattice_programmer
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder
from unittest import mock


class IcebreakerSoCWorkflowTest(unittest.TestCase):
    """TestCase for the IcebreakerSoCWorkflow."""
    def setUp(self):
        self.soc = mock.create_autospec(litex_soc.LiteXSoC)
        self.builder = mock.create_autospec(builder.Builder)
        self.programmer = mock.create_autospec(
            lattice_programmer.IceStormProgrammer, instance=True)

    def simple_init(self):
        return icebreaker.IcebreakerSoCWorkflow(mock.MagicMock(),
                                                mock.MagicMock(),
                                                mock.create_autospec(
                                                    builder.Builder),
                                                warn=False)

    def test_load(self):
        """Asserts the load method flashes in the right order."""
        self.soc.build_name = 'test_build_name'
        self.builder.output_dir = 'test_output_dir/'
        workflow = self.simple_init()
        workflow.load(self.soc, self.builder, self.programmer)

        expected_calls = [
            mock.call(
                0,
                f'{self.builder.output_dir}/gateware/{self.soc.build_name}.bin'
            ),
            mock.call(workflow.bios_flash_offset,
                      f'{self.builder.output_dir}/software/bios/bios.bin')
        ]
        self.programmer.flash.assert_has_calls(expected_calls)

    def test_software_load(self):
        """Asserts the software is loaded over the bios."""
        workflow = self.simple_init()
        workflow.software_load('test_filename', self.programmer)

        self.programmer.flash.assert_called_once_with(
            workflow.bios_flash_offset, 'test_filename')


if __name__ == '__main__':
    unittest.main()
