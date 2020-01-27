#!/usr/bin/env python3

# start the command line (allowing EXAM-prefixed env vars)
from cli import cli

cli(auto_envvar_prefix='EXAM')
