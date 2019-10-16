#!/usr/bin/env python
# -*- coding: utf-8 -*
import yaml
import os

config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yml')))
