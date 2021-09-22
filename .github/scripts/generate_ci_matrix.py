#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json

json_list = []

def read_projects_to_test(workflows_path):
    with open(os.path.join(workflows_path, "projects_to_test.txt"), "r") as f:
        file_content = f.read()
        projects = file_content.splitlines()

        return projects


def read_supported_targets(workflows_path):
    with open(os.path.join(workflows_path, "supported_targets.txt"), "r") as f:
        file_content = f.read()
        targets = file_content.splitlines()

        return targets


def read_proj_excluded_targets(projects_path, proj_name):
    proj_path = os.path.join(projects_path, proj_name)
    try:
        with open(os.path.join(proj_path, "ci", "ci_exclude_targets.txt"), "r") as f:
            file_content = f.read()
            excluded_targets = file_content.splitlines()
    except IOError:
        excluded_targets = ""

    return excluded_targets


def read_proj_build_params(projects_path, proj_name, params_no):
    proj_path = os.path.join(projects_path, proj_name)
    filename = "ci_build_params.txt." + str(params_no)
    try:
        with open(os.path.join(proj_path, "ci", filename), "r") as f:
            file_content = f.read()
            build_params = file_content.replace("\n", " ")
    except IOError:
        build_params = ""

    return build_params


def get_proj_supported_targets(all_targets, excluded_targets):
    proj_targets = [x for x in all_targets if x not in excluded_targets]

    return proj_targets


def append_to_json_list(proj_name, proj_targets, build_params):
    for i in range(len(proj_targets)):
        if proj_targets[i] == "hps":
            platform = "hps"
        else:
            platform = "common_soc"

        matrix_entry = { 
            "proj_name": proj_name,
            "platform": platform,
            "target": proj_targets[i],
            "build_params": build_params
        }
        json_list.append(matrix_entry)

def list_to_json_str(final_list):
    json_str = json.dumps(final_list)

    return json_str


def main():
    workflows_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workflows"))
    projects_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "proj"))

    projects_to_test = read_projects_to_test(workflows_path)
    all_targets = read_supported_targets(workflows_path)

    for project in projects_to_test:
        excluded_targets = read_proj_excluded_targets(projects_path, project)
        proj_targets = get_proj_supported_targets(all_targets, excluded_targets)

        # Add default variant
        append_to_json_list(project, proj_targets, "")

        # Add custom variants
        for i in range(10):
            build_params = read_proj_build_params(projects_path, project, i)
            if build_params != "":
                append_to_json_list(project, proj_targets, build_params)

    json_str = list_to_json_str(json_list)
    print(json_str)


if __name__ == "__main__":
    main()
