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

import digilent_arty
import unittest
import workflow_args
from litex.build import generic_platform
from litex.soc.integration import builder
from litex.soc.integration import soc as litex_soc
from litex.build.xilinx import vivado
from unittest import mock


class DigilentArtySoCWorkflowTest(unittest.TestCase):
    """TestCase for the DigilentArtySoCWorkflow."""
    def setUp(self):
        self.args = workflow_args.parse_workflow_args([])
        self.soc = mock.create_autospec(litex_soc.LiteXSoC)
        self.soc.platform = mock.create_autospec(
            generic_platform.GenericPlatform)
        self.soc.platform.toolchain = mock.create_autospec(
            vivado.XilinxVivadoToolchain)
        self.soc_constructor = mock.MagicMock()
        self.builder_constructor = mock.create_autospec(builder.Builder)
        self.builder = mock.create_autospec(builder.Builder, instance=True)
        self.builder_constructor.return_value = self.builder


    def simple_init(self):
        """Returns a DigilentArtySoCWorkflow with testing parameters."""
        return digilent_arty.DigilentArtySoCWorkflow(self.args,
                                                     self.soc_constructor,
                                                     self.builder_constructor)

    def test_make_soc(self):
        """Tests the make_soc method of DigilentArtySoCWorkflow."""
        workflow = self.simple_init()
        workflow.make_soc()
        kwargs = self.soc_constructor.call_args.kwargs

        self.assertEqual(kwargs['l2_size'], workflow.args.l2_size)
        self.assertFalse(kwargs['with_jtagbone'], False)
        self.assertEqual(kwargs['variant'], workflow.args.variant)

    @mock.patch('litex.build.xilinx.vivado.vivado_build_argdict')
    def test_build_soc_vivado(self, mock_vivado_build_argdict):
        """Tests that vivado_build_argdict is called when using Vivado."""
        argdict_return = {'ijkl': 'mnop'}
        mock_vivado_build_argdict.return_value = argdict_return
        workflow = self.simple_init()
        workflow.build_soc(self.soc)

        mock_vivado_build_argdict.assert_called_once_with(workflow.args)
        build_kwargs = self.builder.build.call_args.kwargs
        self.assertEqual(argdict_return['ijkl'], build_kwargs['ijkl'])


if __name__ == '__main__':
    unittest.main()
