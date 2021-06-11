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
import unittest.mock


class TestGeneralSoCWorkflow(unittest.TestCase):
    """TestCase for the GeneralSoCWorkflow class.
    
    All methods except `run` are tested in this test case.  
    """
    def setUp(self):
        """Sets up various mocks used throughout the tests."""

        # Mocks the argparse arguments
        self.mock_namespace = unittest.mock.MagicMock()
        self.target_value = 'test_target'
        self.target_keyword = 'target'
        self.build_keyword = 'build'
        self.build_value = True
        self.call_kwargs = {
            self.target_keyword: self.target_value,
            self.build_keyword: self.build_value,
        }
        self.mock_namespace.configure_mock(**self.call_kwargs)

        # Mocks the generated LiteXSoC
        self.mock_soc = unittest.mock.MagicMock()
        self.build_name = 'build_name'
        self.mock_soc.configure_mock(build_name=self.build_name)

        # Mocks the imported LiteX-Boards module
        self.mock_module = unittest.mock.MagicMock()
        self.mock_module.BaseSoC = unittest.mock.MagicMock(
            return_value=self.mock_soc)

        # Mocks the LiteX Builder
        self.mock_builder = unittest.mock.MagicMock()
        self.gateware_dir = 'test_gateware_dir/'
        self.mock_builder.configure_mock(gateware_dir=self.gateware_dir)
        self.mock_builder.build = unittest.mock.MagicMock()

        # Overwrite the format_bistream_filename method to avoid os.
        self.format_bitsream_filename = general.GeneralSoCWorkflow.format_bitstream_filename
        self.test_format_func = lambda cls, x, y: f'{x}, {y}'
        general.GeneralSoCWorkflow.format_bitstream_filename = self.test_format_func

    def tearDown(self):
        """Fixes the overwritten format_bitstream_filename method."""
        general.GeneralSoCWorkflow.format_bitstream_filename = self.format_bitsream_filename

    @unittest.mock.patch('importlib.import_module')
    def patched_init(self, mock_import_module):
        """Calls the constructor with a redefined importlib.import_module."""
        mock_import_module.return_value = self.mock_module
        self.mock_import_module = mock_import_module
        return general.GeneralSoCWorkflow(self.mock_namespace)

    def test_init(self):
        """Tests constructor args and import."""
        workflow = self.patched_init()

        self.mock_import_module.assert_called_once_with(
            general.GeneralSoCWorkflow.format_import_path(self.target_value))
        self.assertEqual(workflow.args, self.mock_namespace)
        self.assertEqual(workflow.module, self.mock_module)

    @unittest.mock.patch('litex.soc.integration.soc_core.soc_core_argdict')
    def patched_make_soc(self, mock_soc_core_argdict, **kwargs):
        """Calls make_soc with a redefined soc_core_argdict."""
        workflow = self.patched_init()
        self.mock_soc_core_argdict = mock_soc_core_argdict
        return workflow, workflow.make_soc(**kwargs)

    def test_make_soc(self):
        """Tests the general make_soc function without kwargs."""
        _, soc = self.patched_make_soc()

        self.mock_soc_core_argdict.assert_called_once_with(self.mock_namespace)
        self.assertEqual(soc, self.mock_soc)
        self.mock_module.BaseSoC.assert_called_once()

    def test_make_soc_kwargs(self):
        """Tests to see if kwargs are passed through in make_soc."""
        self.patched_make_soc(**self.call_kwargs)
        kwargs = self.mock_module.BaseSoC.call_args.kwargs

        self.assertIn(self.target_keyword, kwargs)
        self.assertTrue(kwargs[self.target_keyword] == self.target_value)

    @unittest.mock.patch('litex.soc.integration.builder.Builder')
    @unittest.mock.patch('litex.soc.integration.builder.builder_argdict')
    @unittest.mock.patch('litex.build.xilinx.vivado.vivado_build_argdict')
    def patched_build_soc(self,
                          mock_vivado_build_argdict,
                          mock_builder_argdict,
                          mock_builder_class,
                          is_vivado=False,
                          **kwargs):
        """Calls build_soc with redefined imports."""
        workflow, soc = self.patched_make_soc()
        mock_builder_argdict.return_value = self.call_kwargs
        mock_builder_class.return_value = self.mock_builder
        soc.platform = unittest.mock.MagicMock()
        if is_vivado:
            soc.platform.toolchain = unittest.mock.MagicMock(
                spec=general._VIVADO_TOOLCHAIN_TYPE)
            mock_vivado_build_argdict.return_value = self.call_kwargs

        self.mock_builder_class = mock_builder_class
        self.mock_builder_argdict = mock_builder_argdict
        self.mock_vivado_build_argdict = mock_vivado_build_argdict

        return workflow, workflow.build_soc(soc, **kwargs)

    def test_build_soc(self):
        """Tests general logic of build_soc (when is_vivado is False)."""
        _, builder = self.patched_build_soc(is_vivado=False)
        kwargs = self.mock_builder.build.call_args.kwargs

        self.assertEqual(builder, self.mock_builder)
        self.mock_builder_argdict.assert_called_once_with(self.mock_namespace)
        self.mock_builder_class.assert_called_once_with(
            self.mock_soc, **self.call_kwargs)
        self.assertEqual(kwargs['run'], self.build_value)
        self.mock_vivado_build_argdict.assert_not_called()

    def test_build_soc_vivado(self):
        """Tests build_soc when is_vivado is True."""
        _, builder = self.patched_build_soc(is_vivado=True)
        kwargs = self.mock_builder.build.call_args.kwargs

        self.assertEqual(builder, self.mock_builder)
        self.mock_builder_argdict.assert_called_once_with(self.mock_namespace)
        self.mock_builder_class.assert_called_once_with(
            self.mock_soc, **self.call_kwargs)
        self.assertEqual(kwargs['run'], self.build_value)
        self.mock_vivado_build_argdict.assert_called_once_with(
            self.mock_namespace)

    def test_build_soc_kwargs(self):
        """Tests to see if kwargs are passed through in build_soc."""
        extra_kwarg = {'a': 'a'}
        self.patched_build_soc(is_vivado=False, **extra_kwarg)
        kwargs = self.mock_builder_class.call_args.kwargs

        self.assertIn('a', kwargs)

    def test_load(self):
        """Tests load with a redefined format bitstream."""
        workflow, _ = self.patched_build_soc()
        programmer = unittest.mock.MagicMock()
        self.mock_soc.platform.create_programmer.return_value = programmer
        workflow.load(self.mock_soc, self.mock_builder)

        self.mock_soc.platform.create_programmer.assert_called_once()
        programmer.load_bitstream.assert_called_once_with(
            self.test_format_func(None, self.gateware_dir, self.build_name))


class FakeGeneralSockWorkflow(general.GeneralSoCWorkflow):
    """Subclasses GeneralSoCWorkflow to have all methods record call order."""
    def __init__(self, load=False):
        self.call_order = []
        self.args = unittest.mock.MagicMock()
        self.args.configure_mock(load=load)

    def make_soc(self):
        self.call_order.append('make_soc')
        return unittest.mock.MagicMock()

    def build_soc(self, soc):
        self.call_order.append('build_soc')
        return unittest.mock.MagicMock()

    def load(self, soc, builder):
        self.call_order.append('load')


class TestGeneralSoCWorkflowRun(unittest.TestCase):
    """TestCase for the `run` method of GeneralSoCWorkflow."""
    def test_run_load_false(self):
        workflow = FakeGeneralSockWorkflow(load=False)
        workflow.run()
        self.assertListEqual(workflow.call_order, ['make_soc', 'build_soc'])

    def test_run_load_true(self):
        workflow = FakeGeneralSockWorkflow(load=True)
        workflow.run()
        self.assertListEqual(workflow.call_order,
                             ['make_soc', 'build_soc', 'load'])


if __name__ == '__main__':
    unittest.main()
