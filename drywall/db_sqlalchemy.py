# coding: utf-8
"""
This is the SQLAlchemy backend, intended to replace all existing
database backends.
"""
from drywall import db_models as models
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)

models.Base.metadata.create_all(engine)

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
		session.query(models.object_type_to_model(object_type)).get(id).delete()
		object_type_query.delete()
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
		object_dict = vars(object)
		object_dict['object_type'] = object_type
		object_dict.pop('_sa_instance_state')
		object_dict_clean = {k: v for k, v in object_dict.items() if v is not None}
		print("DEBUG: " + str(object_dict_clean))
		return object_dict_clean

def get_object_by_key_value_pair(object_type, key_value_dict, limit_objects=False):
	"""
	Takes an object type, a dict with key/value pairs and returns objects that
	match (contain) all key-value pairs. Returns a list with dicts.

	Optional arguments:
	  - limit_objects (default: False) - If set to a number, limits the
	                                     search to the given amount of
	                                     objects.
	"""
	key_count = len(key_value_dict.keys())
	matches = []
	model = models.object_type_to_model(object_type)
	with Session(engine) as session:
		for key, value in key_value_dict.items():
			query = session.query(model).filter(getattr(model, key) == value)
			if query:
				matches.append(vars(query))
	if len(matches) != key_count:
		return query
	else:
		return None

# Users

def get_user_by_email(email):
	"""
	Returns an user's username on the server by email. If not found, returns
	None.
	"""
	if email in user_db:
			return user_db[email]
	return None

def add_user(user_dict):
	"""Adds a new user to the database."""
	user_db[user_dict["email"]] = user_dict
	return user_dict

def update_user(user_email, user_dict):
	"""Edits a user in the database."""
	if user_email == user_dict['email']:
		user_db[user_email] = user_dict
	else:
		if get_user_by_email(user_dict['email']):
			raise ValueError("E-mail is taken.")
		del user_db[user_email]
		user_db[user_dict['email']] = user_dict
	return user_dict

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
