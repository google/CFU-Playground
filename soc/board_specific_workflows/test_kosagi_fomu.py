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

import io
import kosagi_fomu
import unittest
from litex.build import dfu
from litex.soc.integration import builder
from unittest import mock


class CreateImageTest(unittest.TestCase):
    """TestCase for the create_image function."""
    def test_simple_image(self):
        gateware = io.BytesIO(b'gateware')
        software = io.BytesIO(b'software')
        offset = 0x100
        output = kosagi_fomu.create_image(gateware, software, offset)
        self.assertEqual(output[:len(gateware.getvalue())],
                         gateware.getvalue())
        self.assertEqual(output[offset:offset + len(software.getvalue())],
                         software.getvalue())

    def test_max_gateware(self):
        gateware = io.BytesIO(b'gateware')
        software = io.BytesIO(b'software')
        offset = len(gateware.getvalue())
        output = kosagi_fomu.create_image(gateware, software, offset)
        self.assertEqual(output, gateware.getvalue() + software.getvalue())

    def test_gateware_too_big(self):
        with self.assertRaises(ValueError):
            gateware = io.BytesIO(b'gateware')
            software = io.BytesIO(b'software')
            offset = 0x1
            kosagi_fomu.create_image(gateware, software, offset)


class KosagiFomuSoCWorkflowWorkflowTest(unittest.TestCase):
    """TestCase for the KosagiFomuSoCWorkflow."""
    def setUp(self):
        self.soc_constructor = mock.MagicMock()

    def simple_init(self):
        return kosagi_fomu.KosagiFomuSoCWorkflow(mock.MagicMock(),
                                                 self.soc_constructor,
                                                 mock.create_autospec(
                                                     builder.Builder),
                                                 warn=False)

    def test_make_soc(self):
        self.simple_init().make_soc()

        call_kwargs = self.soc_constructor.call_args.kwargs
        self.assertNotEqual(call_kwargs['integrated_rom_init'], [])
        self.assertEqual(call_kwargs['spi_flash_module'], 'W25Q128JV')
        self.assertFalse(call_kwargs['with_ctrl'])
        self.assertFalse(call_kwargs['with_led_chaser'])
        self.assertFalse(call_kwargs['with_timer'])

    def test_software_load(self):
        workflow = self.simple_init()

        workflow.args.output_dir = 'test_dir'
        test_filename = 'test_filename'
        mock_image_builder = mock.create_autospec(
            kosagi_fomu.fomu_image_builder)
        mock_programmer = mock.create_autospec(dfu.DFUProg, instance=True)

        workflow.software_load(test_filename, mock_programmer,
                               mock_image_builder)

        call_kwargs = mock_image_builder.call_args.kwargs
        self.assertEqual(call_kwargs['gateware_filename'],
                         'test_dir/gateware/kosagi_fomu_pvt.bin')
        self.assertEqual(call_kwargs['software_filename'], 'test_filename')
        self.assertEqual(call_kwargs['offset'],
                         workflow.bios_flash_offset - 0x40000)

        mock_programmer.load_bitstream.assert_called_once_with(
            call_kwargs['image_filename'])


if __name__ == '__main__':
    unittest.main()
