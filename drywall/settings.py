# encoding: utf-8
"""
Handles interactions with the settings file.

This is the settings module for handling the config.json file;
if you're looking for code for the settings web-page, it's in
the web module.
"""
import simplejson as json
settings = json.loads(open("config.json", 'r').read())

def get(setting):
	"""Get a setting's value by name. Returns the content of the setting."""
	return settings.get(setting)
