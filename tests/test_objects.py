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

def generate_objects():
	"""
	This function generates objects of all types and returns a list
	containing the dict with objects and a dict with their IDs, both
	sorted by object type.
	"""
	created_objects = {}
	created_ids = {}
	for object in ['instance', 'account', 'conference', 'conference_member', 'invite', 'role', 'channel', 'message', 'report']:
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
					created_dict[key] = key + "_string"
			elif key_type == "number":
				created_dict[key] = 1
			elif key_type == "boolean":
				created_dict[key] = "false"
			elif key_type == "permission_map":
				created_dict[key] = "11111"
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
			else:
				raise TypeError("Invalid key type")

		# Finally, we create an object from the dict and add it to our
		# created_objects and created_ids dicts, for use in later tests.
		object_generated_from_dict = objects.make_object_from_dict(created_dict)
		created_objects[object] = object_generated_from_dict.__dict__
		db.add_object(object_generated_from_dict)
		created_ids[object] = object_generated_from_dict.__dict__["id"]

	return [created_objects, created_ids]

def test_generate_objects():
	"""For pytest: run the above function"""
	assert generate_objects()
