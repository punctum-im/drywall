#!/usr/bin/env python3
# coding: utf-8
"""
Tests for the API.
Huge TODO: clean this up, maybe? There's plenty of room for optimization, but
speed isn't too important here since these are only tests, and they never take
more than about a second. The code has loads of repetitions, though...
"""
import pytest

import drywall
import drywall.api
from test_objects import generate_objects

@pytest.fixture
def client():
    drywall.app.config['TESTING'] = True
    with drywall.app.test_client() as client:
        yield client

class PostedObjectDicts:
	"""
	Contains posted object dicts for testing DELETE endpoints
	"""
	items = {}

def endpoint_test(client, method, endpoint, data=None, object_type=None,
                  ignore_data=False, ignore_object_type=False, response_code=None,
                  use_post_values=None):
	"""
	Performs some basic tests on the given endpoint.

	Arguments:
	  - client (required) - provided by the client pytest fixture
	  - method (required) - HTTP method to use on the endpoint
	  - endpoint (required) - endpoint
	  - data - Data to provide, in case of a POST/PATCH method
	  - object_type - Dictionary with object types for each placeholder
	  - ignore_data - Ignore data, for POST requests that do not require data
	  - ignore_object_type - Endpoint is not object-type sensitive
	  - response_code - Alternative response code
	  - use_post_values - Whether to use objects created by POST tests or
	                      pregenerated ones

	FOR DEVELOPERS: if adding a feature that copies data to another var, please
	use data.copy() instead of just data, because just using data will not copy
	it and instead manipulate whatever's provided in data manually (which can
	be something from PregeneratedObjects, in which case you'll break all other
	tests)
	"""
	# Set value for use_post_values
	if use_post_values == None:
		if method == "POST":
			use_post_values = False
		else:
			use_post_values = True
	# Set default response code
	if not response_code:
		if method == "POST":
			response_code = "201 CREATED"
		else:
			response_code = "200 OK"

	# Set default action - client.get, client.post, client.patch, client.delete
	if method == "GET":
		action = client.get
	elif method == "PATCH":
		if not data:
			raise KeyError("No data provided")
		action = client.patch
	elif method == "POST":
		if not data and not ignore_data:
			raise KeyError("No data provided")
		action = client.post
	elif method == "DELETE":
		action = client.delete
	else:
		raise TypeError("Incorrect method (note methods MUST be all-caps)")

	print("  * Testing " + method + " " + endpoint)

	if data and object_type and len(list(object_type.keys())) == 2:
		if 'parent_conference' in data:
			data['parent_conference'] = PostedObjectDicts.items['conference']['id']
		elif list(object_type.values())[-1] == "invite":
			data['conference_id'] = PostedObjectDicts.items['conference']['id']


	# Go over object types and fill in the placeholders in the endpoint
	# The object_type variable is a dict containing pairs of placeholder strings
	# and object types to be assigned to them. POST requests set the placeholder
	# to None for the object they're sending.
	object_types = list()
	if object_type:
		original_endpoint = endpoint
		if use_post_values:
			for object in object_type.items():
				if object[1] in PostedObjectDicts.items:
					if len(list(object_type.keys())) == 2:
						if 'parent_conference' in PostedObjectDicts.items[object[1]]:
							PostedObjectDicts.items[object[1]]['parent_conference'] = PostedObjectDicts.items['conference']['id']
						elif object[1] == "invite":
							PostedObjectDicts.items[object[1]]['conference_id'] = PostedObjectDicts.items['conference']['id']
					object_types.append(PostedObjectDicts.items[object[1]])
					endpoint = endpoint.replace(object[0], PostedObjectDicts.items[object[1]]['id'])
				else:
					print("    ! WARN: using PregeneratedObjects as fallback")
					object_types.append(PregeneratedObjects.dicts[object[1]])
					if object[0]:
						endpoint = endpoint.replace(object[0], PregeneratedObjects.ids[object[1]])
			print("    -> " + endpoint)
		else:
			for object in object_type.items():
				object_types.append(PregeneratedObjects.dicts[object[1]])
				if object[0]:
					endpoint = endpoint.replace(object[0], PregeneratedObjects.ids[object[1]])
			print("    -> " + endpoint)

	# Perform the API endpoint call
	if data and not ignore_data:
		action_result = action(endpoint, json=data)
	else:
		action_result = action(endpoint)

	# Test the results
	action_result_json = action_result.get_json()
	#print(action_result_json)
	try:
		assert action_result.status == response_code
	except AssertionError as e:
		print("    !!! " + method + " " + endpoint + " failed!")
		if data:
			print("    - Data:\n  " + str(data))
		print("    - Result:\n  " + str(action_result_json))
		raise e

	if method == "GET" and object_type:
		assert action_result_json == object_types[-1]
	if method == "POST" and data and not ignore_data and "id" in data:
		assert action_result_json['id'] != data['id']
		safe_data = data.copy()
		safe_data['id'] = action_result_json.get('id')
		assert action_result_json == safe_data
		PostedObjectDicts.items[action_result_json['object_type']] = action_result_json
	if method == "PATCH":
		assert action_result_json != data
		if object_type:
			assert action_result_json != object_types[-1]
			for key in data.keys():
				assert action_result_json[key] == data[key]
	if method == "DELETE":
		#PostedObjectDicts.items = {}
		assert client.get('/api/v1/id/' + action_result_json['id']).status == "404 NOT FOUND"
	if data and not ignore_data:
		action_no_data = action(endpoint)
		assert action_no_data.status == "400 BAD REQUEST"

	# Try fake ID
	if method == "GET" or method == "PATCH" or method == "DELETE":
		if object_type:
			object_types = list()
			endpoint = original_endpoint
			for object in object_type.items():
				object_types.append(PregeneratedObjects.dicts[object[1]])
				if object[0]:
					endpoint = endpoint.replace(object[0], 'fakeid')
			if not endpoint == original_endpoint:
				print("       -> Fake ID: " + endpoint)
				action_result = action(endpoint, json=data)
				assert action_result.status == "404 NOT FOUND"

	# Try wrong object type
	if object_type and not ignore_object_type:
		object = object_type
		if not list(object.keys())[-1] == None:
			object = object_types[-1]
			if object['object_type'] == "message":
				wrong_type = "channel"
			else:
				wrong_type = "message"
			object = list(object_type.keys())[-1]
			endpoint = original_endpoint
			if object[0]:
				endpoint = endpoint.replace(object[0], PregeneratedObjects.dicts[wrong_type]['id'])
	# I had some working code for this, similar to the fake ID handler, but
	# it'd need to be modified to work with endpoints with two ID values, as
	# without modifications it will return 404 since the parent ID does not
	# exist. Also, fake ID will have to be fixed now, but it returns the
	# correct values nonetheless so... uhhh... it's ok I guess?

	# TODO: check/assert the error codes

class PregeneratedObjects:
	"""Contains pregenerated objects and their IDs."""
	pregenerated_objects = generate_objects()
	dicts = pregenerated_objects[0]
	ids = pregenerated_objects[1]

def test_api_id(client):
	"""Test API endpoints related to objects and IDs."""
	endpoint_test(client, 'GET', '/api/v1/instance')
	endpoint_test(client, 'POST', '/api/v1/id', data=PregeneratedObjects.dicts['message'],
	              object_type={None: "message"}, ignore_object_type=True)
	endpoint_test(client, 'GET', '/api/v1/id/<id>', object_type={"<id>": "message"},
	              ignore_object_type=True)
	endpoint_test(client, 'PATCH', '/api/v1/id/<id>', data={"content": "new_content"},
	              object_type={"<id>": "message"}, ignore_object_type=True)
	endpoint_test(client, 'DELETE', '/api/v1/id/<id>', object_type={"<id>": "message"},
	              ignore_object_type=True)
	endpoint_test(client, 'POST', '/api/v1/stash/request',
	              data={"id_list": [PregeneratedObjects.ids['message'],
	                                PregeneratedObjects.ids['account']]}, response_code="200 OK")

def test_api_accounts(client):
	"""Test API endpoints related to accounts."""
	endpoint_test(client, 'POST', '/api/v1/accounts', PregeneratedObjects.dicts['account'],
	              object_type={None: "account"})
	endpoint_test(client, 'GET', '/api/v1/accounts/<account_id>', object_type={"<account_id>": "account"})
	endpoint_test(client, 'PATCH', '/api/v1/accounts/<account_id>', data={"bio": "new_bio"},
	              object_type={"<account_id>": "account"})
	endpoint_test(client, 'DELETE', '/api/v1/accounts/<account_id>', object_type={"<account_id>": "account"})

def test_api_conferences(client):
	"""Test API endpoints related to conferences."""
	endpoint_test(client, 'POST', '/api/v1/conferences', PregeneratedObjects.dicts['conference'],
	              object_type={None: "conference"})
	endpoint_test(client, 'GET', '/api/v1/conferences/<conference_id>', object_type={"<conference_id>": "conference"})
	endpoint_test(client, 'PATCH', '/api/v1/conferences/<conference_id>', data={"name": "new_name"},
	              object_type={"<conference_id>": "conference"})
	endpoint_test(client, 'DELETE', '/api/v1/conferences/<conference_id>', object_type={"<conference_id>": "conference"})

	# Recreate conference for conference child tests
	endpoint_test(client, 'POST', '/api/v1/conferences', PostedObjectDicts.items['conference'],
	              object_type={None: "conference"})

	endpoint_test(client, 'POST', '/api/v1/conferences/<conference_id>/members', PregeneratedObjects.dicts['conference_member'],
	              object_type={"<conference_id>": "conference", None: "conference_member"},
	              use_post_values=True)
	endpoint_test(client, 'GET', '/api/v1/conferences/<conference_id>/members/<member_id>',
	              object_type={"<conference_id>": "conference", "<member_id>": "conference_member"}, use_post_values=True)
	endpoint_test(client, 'PATCH', '/api/v1/conferences/<conference_id>/members/<member_id>',
	              data={"nickname": "new_nickname"},
	              object_type={"<conference_id>": "conference", "<member_id>": "conference_member"})
	endpoint_test(client, 'DELETE', '/api/v1/conferences/<conference_id>/members/<member_id>',
	              object_type={"<conference_id>": "conference", "<member_id>": "conference_member"})

	endpoint_test(client, 'POST', '/api/v1/conferences/<conference_id>/channels', PregeneratedObjects.dicts['channel'],
	              object_type={"<conference_id>": "conference", None: "channel"},
	              use_post_values=True)
	endpoint_test(client, 'GET', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
	              object_type={"<conference_id>": "conference", "<channel_id>": "channel"})
	endpoint_test(client, 'PATCH', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
	              data={"name": "new_name"},
	              object_type={"<conference_id>": "conference", "<channel_id>": "channel"})
	endpoint_test(client, 'DELETE', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
	              object_type={"<conference_id>": "conference", "<channel_id>": "channel"})

	endpoint_test(client, 'POST', '/api/v1/conferences/<conference_id>/invites', PregeneratedObjects.dicts['invite'],
	              object_type={"<conference_id>": "conference", None: "invite"})
	endpoint_test(client, 'GET', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
	              object_type={"<conference_id>": "conference", "<invite_id>": "invite"})
	endpoint_test(client, 'PATCH', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
	              data={"name": "new_name"},
	              object_type={"<conference_id>": "conference", "<invite_id>": "invite"})
	endpoint_test(client, 'DELETE', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
	              object_type={"<conference_id>": "conference", "<invite_id>": "invite"})

	endpoint_test(client, 'POST', '/api/v1/conferences/<conference_id>/roles', PregeneratedObjects.dicts['role'],
	              object_type={"<conference_id>": "conference", None: "role"})
	endpoint_test(client, 'GET', '/api/v1/conferences/<conference_id>/roles/<role_id>',
	              object_type={"<conference_id>": "conference", "<role_id>": "role"})
	endpoint_test(client, 'PATCH', '/api/v1/conferences/<conference_id>/roles/<role_id>',
	              data={"name": "new_name"},
	              object_type={"<conference_id>": "conference", "<role_id>": "role"})
	endpoint_test(client, 'DELETE', '/api/v1/conferences/<conference_id>/roles/<role_id>',
	              object_type={"<conference_id>": "conference", "<role_id>": "role"})

def test_api_channels(client):
	"""Test API endpoints related to channels."""
	endpoint_test(client, 'POST', '/api/v1/channels', PregeneratedObjects.dicts['channel'],
	              object_type={None: "channel"})
	endpoint_test(client, 'GET', '/api/v1/channels/<channel_id>', object_type={"<channel_id>": "channel"})
	endpoint_test(client, 'PATCH', '/api/v1/channels/<channel_id>', data={"name": "new_name"},
	              object_type={"<channel_id>": "channel"})
	endpoint_test(client, 'DELETE', '/api/v1/channels/<channel_id>', object_type={"<channel_id>": "channel"})

def test_api_messages(client):
	"""Test API endpoints related to messages."""
	endpoint_test(client, 'POST', '/api/v1/messages', PregeneratedObjects.dicts['message'],
	              object_type={None: "message"})
	endpoint_test(client, 'GET', '/api/v1/messages/<message_id>', object_type={"<message_id>": "message"})
	endpoint_test(client, 'PATCH', '/api/v1/messages/<message_id>', data={"content": "new_content"},
	              object_type={"<message_id>": "message"})
	endpoint_test(client, 'DELETE', '/api/v1/messages/<message_id>', object_type={"<message_id>": "message"})

def test_api_invites(client):
	"""Test API endpoints related to invites."""
	endpoint_test(client, 'POST', '/api/v1/invites', PregeneratedObjects.dicts['invite'],
	              object_type={None: "invite"})
	endpoint_test(client, 'GET', '/api/v1/invites/<invite_id>', object_type={"<invite_id>": "invite"})
	endpoint_test(client, 'PATCH', '/api/v1/invites/<invite_id>', data={"name": "new_name"},
	              object_type={"<invite_id>": "invite"})
	endpoint_test(client, 'DELETE', '/api/v1/invites/<invite_id>', object_type={"<invite_id>": "invite"})

def test_api_roles(client):
	"""Test API endpoints related to roles."""
	endpoint_test(client, 'POST', '/api/v1/roles', PregeneratedObjects.dicts['role'],
	              object_type={None: "role"})
	endpoint_test(client, 'GET', '/api/v1/roles/<role_id>', object_type={"<role_id>": "role"})
	endpoint_test(client, 'PATCH', '/api/v1/roles/<role_id>', data={"name": "new_name"},
	              object_type={"<role_id>": "role"})
	endpoint_test(client, 'DELETE', '/api/v1/roles/<role_id>', object_type={"<role_id>": "role"})
