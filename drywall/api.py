# coding: utf-8
"""
This file contains API path definitions for all API paths.
"""
from drywall import db_dummy as db
from drywall import objects
from drywall import app

import sys

from flask import Flask, Response, request

# Common functions.
def __return_object_by_id(id):
	"""
	Returns an object with a specified ID, as a dictionary. Raises a KeyError
	if there is no object with the given ID.
	"""
	object_dict = db.get_object_as_dict_by_id(str(id))
	if object_dict:
		return object_dict
	else:
		raise KeyError

def __post_object(post_dict):
	"""
	Takes an object dict and adds that object to the database.
	Returns the resulting object.
	"""
	try:
		object_dict = objects.make_object_from_dict(post_dict)
		db.add_object(object_dict)
	except Exception as e:
		raise e
	return object_dict.__dict__

def __patch_object(id, patch_dict):
	"""
	Takes an ID and an object dictionary and applies the contents of that object
	to the object with the given ID. Returns the resulting object.
	"""
	try:
		object_dict = objects.make_object_from_dict(patch_dict, extend=id)
		db.push_object(id, object_dict)
	except Exception as e:
		raise e
	return object_dict.__dict__

def __get_or_patch_method(id, object_type=None):
	"""
	Takes an ID and performs a GET/PATCH operation on the object with the given ID.
	Returns the resulting dict or a Response object in case of failure.
	"""
	try:
		object_dict = __return_object_by_id(id)
	except KeyError:
		return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')
	if object_type:
		if not object_dict['object_type'] == object_type:
			return Response('{"error": "The requested object is not a(n) ' + str(object_type) + '"}', status=400, mimetype='application/json')

	if request.method == "GET":
		return object_dict
	elif request.method == "PATCH":
		if not request.json:
			return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
		return __patch_object(id, request.json)

def __post_method(object_type=None, object_dict=None):
	"""
	Performs a POST operation using object_dict as the input.
	Returns the resulting dict or a Response object in case of failure.
	"""
	if not object_dict:
		object_dict = request.json
	if not object_dict:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	if object_type:
		if not object_dict['object_type'] == object_type:
			return Response('{"error": "The provided object has an incorrect object_type (should be ' + object_type + ')"}', status=400, mimetype='application/json')
	try:
		return __post_object(object_dict)
	except KeyError:
		return Response('{"error": "Missing value: ' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')
	except TypeError:
		return Response('{"error": "' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')


###############
# API methods #
###############

# IDs and instance info

@app.route('/api/v1/instance')
def api_return_instance():
	"""Returns information about the instance."""
	return __return_object_by_id("0")

@app.route('/api/v1/id', methods=['POST'])
def api_id():
	"""POST: Posts an object."""
	return __post_method()

@app.route('/api/v1/id/<id>', methods=['PATCH', 'GET'])
def api_request_or_patch_specific_id(id):
	"""GET/PATCH: Requests or patches an object by ID."""
	return __get_or_patch_method(id)

@app.route('/api/v1/id/<id>/type')
def api_return_object_type_by_id(id):
	"""
	Returns the object type and all other applicable type variables
	of the object with the given ID
	"""
	try:
		object_dict = __return_object_by_id(id)
	except KeyError:
		return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')

	ret_dict = {}
	for key, value in object_dict.items():
		if key == "id" or key == "type" or key == "object_type" or key == "channel_type" or key == "attachment_type" or key == "embed_type":
			ret_dict[key] = value
	return ret_dict

@app.route('/api/v1/stash/request')
def api_return_stash():
	"""GET: Requests a stash."""
	if not request.json:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	else:
		if request.json['id_list']:
			id_list = request.json['id_list']
		else:
			return Response('{"error": "Malformed JSON data (there should be a key called id_list containing a list of IDs)"}', status=400, mimetype='application/json')
	try:
		stash_dict = db.create_stash(id_list)
	except ValueError:
		return Response('{"error": "Too much IDs or no IDs provided (max. 100 IDs)"}', status=400, mimetype='application/json')
	except KeyError:
		return Response('{"error": "' + str(sys.exc_info()[1]) + '"}', status=404, mimetype='application/json')
	return stash_dict

# Accounts

@app.route('/api/v1/accounts', methods=['POST'])
def api_post_message():
	"""POST: Creates an Account object."""
	return __post_method(object_type="account")

@app.route('/api/v1/accounts/<id>', methods=['PATCH', 'GET'])
def api_get_or_patch_account_by_id(id):
	"""GET/PATCH: Returns or patches the object with the given ID if it's an account."""
	return __get_or_patch_method(id, object_type="account")

@app.route('/api/v1/accounts/<bot_id>/invite', methods=['POST'])
def api_invite_bot_to_conference(bot_id):
	"""POST: Adds a bot account to a conference."""
	if not request.json:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	else:
		try:
			bot_user = __return_object_by_id(id)
		except KeyError:
			return Response('{"error": "No object with given ID"}', status=404, mimetype='application/json')
		if not bot_user['bot']:
			return Response('{"error": "Provided ID does not belong to a bot"}', status=400, mimetype='application/json')
		conference_id = request.json['conference_id']
		if not conference_id:
			return Response('{"error": "Malformed JSON data (there should be a key called conference_id containing the conference that the bot will be invited to)"}', status=400, mimetype='application/json')
		# TODO: Figure out how to add a user to a conference
		# Quickly going through the protocol, it seems like we're missing
		# a proper endpoint for joining a conference, we'll take care of
		# that first before we implement this

@app.route('/api/v1/accounts/by-name/<name>', methods=['PATCH', 'GET'])
def api_get_or_patch_account_by_name(name):
	"""GET/PATCH: Returns or patches the account with the given name."""
	object_dict_query = db.get_object_by_key_value_pair({"username": name, "object_type": "account"}, limit_objects=1, discard_if_key_with_name_present=["remote_domain"])
	if not object_dict_query:
		return Response('{"error": "No account with given name found"}', status=404, mimetype='application/json')
	object_dict = object_dict_query[0]

	if request.method == "GET":
		return object_dict
	elif request.method == "PATCH":
		if not request.json:
			return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
		return __patch_object(object_dict['id'], request.json)

# Messages

@app.route('/api/v1/messages', methods=['POST'])
def api_post_message():
	"""POST: Posts a message to the channel specified in the parent_channel value."""
	return __post_method(object_type="message")

@app.route('/api/v1/messages/<id>', methods=['PATCH', 'GET'])
def api_get_or_patch_message_by_id(id):
	"""GET/PATCH: Returns or patches the object with the given ID if it's a message."""
	return __get_or_patch_method(id, object_type="message")

# Conferences

@app.route('/api/v1/conferences', methods=['POST'])
def api_post_conference():
	"""POST: Creates a new conference using the provided object."""
	return __post_method(object_type="conference")

@app.route('/api/v1/conferences/<id>', methods=['PATCH', 'GET'])
def api_get_or_patch_conference_by_id(id):
	"""GET/PATCH: Returns or patches the object with the given ID if it's a conference."""
	return __get_or_patch_method(id, object_type="conference")

