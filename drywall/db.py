# coding: utf-8
"""
This is the SQLAlchemy backend, intended to replace all existing
database backends.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from drywall import db_models as models
from drywall import auth_models # noqa: F401
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
