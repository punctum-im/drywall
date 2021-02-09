# encoding: utf-8
"""
Handles interactions with the config.json file.
"""
import simplejson as json
config_file = json.loads(open("config.json", 'r').read())

def get(setting):
	"""Get a setting's value by name. Returns the content of the setting."""
	return config_file.get(setting)
