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

import general
import unittest
import workflow_args
from unittest import mock
from litex.build import generic_platform, generic_programmer
from litex.soc.integration import builder
from litex.soc.integration import soc as litex_soc


class GeneralSoCWorkflowTest(unittest.TestCase):
    """TestCase for the GeneralSoCWorkflow class.
    
    All methods except 'run' are tested here.
    """
    def setUp(self):
        """Sets up mocks and fakes used throughout the tests."""
        # Generates a real argparse Namespace for testing.
        self.target = 'test_target'
        self.build = True
        self.args = workflow_args.parse_workflow_args(
            ['--target', self.target, '--build' if self.build else ''])

        # Autospec the SoC.
        self.programmer = mock.create_autospec(
            generic_programmer.GenericProgrammer)
        self.soc = mock.create_autospec(litex_soc.LiteXSoC, instance=True)
        self.soc.platform = mock.create_autospec(
            generic_platform.GenericPlatform, instance=True)
        self.soc.platform.create_programmer.return_value = self.programmer
        self.build_name = 'test_build_name'
        self.soc.build_name = self.build_name

        # Autospec the Builder.
        self.builder = mock.create_autospec(builder.Builder, instance=True)
        self.gateware_dir = 'test_gateware_dir/'
        self.builder.gateware_dir = self.gateware_dir

        self.builder_constructor = mock.create_autospec(
            builder.Builder, return_value=self.builder)
        # Can't easily autospec the soc_constructor -- interface inconsistent.
        self.soc_constructor = mock.MagicMock(return_value=self.soc)

    def simple_init(self):
        """Returns a GeneralSoCWorkflow with reasonable testing parameters."""
        return general.GeneralSoCWorkflow(self.args, self.soc_constructor,
                                          self.builder_constructor)

    @mock.patch('litex.soc.integration.soc_core.soc_core_argdict')
    def test_make_soc(self, mock_soc_core_argdict):
        """Tests functionality of the make_soc method."""
        in_kwargs = {'abcd': 'efgh'}
        argdict_return = {'ijkl': 'mnop'}
        mock_soc_core_argdict.return_value = argdict_return
        soc = self.simple_init().make_soc(**in_kwargs)
        soc_kwargs = self.soc_constructor.call_args.kwargs

        # Check the kwargs of the constructor.
        self.soc_constructor.assert_called_once()
        self.assertEqual(soc, self.soc)
        self.assertNotIn('toolchain', soc_kwargs)
        self.assertEqual(in_kwargs['abcd'], soc_kwargs['abcd'])
        self.assertEqual(self.args.with_ethernet, soc_kwargs['with_ethernet'])
        self.assertEqual(self.args.with_etherbone,
                         soc_kwargs['with_etherbone'])
        self.assertEqual(self.args.with_mapped_flash,
                         soc_kwargs['with_mapped_flash'])
        self.assertEqual(self.args.with_spi_sdcard,
                         soc_kwargs['with_spi_sdcard'])
        self.assertEqual(self.args.with_video_framebuffer,
                         soc_kwargs['with_video_framebuffer'])

        # Check the return value of soc_core_argdict is used.
        mock_soc_core_argdict.assert_called_once()
        self.assertEqual(argdict_return['ijkl'], argdict_return['ijkl'])

    @mock.patch('litex.soc.integration.builder.builder_argdict')
    def test_build_soc(self, mock_builder_argdict):
        """Tests functionality of the build_soc method."""
        in_kwargs = {'abcd': 'efgh'}
        argdict_return = {'output_dir': 'abcd'}
        mock_builder_argdict.return_value = argdict_return
        soc_builder = self.simple_init().build_soc(self.soc, **in_kwargs)
        build_kwargs = soc_builder.build.call_args.kwargs

        # Check the args / kwargs of the .build(...) call.
        self.builder_constructor.assert_called_once()
        soc_builder.build.assert_called_once()
        self.assertEqual(soc_builder, self.builder)
        self.assertEqual(in_kwargs['abcd'], build_kwargs['abcd'])

        # Check the args / kwargs of the constructor.
        constructor_args = self.builder_constructor.call_args.args
        constructor_kwargs = self.builder_constructor.call_args.kwargs
        mock_builder_argdict.assert_called_once()
        self.assertIn(self.soc, constructor_args)

        # Check the return value of builder_argdict is used.
        self.assertEqual(argdict_return['output_dir'],
                         constructor_kwargs['output_dir'])

    def test_load(self):
        """Tests functionality of the load method."""
        self.simple_init().load(self.soc, self.builder)

        self.soc.platform.create_programmer.assert_called_once()
        self.programmer.load_bitstream.assert_called_once_with(
            f'{self.gateware_dir}{self.build_name}.bit')


class FakeGeneralSoCWorkflow(general.GeneralSoCWorkflow):
    """Subclasses GeneralSoCWorkflow to have all methods record call order.
    
    This is used to make sure the `run` method is working as intended.
    """
    def __init__(self, load):
        self.call_order = []
        self.args = unittest.mock.MagicMock()
        self.args.load = load

    def make_soc(self):
        self.call_order.append('make_soc')
        return unittest.mock.MagicMock()

    def build_soc(self, soc):
        self.call_order.append('build_soc')
        return unittest.mock.MagicMock()

    def load(self, soc, builder):
        self.call_order.append('load')


class GeneralSoCWorkflowRunTest(unittest.TestCase):
    """TestCase for the `run` method of GeneralSoCWorkflow."""
    def test_run_load_false(self):
        workflow = FakeGeneralSoCWorkflow(load=False)
        workflow.run()
        self.assertListEqual(workflow.call_order, ['make_soc', 'build_soc'])

    def test_run_load_true(self):
        workflow = FakeGeneralSoCWorkflow(load=True)
        workflow.run()
        self.assertListEqual(workflow.call_order,
                             ['make_soc', 'build_soc', 'load'])


if __name__ == '__main__':
    unittest.main()
