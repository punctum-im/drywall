# encoding: utf-8
"""Handles interactions with the settings file."""
import simplejson as json
settings = json.loads(open("config.json", 'r').read())

def get(setting):
	"""Get a setting's value by name. Returns the content of the setting."""
	return settings.get(setting)
