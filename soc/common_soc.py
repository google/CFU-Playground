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
import importlib
from board_specific_workflows import workflow_factory, parse_workflow_args
from litex.soc.integration import soc
from typing import Callable


def get_soc_constructor(target: str) -> Callable[..., soc.LiteXSoC]:
    """Returns the constructor for the target SoC from litex-boards module."""
    try:
        module = importlib.import_module(f'litex_boards.targets.{target}')
    except:
        raise ModuleNotFoundError(f'Could not load {target} target.')
    return module.BaseSoC


def main():
    parser = argparse.ArgumentParser(
        'Determine purpose (load software or hardware).')
    parser.add_argument('--software-load',
                        action='store_true',
                        help='Perform pre-lxterm loading procedures.')
    parser.add_argument('--software-path', help='Path to software to load')
    purpose, _ = parser.parse_known_args()

    args = parse_workflow_args()
    assert not (args.with_ethernet and args.with_etherbone)
    workflow = workflow_factory(args.target)(args,
                                             get_soc_constructor(args.target))

    # Determine if call to code was for loading software or hardware/bios.
    if purpose.software_load == True:
        workflow.software_load(purpose.software_path)
    else:
        workflow.run()


if __name__ == "__main__":
    main()
