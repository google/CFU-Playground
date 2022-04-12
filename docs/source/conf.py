#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020  The SymbiFlow Authors.
# Copyright (C) 2021  The CFU-Playground Authors.
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
#
# SPDX-License-Identifier: Apache-2.0

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from recommonmark.parser import CommonMarkParser

# -- Project information -----------------------------------------------------

project = u'CFU-Playground'
authors = u'The CFU-Playground Authors'
copyright = authors + u', 2020'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_tabs.tabs',
    'sphinxcontrib.jinja',
    'recommonmark',
    'sphinxcontrib.wavedrom',
]

source_parsers = {
    '.md': CommonMarkParser,
}

source_suffix = ['.rst', '.md']


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_show_sourcelink = True
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

html_theme = 'sphinx_material'
html_theme_options = {
    'nav_title': project,
    'color_primary': 'deep-orange',
    'color_accent': 'gray',
    'repo_name': "google/CFU-Playground",
    'repo_url': 'https://github.com/google/CFU-Playground',
    'globaltoc_depth': 5,
    'globaltoc_collapse': True
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# CFU-Playground specific customisations
html_css_files = ['stylesheets/cfu-playground.css']


# -- Collect READMEs from examples --------------------------------------------
#
#from collect_readmes import full_name_lut, families, fill_context
#
#jinja_contexts = {}
#top_dir = os.path.join(os.path.dirname(__file__), '..')
#for family in families:
#    examples = os.scandir(os.path.join(top_dir, family))
#    for example in examples:
#        if example.is_dir():
#
#            # get README
#            path = os.path.join(top_dir, family, example, 'README.rst')
#
#            # skip if file does not exist
#            if not os.path.isfile(path):
#                continue
#
#            with open(path) as f:
#                text = f.read()
#
#            key = '_'.join((family, example.name))
#            jinja_contexts[key] = {'blocks': fill_context(text)}
