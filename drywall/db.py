# encoding: utf-8
"""
Main database module. Loads the database backend selected in the settings.
"""
import json
from drywall import config

if not config.get("db_backend"):
	raise KeyError("No database backend selected!")
backend = config.get('db_backend')

if backend == 'dummy':
	from drywall import db_dummy as db_backend
elif backend == 'sqlite':
	from drywall import db_sqlite as db_backend
elif backend == 'sqlalchemy':
	from drywall import db_sqlalchemy as db_backend
#elif backend == 'mysql':
#	from drywall import db_mysql as db_backend
else:
	raise TypeError("Incorrect database backend type " + backend)

# Objects

def add_object(object):
	"""
	Takes an object and inserts it into the database. Returns the inserted object.

	Returns False if the ID is already taken.
	"""
	return db_backend.add_object(object)

def push_object(id, object):
	"""
	Takes an ID and an object, then overwrites the object with said ID in the
	database. Returns the pushed object.

	Returns False if the ID does not exist.
	"""
	return db_backend.push_object(id, object)

def delete_object(id):
	"""
	Takes an object ID and deletes the object with the provided ID from the
	database. Returns the ID of the deleted object.

	Returns False if the ID does not exist.
	"""
	return db_backend.delete_object(id)

def id_taken(id):
	"""
	Takes an ID and returns True or False based on whether the ID was found in
	the database.
	"""
	return db_backend.id_taken(id)

def get_object_as_dict_by_id(id):
	"""
	Takes an object ID and returns a dict containing the object's content.

	Returns None if the ID is not found in the database.
	"""
	return db_backend.get_object_as_dict_by_id(id)

def get_object_by_key_value_pair(object_type, key_value_dict, limit_objects=False):
	"""
	Takes an object type, a dict with key/value pairs and returns objects that
	match (contain) all key-value pairs. Returns a list with dicts.

	Optional arguments:
	  - limit_objects (default: False) - If set to a number, limits the
	                                     search to the given amount of
	                                     objects.
	"""
	return db_backend.get_object_by_key_value_pair(object_type=object_type, key_value_dict=key_value_dict, limit_objects=limit_objects)

# Users

def get_user_by_email(email):
	"""
	Returns an user's username on the server by email. If not found, returns
	None.
	"""
	return db_backend.get_user_by_email(email)

def add_user(user_dict):
	"""
	Adds a new user to the database.
	"""
	if get_user_by_email(user_dict['email']):
		raise ValueError("E-mail is taken.")
	return db_backend.add_user(user_dict)

def update_user(user_email, user_dict):
	"""Adds a new client to the database."""
	return db_backend.update_user(user_email, user_dict)

def remove_user(email):
	"""
	Removes an user from the database.
	"""
	return db_backend.remove_user(email)

# Clients

def get_client_by_id(client_id):
	"""Returns a client dict by client ID. Returns None if not found."""
	return db_backend.get_client_by_id(client_id)

def get_clients_for_user(user_id, access_type):
	"""Returns a dict containing all clients owned/given access to by an user."""
	return db_backend.get_clients_for_user(user_id, access_type)

def add_client(client_dict):
	"""Adds a new client to the database."""
	return db_backend.add_client(client_dict)

def update_client(client_id, client_dict):
	"""Replaces a client object in the database."""
	return db_backend.update_client(client_id, client_dict)

def remove_client(client_id):
	"""Removes a client from the database."""
	return db_backend.remove_client(client_id)
