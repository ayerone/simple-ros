# Minimal Sphinx config for browsing a local subset of the ROS 2 docs
# (upstream: https://github.com/ros2/ros2_documentation, lyrical branch).

import os
from docutils.parsers.rst import Directive

project = 'simple-ros'
author = 'Open Robotics'
copyright = '2026, Open Robotics'

master_doc = 'index'
default_role = 'any'
exclude_patterns = ['**/_*.rst', '.venv/**']

extensions = [
    'sphinx_rtd_theme',
    'sphinx_tabs.tabs',
    'sphinx_copybutton',
]

html_theme = 'sphinx_rtd_theme'
html_static_path = ['source/_static']
html_css_files = ['simple-ros.css']


# Upstream pages use ".. redirect-from::" to record old URLs for their
# redirect plugin. That plugin isn't installed here, so register a no-op
# directive with the same name/arguments so the pages still parse.
class RedirectFrom(Directive):
    has_content = True
    optional_arguments = 0

    def run(self):
        return []


def setup(app):
    app.add_directive('redirect-from', RedirectFrom)
