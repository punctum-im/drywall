# coding: utf-8
"""
This is a fake database shim, intended for development purposes.
It uses dicts to store data in memory, and as such does not require
any extra libraries, dependencies or configuration. However, it has one
flaw - all data is kept in memory, so as soon as the server is shut
down **ALL DATA IS LOST**.

While we could technically solve this by simply dumping the contents
of the database dict to a file every once in a while, there are
database programs out there that are much more fit for the job.
Also, it's a security risk (saving stuff as plaintext is usually
not a good idea).

This shim can also be used as a template for adding new database
backends.
"""

db = {}

def manipulate_object(id=None, object=None):
	"""
	Usage:
	    manipulate_object(object)
	    # ...or...
	    manipulate_object(object, id)
	Takes an object and optionally an ID, then replaces the object in the database
	with the provided object. If the object does not exist, it will be created.
	Returns the ID of the object.

	If you want to add an object to the database, use the add_object function,
	as it checks if the ID is already present in the database and errors out
	if it is.

	If you want to replace an object with a certain ID with another object,
	use the push_object function, as it errors out when the ID does not exist.

	These two functions use this function (manipulate_objects) at their core,
	but implement the necesary checks for convenience.

	Arguments:
	    object - object that will be pushed
	    id (optional) - ID to manipulate; if not passed it will be taken from
	                    the object
	"""
	object_dict = {}

	for key, value in vars(object).items():
		object_dict[key] = value

	if not id:
		id = vars(object)['id']

	db[id] = object_dict

	return object_dict

def add_object(object):
	"""
	Takes an object and inserts it into the database. Returns the inserted object.

	Returns False if the ID is already taken.
	"""
	id = vars(object)['id']
	if id_taken(id):
		return False
	else:
		return manipulate_object(id=id, object=object)

def push_object(id, object):
	"""
	Takes an ID and an object, then overwrites the object with said ID in the
	database. Returns the pushed object.

	Returns False if the ID does not exist.
	"""
	if id_taken(str(id)):
		return manipulate_object(id=id, object=object)
	else:
		return False

def delete_object(id):
	"""
	Takes an object ID and deletes the object with the provided ID from the
	database. Returns the ID of the deleted object.

	Returns False if the ID does not exist.
	"""
	if id_taken(str(id)):
		del db[str(id)]
		return(id)
	else:
		return False

def id_taken(id):
	"""
	Takes an ID and returns True or False based on whether the ID was found in
	the database.
	"""
	if str(id) in db:
		return True
	else:
		return False

def get_object_as_dict_by_id(id):
	"""
	Takes an object ID and returns a dict containing the object's content.

	Returns None if the ID is not found in the database.
	"""
	if str(id) in db:
		return db[id]
	else:
		return None

def get_object_by_key_value_pair(key_value_dict, limit_objects=False, discard_if_key_with_name_present=[]):
	"""
	Takes a dict with key and value pairs and returns objects that match
	(contain) all key-value pairs. Returns a list with dicts.

	Optional arguments:
	  - limit_objects (default: False) - If set to a number, limits the
	                                     search to the given amount of
	                                     objects.
	  - discard_if_key_with_name_present - If any of the key names in this
	                                       list are found in the object, it
	                                       is discarded.
	"""
	object_match = []
	for object in db.values():
		keys_satisfied = []
		for key, value in key_value_dict.items():
			if key in object:
				if key in discard_if_key_with_name_present:
					continue
				if object[key] == value:
					keys_satisfied.append(key)
		if keys_satisfied == list(key_value_dict.keys()):
			object_match.append(object)

	if object_match:
		if limit_objects:
			return object_match[:limit_objects]
		else:
			return object_match
	return None
