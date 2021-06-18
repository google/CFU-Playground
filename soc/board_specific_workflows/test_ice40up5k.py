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

import ice40up5k
import unittest
import workflow_args
from litex.soc.integration import builder
from unittest import mock


class Ice40UP5KWorkflowTest(unittest.TestCase):
    """TestCase for the Ice40UP5KWorkflow."""
    def setUp(self):
        self.args = workflow_args.parse_workflow_args(
            ['--cpu_variant', 'not fomu + cfu...'])
        self.soc_constructor = mock.MagicMock()

    def simple_init(self, warn: bool = False):
        return ice40up5k.Ice40UP5KWorkflow(self.args,
                                           self.soc_constructor,
                                           mock.create_autospec(
                                               builder.Builder),
                                           warn=warn)

    @mock.patch('warnings.warn')
    def test_warning(self, mock_warner):
        """Asserts the user is warned when cpu_variant switched."""
        self.simple_init(warn=True)

        # Let's not worry about the warning text, but make sure it exists.
        mock_warner.assert_called_once()

    def test_make_soc(self):
        """Tests to make sure the bios_flash_offset is passed through."""
        workflow = self.simple_init()
        workflow.make_soc()
        kwargs = self.soc_constructor.call_args.kwargs

        self.assertIn('bios_flash_offset', kwargs)
        self.assertEqual(kwargs['bios_flash_offset'],
                         workflow.bios_flash_offset)

    def test_software_load(self):
        """Asserts boards must implement their own software logic."""
        with self.assertRaises(NotImplementedError):
            self.simple_init().software_load('test_filename')


if __name__ == '__main__':
    unittest.main()
