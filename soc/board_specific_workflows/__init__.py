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

from digilent_arty import DigilentArtySoCWorkflow
from general import GeneralSoCWorkflow
from icebreaker import IcebreakerSoCWorkflow
from workflow_args import parse_workflow_args


def workflow_factory(target: str) -> GeneralSoCWorkflow:
    """Factory function to map a target to a SoC workflow.
    
    Args:
        target: A string representing the target board.
    
    Returns:
        The SoC workflow for the specific board. Will return the general
        workflow if there is no known specific workflow.
    """
    return {
        'digilent_arty': DigilentArtySoCWorkflow,
        '1bitsquared_icebreaker': IcebreakerSoCWorkflow,
    }.get(target, GeneralSoCWorkflow)


__all__ = [
    'DigilentArtySoCWorkflow',
    'GeneralSoCWorkflow',
    'IcebreakerSoCWorkflow',
    'parse_workflow_args'
    'workflow_factory',
]
