#!/usr/bin/env python3
# encoding: utf-8
"""
This file contains tests for all database backends.
"""
from drywall import objects
from drywall import db
from test_objects import generate_objects
from shutil import copy, move
from os import remove
import simplejson as json

class PregeneratedObjects:
    """Contains pregenerated objects and their IDs."""
    pregenerated_objects = generate_objects()
    dicts = pregenerated_objects[0]
    ids = pregenerated_objects[1]

def test_db():
	"""Tests the current database backend."""
	test_object = PregeneratedObjects.dicts['account']
	test_object_class = objects.make_object_from_dict(test_object)
	test_object['id'] = test_object_class.__dict__['id']
	test_object_id = test_object['id']

	assert db.id_taken("fakeid") == False

	object_add = db.add_object(test_object_class)
	assert db.get_object_as_dict_by_id(test_object_id) != None
	assert db.get_object_as_dict_by_id(test_object_id) == test_object

	assert db.add_object(test_object_class) == False

	test_object['username'] = "edittest"
	test_object_class = objects.make_object_from_dict(test_object, extend=test_object_id)
	object_push = db.push_object(test_object_id, test_object_class)
	assert db.get_object_as_dict_by_id(test_object_id) == test_object

	pair_get = db.get_object_by_key_value_pair({"object_type": "account", "username": "edittest"})
	assert pair_get[0] == test_object

	db.delete_object(test_object_id)
	assert db.id_taken(test_object_id) == False

	test_user = {"username": "test", "email": "mail@example.com", "password": "password", "account_id": PregeneratedObjects.dicts['account']['id']}
	db.add_user(test_user)
	assert db.get_user_by_email("mail@example.com")

	"""
	try:
		db.add_user(test_user)
		raise Exception
	except ValueError:
		pass

	test_user["username"] = "test2"
	try:
		db.add_user(test_user)
		raise Exception
	except ValueError:
		pass
	"""

	# db.remove_user("mail@example.com")
	# assert db.get_user_by_email("mail@example.com") == None
