#!/usr/bin/env python3
# coding: utf-8
"""
This file contains tests related to objects. It can be included from other
tests to extend their functionality (in particular, the generate_objects
function can be used to quickly generate objects and IDs for testing
purposes).
"""
from drywall import db
from drywall import objects
from uuid import uuid4
from datetime import datetime

class GeneratedObjects:
	"""Stores generated objects for later tests."""

def generate_objects():
	"""
	This function generates objects of all types and returns a list
	containing the dict with objects and a dict with their IDs, both
	sorted by object type.
	"""
	created_objects = {}
	created_ids = {}
	created_db_objects = {}
	for object in objects.object_types:
		# Reset the created_dict and set our object class. The latter is used to
		# get values like required keys, key types, etc. to know how to fill
		# an object dict.
		created_dict = {"object_type": object}
		object_class = objects.get_object_class_by_type(object)

		# First, we go over all the required keys for the given object:
		for key in object_class.required_keys:
			key_type = object_class.key_types[key]
			# Depending on the key type, we're going to set them differently.
			if key_type == "string":
				if key == "channel_type":
					created_dict[key] = "text"
					created_dict["parent_conference"] = created_ids["conference"]
				elif key == "attachment_type":
					created_dict[key] = "quote"
					created_dict["quoted_message"] = created_ids["message"]
				else:
					# We append a random string here to prevent tests from
					# tripping up on unique keys. We test for those later.
					created_dict[key] = key + "_string_" + str(uuid4())
			elif key_type == "number":
				created_dict[key] = 1
			elif key_type == "boolean":
				created_dict[key] = False
			elif key_type == "permission_map":
				created_dict[key] = 64
			elif key_type == "id":
				id_key_type = object_class.id_key_types[key]
				if id_key_type == "any":
					id_key_type = "message"
				created_dict[key] = created_ids[id_key_type]
			elif key_type == "id_list":
				# While we could just add the same key twice, this might end up
				# breaking once ID list key deduplication is implemented. A way to
				# work around this would be to generate multiple keys for a key
				# type, but this would require a larger chunk of code to handle
				# giving out keys (remember we have to account for singular IDs
				# with the same IDs too). Currently this is not the case however,
				# so we can ignore it for now.
				created_dict[key] = [created_ids[object_class.id_key_types[key]]]
			elif key_type == "datetime":
				# Datetime keys are automatically rewritten upon object creation,
				# so this is ignored.
				created_dict[key] = datetime.utcnow()
			else:
				raise TypeError("Invalid key type")

		# Finally, we create an object from the dict and add it to our
		# created_objects and created_ids dicts, for use in later tests.
		object_generated_from_dict = objects.make_object_from_dict(created_dict)
		created_objects[object] = object_generated_from_dict.__dict__

		# We add our objects to the database, as some of them are required for
		# later tests (like Account objects for the owner variable in Conference
		# objects). However, this also breaks unique keys, so we need to edit
		# them to avoid conflicts when generated objects are used in later tests.
		db.add_object(object_generated_from_dict)
		created_db_objects[object] = vars(object_generated_from_dict)
		if object_class.unique_keys:
			old_dict = object_generated_from_dict.__dict__
			patch_dict = old_dict.copy()
			for key in object_class.unique_keys:
				if object_class.key_types[key] == "string":
					patch_dict[key] = key + "_string_" + str(uuid4())
			if old_dict == patch_dict:
				raise Exception
			patch_from_dict = objects.make_object_from_dict(patch_dict, extend=old_dict['id'])
			created_db_objects[object] = vars(patch_from_dict)
			assert created_db_objects[object]['id'] == old_dict['id']
			db.push_object(old_dict['id'], patch_from_dict)
			assert db.get_object_as_dict_by_id(old_dict['id']) == vars(patch_from_dict)
		created_ids[object] = object_generated_from_dict.__dict__["id"]
		assert created_ids[object] == created_db_objects[object]['id']
	return [created_objects, created_ids, created_db_objects]

def test_validate_objects():
	"""Check for some common object errors"""
	for object in objects.objects:
		for key in object.valid_keys:
			# Check if key has key type set
			assert key in object.key_types.keys()
			key_type = object.key_types[key]
			# Check if key type is correct
			assert key_type in ['string', 'number', 'id', 'id_list', 'list', 'datetime', 'boolean', 'permission_map']
			# If the key is an ID key, check if the ID key type is provided
			if key_type == 'id':
				assert key in object.id_key_types.keys()
		# Check for nonexistent keys (keys not in valid_keys) in:
		key_lists = []
		# - key types
		key_lists.append(object.key_types.keys())
		# - ID key types
		key_lists.append(object.id_key_types.keys())
		# - required keys
		key_lists.append(object.required_keys)
		# - nonrewritable keys
		key_lists.append(object.nonrewritable_keys)
		# - default keys
		key_lists.append(object.default_keys)
		# - unique keys
		key_lists.append(object.unique_keys)
		# ...
		for list in key_lists:
			for key in list:
				assert key in object.valid_keys

def test_generate_objects():
	"""Try to generate objects"""
	generate = generate_objects()
	assert generate
	GeneratedObjects.objects = generate[0]
	GeneratedObjects.ids = generate[1]
	GeneratedObjects.objects_in_db = generate[2]

def test_object_init_failcases():
	"""Object initialization fail cases"""
	# Try invalid ID in ID key field
	test_report = GeneratedObjects.objects['report'].copy()
	test_report['target'] = 'fakeid'
	try:
		objects.Report(test_report)
	except TypeError:
		pass
	else:
		raise Exception("Fake ID test failed!")

	# Try wrong ID key type in ID key field
	test_message = GeneratedObjects.objects['message'].copy()
	test_message['author'] = GeneratedObjects.ids['invite']
	try:
		objects.Message(test_message)
	except TypeError:
		pass
	else:
		raise Exception("Wrong ID type test failed!")

	# Try to fail unique key constraint
	try:
		objects.Account(GeneratedObjects.objects_in_db['account'].copy())
	except TypeError:
		pass
	else:
		raise Exception("Unique key constraint test failed!")

	# Try to fail nonrewritable key check
	try:
		objects.Message(GeneratedObjects.objects['message'].copy(),
			force_id=GeneratedObjects.ids['message'],
			patch_dict={"post_date": "0"})
	except ValueError:
		pass
	else:
		raise Exception("Nonrewritable key test failed!")

	# Try to fail required key test
	test_message.pop('author')
	try:
		objects.Message(test_message)
	except KeyError:
		pass
	else:
		raise Exception("Required key test failed!")

	# Try to init object without providing force_id
	# (this is not recommended, but we provide a workaround, so test it)
	test_role = GeneratedObjects.objects['role'].copy()
	objects.Role(test_role, patch_dict={"name": "test"})
	test_role.pop('id')
	try:
		objects.Role(test_role, patch_dict={"name": "test"})
	except KeyError:
		pass
	else:
		raise Exception("Patch dict with no force_id test failed!")

def test_object_specific_failcases():
	"""Test some object-specific constraints"""
	# Channel: try to create a channel without a parent conference
	channel_dict = GeneratedObjects.objects['channel'].copy()
	channel_dict.pop('parent_conference')
	try:
		objects.Channel(channel_dict)
	except KeyError:
		pass
	else:
		raise Exception("Text channel without parent conference test failed!")

	# Channel: try to create a channel without members/icon (direct_message)
	channel_dict['channel_type'] = 'direct_message'
	try:
		objects.Channel(channel_dict)
	except KeyError:
		pass
	else:
		raise Exception("DM channel without members variable test failed!")
	channel_dict['members'] = []
	try:
		objects.Channel(channel_dict)
	except KeyError:
		pass
	else:
		raise Exception("DM channel without icon variable test failed!")

	# Channel: try fake channel type
	channel_dict['channel_type'] = 'faketype'
	try:
		objects.Channel(channel_dict)
	except KeyError:
		pass
	else:
		raise Exception("Fake channel type test failed!")


	# Message: try to create a message with an edit_date
	message_dict = GeneratedObjects.objects['message'].copy()
	message_dict['edit_date'] = datetime.now()
	message_object = objects.Message(message_dict)
	if 'edit_date' in vars(message_object):
		raise Exception("Edit date removal test failed!")

def test_make_object_dict():
	"""make_object_from_dict() fail cases"""
	# Try to make an object from a correct dict
	test_message = GeneratedObjects.objects['message'].copy()
	objects.make_object_from_dict(test_message)

	# Try to extend nonexistent objects
	try:
		objects.make_object_from_dict(test_message, extend='fakeid')
	except NameError:
		pass
	else:
		raise Exception("Nonexistent object in extend test failed!")

	# Try to make object with fake object type
	try:
		objects.make_object_from_dict({"object_type": "fakeobject"})
	except TypeError:
		pass
	else:
		raise Exception("Fake object type test failed!")

	# Try to fail object creation step
	test_message['author'] = GeneratedObjects.ids['invite']
	try:
		objects.make_object_from_dict(test_message)
	except (KeyError, ValueError, TypeError):
		pass
	else:
		raise Exception("Object creation step fail test failed!")

def test_permissions():
	"""Tests permissions"""
	# Try to create some Permissions objects
	objects.Permissions(0)
	full_perms = objects.Permissions(8191)
	try:
		objects.Permissions(9000)
		objects.Permissions(-1)
	except ValueError:
		pass
	else:
		raise Exception("Permission validation test failed!")
	# Try to run individual functions
	full_perms.validate()
	assert full_perms.break_down_to_values() == list(full_perms.shorthands.values())
	assert full_perms.value_to_shorthands() == list(full_perms.shorthands.keys())

def test_stashes():
	"""Tests stash creation"""
	# Create a stash
	stash_id_list = [GeneratedObjects.ids['account'], GeneratedObjects.ids['message']]
	stash = objects.create_stash(stash_id_list)
	assert stash == {"type": "stash", "id_list": stash_id_list,
		GeneratedObjects.ids['account']: GeneratedObjects.objects_in_db['account'],
		GeneratedObjects.ids['message']: GeneratedObjects.objects['message']}
	# Make a stash with a missing ID
	stash_id_list.append("fakeid")
	try:
		objects.create_stash(stash_id_list)
	except KeyError:
		pass
	else:
		raise Exception("Stash created despite having missing ID in its list")
	# Stuff the ID list with object IDs; we don't check for validity this early,
	# so it's fine
	stash_id_list = ['fakeid'] * 101
	try:
		objects.create_stash(stash_id_list)
	except ValueError:
		pass
	else:
		raise Exception("Stash created despite too many IDs being provided")
