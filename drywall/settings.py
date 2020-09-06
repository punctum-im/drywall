# coding: utf-8
"""Contains functions for loading and saving settings"""

import simplejson as json

settings_file = json.loads(open("config.json", 'r').read())

def get(setting):
	return settings_file.get(setting)
