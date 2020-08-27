# coding: utf-8
"""
This file contains definitions of all the API paths and is meant to be ran as a
Flask app.
"""
import objects, settings
import db_dummy as db

import sys
from flask import Flask, Response, request
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

VERSION = "0.1"

# Define our instance.
if not db.id_taken('0'):
	instance_dict = {"type": "object", "object_type": "instance", "address": settings.get('instance_domain'), "server_software": "drywall " + VERSION, "name": settings.get('instance_name'), "description": settings.get('instance_description')}
	created_instance_object = objects.make_object_from_dict(instance_dict, extend=0, ignore_nonexistent_id_in_extend=True)
	if not db.add_object(created_instance_object):
		raise ValueError('Unable to create the object')
instance = db.get_object_as_dict_by_id('0')

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
	return object_dict

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
	return object_dict

###############
# API methods #
###############

# IDs and instance info

@app.route('/api/v1/instance')
def api_return_instance():
	"""Returns information about the instance."""
	try:
		return __return_object_by_id("0")
	except KeyError:
		return Response('{"error": "No object with the ID 0 found. This should not happen! Please file a bug in the drywall repository."}', status=500, mimetype='application/json')

@app.route('/api/v1/id', methods=['POST'])
def api_id():
	"""POST: Posts an object."""
	if not request.json:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	else:
		try:
			return __post_object(request.json)
		except KeyError:
			return Response('{"error": "Missing value: ' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')
		except ValueError:
			return Response('{"error": "Attempted to replace nonreplacable value: ' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')
		except TypeError:
			return Response('{"error": "' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')

@app.route('/api/v1/id/<id>', methods=['PATCH', 'GET'])
def api_request_or_patch_specific_id(id):
	"""
	GET: Requests an object by ID.
	PATCH: Patches the object with the specified ID.
	"""
	if request.method == "GET":
		try:
			return __return_object_by_id(id)
		except:
			return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')

	elif request.method == "PATCH":
		if not request.json:
			return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
		else:
			try:
				return __patch_object(id, request.json)
			except KeyError:
				return Response('{"error": "Missing value: ' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')
			except ValueError:
				return Response('{"error": "Attempted to replace nonreplacable value: ' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')
			except (NameError, TypeError):
				return Response('{"error": "' + str(sys.exc_info()[1]) + '"}', status=400, mimetype='application/json')

@app.route('/api/v1/id/<id>/type')
def api_return_object_type_by_id(id):
	"""Returns the object type of the object with the given ID"""
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
	"""Requests a stash"""
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

@app.route('/api/v1/accounts/<id>', methods=['PATCH', 'GET'])
def api_get_or_patch_account_by_id(id):
	"""Returns or patches the object with the given ID if it's an account."""
	object_dict = __return_object_by_id(id)
	if not object_dict['object_type'] == "account":
		return Response('{"error": "Provided ID does not belong to an account."}', status=400, mimetype='application/json')

	if request.method == "GET":
		return object_dict
	elif request.method == "PATCH":
		if not request.json:
			return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
		return __patch_object(id, request.json)

@app.route('/api/v1/accounts/<bot_id>/invite', methods=['POST'])
def api_invite_bot_to_conference(bot_id):
	"""Adds a bot account to a conference."""
	if not request.json:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	else:
		try:
			bot_user = __return_object_by_id(id)
		except:
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

@app.route('/api/v1/accounts/<name>', methods=['PATCH', 'GET'])
def api_get_or_patch_account_by_name(name):
	"""Returns or patches the account with the given name."""
	return db.get_object_by_key_value_pair({"name": name, "object_type": "account"}, limit_objects=1)
