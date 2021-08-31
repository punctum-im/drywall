# coding: utf-8
"""
This is the SQLAlchemy backend, intended to replace all existing
database backends.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from drywall import db_models as models
from drywall import config

# !!! IMPORTANT !!! --- !!! IMPORTANT !!! --- !!! IMPORTANT !!!
# If you came here to change the database type, ***DON'T***.
# Drywall relies on some Postgres-specific features to function:
#
# - datetime support for dates; we could just store them as strings,
#   but having proper date support is useful for search APIs.
#
# - arrays, for ID lists (and lists in general); the only alternatives
#   for this are storing lists as strings or using pickles, both of
#   which would basically be asking for RCE vulnerabilities.
#   Alternatively, you could use JSON for this, but we'll provide
#   limited support for this hack.
#
# If you wanted to change the DB to in-memory sqlite for testing: there's
# no need to! See the test runner script (tests/test_runner.sh) for more
# information on how to prepare a database for one-time use.
# !!! IMPORTANT !!! --- !!! IMPORTANT !!! --- !!! IMPORTANT !!!
engine = create_engine("postgresql://%s:%s@localhost/%s" % (config.get('db_user'), config.get('db_password'), config.get('db_name')), future=True)

models.Base.metadata.create_all(engine)

# The current client DB functions are due to be deprecated once we add authlib
# support. Thus, we'll re-use the old dummy DB backend functions for it.
client_db = {}

# Helper functions

def clean_object_dict(object_dict, object_type):
	"""Adds type/object_type values to an object_dict and removes empty keys"""
	object_dict['type'] = 'object'
	object_dict['object_type'] = object_type
	object_dict_clean = {k: v for k, v in object_dict.items() if v is not None}
	return object_dict_clean

# Objects

def add_object(object):
	"""
	Takes an object and inserts it into the database. Returns the inserted object.

	Returns False if the ID is already taken.
	"""
	object_dict = vars(object)

	id = object_dict['id']
	if id_taken(str(id)):
		return False

	with Session(engine) as session:
		object_type = object_dict['object_type']
		new_type_object = models.object_type_to_model(object_type)()
		new_generic_object = models.Objects(id=id, object_type=object_type)
		for key, value in object_dict.items():
			setattr(new_type_object, key, value)
		session.add(new_type_object)
		session.add(new_generic_object)
		session.commit()

	return object_dict

def push_object(id, object):
	"""
	Takes an ID and an object, then overwrites the object with said ID in the
	database. Returns the pushed object.

	Returns False if the ID does not exist.
	"""
	object_dict = vars(object)

	if not id_taken(str(id)):
		return False

	with Session(engine) as session:
		object_type = session.query(models.Objects).get(id).object_type
		new_object = session.query(models.object_type_to_model(object_type)).get(id)
		for key, value in object_dict.items():
			setattr(new_object, key, value)
		session.commit()

	return object_dict

def delete_object(id):
	"""
	Takes an object ID and deletes the object with the provided ID from the
	database. Returns the ID of the deleted object.

	Returns False if the ID does not exist.
	"""
	with Session(engine) as session:
		object_type_query = session.query(models.Objects).get(id)
		if not object_type_query:
			return None
		object_type = object_type_query.object_type
		object = session.query(models.object_type_to_model(object_type)).get(id)
		session.delete(object)
		session.delete(object_type_query)
		session.commit()

	return id

def id_taken(id):
	"""
	Takes an ID and returns True or False based on whether the ID was found in
	the database.
	"""
	with Session(engine) as session:
		if session.query(models.Objects).get(id):
			return True
		else:
			return False

def get_object_as_dict_by_id(id):
	"""
	Takes an object ID and returns a dict containing the object's content.

	Returns None if the ID is not found in the database.
	"""
	if not id:
		return None

	with Session(engine) as session:
		object_type_query = session.query(models.Objects).get(id)
		if not object_type_query:
			return None
		object_type = object_type_query.object_type
		object = session.query(models.object_type_to_model(object_type)).get(id)
		object_dict = object.to_dict()
		return clean_object_dict(object_dict, object_type)

def get_object_by_key_value_pair(object_type, key_value_dict, limit_objects=False):
	"""
	Takes an object type, a dict with key/value pairs and returns objects that
	match (contain) the key-value pair. Returns a list with dicts.

	Optional arguments:
	  - limit_objects (default: False) - If set to a number, limits the
	                                     search to the given amount of
	                                     objects.
	"""
	matches = []
	model = models.object_type_to_model(object_type)
	with Session(engine) as session:
		for key, value in key_value_dict.items():
			query = session.query(model).filter(getattr(model, key) == value).all()
			if query:
				for object in query:
					matches.append(clean_object_dict(object.to_dict(), object_type))
	if matches:
		return matches
	else:
		return None

# Users

def get_user_by_email(email):
	"""
	Returns an user's username on the server by email. If not found, returns
	None.
	"""
	user_dict = None
	with Session(engine) as session:
		query = session.query(models.User).get(email)
		if query:
			user_dict = query.to_dict()
	return user_dict

def add_user(user_dict):
	"""Adds a new user to the database."""
	with Session(engine) as session:
		new_user = models.User()
		for key in ['account_id', 'username', 'email', 'password']:
			setattr(new_user, key, user_dict[key])
		session.add(new_user)
		session.commit()
		new_user_dict = new_user.to_dict()
	return new_user_dict

def update_user(user_email, user_dict):
	"""Edits a user in the database."""
	with Session(engine) as session:
		object = session.query(models.User).get(user_email)
		if user_email != user_dict['email']:
			if get_user_by_email(user_email):
				raise ValueError("E-mail is taken")
		for key in ['account_id', 'username', 'email', 'password']:
			setattr(object, key, user_dict[key])
		session.commit()
		new_user_dict = object.to_dict()
	return new_user_dict

def remove_user(email):
	"""Removes a user from the database."""
	# This will be implemented once we can figure out all the related
	# side-effects, like removing/adding stubs to orphaned objects or
	# removing the user's Account object.
	raise Exception('stub')

# Clients

def get_client_by_id(client_id):
	"""Returns a client dict by client ID. Returns None if not found."""
	if id in client_db:
		return client_db['id']
	return None

def get_clients_for_user(user_id, access_type):
	"""Returns a dict containing all clients owned/given access to by an user."""
	return_dict = {}
	if access_type == "owner":
		for client_dict in client_db.values():
			if client_dict['owner'] == user_id:
				return_dict[client_dict['client_id']] == client_dict
	elif access_type == "user":
		# TODO: We should let people view the apps they're using and
		# revoke access if needed. This will most likely require adding
		# an extra variable to the user dict for used applications, which
		# we could then iterate using simmilar code as above.
		# For now, we'll stub this.
		raise Exception('stub')
	else:
		raise ValueError
	if return_dict:
		return return_dict
	return None

def add_client(client_dict):
	"""Adds a new client to the database."""
	client_db[client_dict['id']] = client_dict
	return client_dict

def update_client(client_id, client_dict):
	"""Updates an existing client"""
	client_db[client_id] = client_dict
	return client_dict

def remove_client(client_id):
	"""Removes a client from the database."""
	del client_db[client_id]
	# TODO: Handle removing removed clients from "used applications" variables
	# in user info; since we don't implement this yet, there's no code for it
	return client_id
