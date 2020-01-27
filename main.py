#!/usr/bin/env python3
import os
import sys

# configure import paths
root_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, os.path.abspath(root_dir))

# start the command line (allowing EXAM-prefixed env vars)
from cli import cli

cli(auto_envvar_prefix='EXAM')
