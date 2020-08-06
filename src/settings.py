import simplejson as json

settings_file = json.loads(open("config.json", 'r').read())

def get(setting):
	return settings_file.get(setting)
