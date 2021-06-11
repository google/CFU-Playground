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
import unittest.mock


class FakeDigilentArtySoCWorkflow(digilent_arty.DigilentArtySoCWorkflow):
    """Subclass of DigilentArtySoCWorkflow that makes __init__ a no-op."""
    def __init__(self):
        pass


class DigilentArtySoCWorkflow(unittest.TestCase):
    """TestCase for the DigilentArtySoCWorkflow."""
    @unittest.mock.patch('general.GeneralSoCWorkflow.make_soc')
    def test_make_soc(self, mock_make_soc):
        """Tests the make_soc method of DigilentArtySoCWorkflow."""
        FakeDigilentArtySoCWorkflow().make_soc()
        kwargs = mock_make_soc.call_args.kwargs
        mock_make_soc.assert_called_once()
        self.assertIn('l2_size', kwargs)
        self.assertTrue(kwargs['l2_size'], 8 * 1024)


if __name__ == '__main__':
    unittest.main()
