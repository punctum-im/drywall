#!/usr/bin/env python3
# coding: utf-8
"""
Tests for the API portions of the code.
For authentication pages, see tests/test_auth.py.
"""
import pytest

import drywall
import drywall.api
import drywall.objects
from test_objects import generate_objects

#
# Helper functions and structures
#

@pytest.fixture
def client():
    drywall.app.config['TESTING'] = True
    with drywall.app.test_client() as client:
        yield client

class PregeneratedObjects:
	"""Contains pregenerated objects and their IDs."""
	pregenerated_objects = generate_objects()
	dicts = pregenerated_objects[0]
	ids = pregenerated_objects[1]
	db_dicts = pregenerated_objects[2]

class PostedObjectDicts:
	"""
	Contains posted object dicts for testing DELETE endpoints
	"""
	items = {}

def _posted_id(object_type):
	"""
	Returns the object ID for an object with the provided object type from
	posted objects.
	"""
	return PostedObjectDicts.items[object_type]['id']

def _posted_dict(object_type):
	"""
	Returns the object dict for an object with the provided object type from
	posted objects.
	"""
	return PostedObjectDicts.items[object_type]

def _pregenerated_id(object_type):
	"""
	Returns the object ID for an object with the provided object type from
	pregenerated objects.
	"""
	return PregeneratedObjects.ids[object_type]

def _pregenerated_dict(object_type):
	"""
	Returns the object dict for an object with the provided object type from
	pregenerated objects.

	Note that this will return the item as it appears in the database,
	so it MUST NOT be used for POST requests - it should be used in GET
	requests instead. For the original generated dict see
	_pregenerated_example_dict.

	This distinction is important because generated objects in the database
	have values of unique keys changed from the ones that were generated
	initially.
	"""
	return PregeneratedObjects.db_dicts[object_type]

def _pregenerated_example_dict(object_type):
	"""
	Returns the example object dict for an object with the provided object type
	from pregenerated objects.

	Note that this will return the item as it was originally generated, and
	should only be used for POST requests; for the dict of the object as it
	appears in the database, see _pregenerated_dict.

	This distinction is important because generated objects in the database
	have values of unique keys changed from the ones that were generated
	initially.
	"""
	return PregeneratedObjects.dicts[object_type]

#
# Endpoint helper functions
#

def _fill_placeholder_in_endpoint(endpoint, object_type_dict, use_posted=False):
	"""
	Fills the placeholder in the endpoint automatically.

	Returns the filled endpoint.
	"""
	placeholder = None
	object_type = None
	if object_type_dict:
		placeholder = list(object_type_dict.keys())[0]
		object_type = list(object_type_dict.values())[0]

	# Get target ID
	if use_posted:
		if object_type:
			target_id = _posted_id(object_type)
		else:
			target_id = _posted_id('message')
	else:
		if object_type:
			target_id = _pregenerated_id(object_type)
		else:
			# Some endpoints, like '/api/v1/id/<id>', can take any object type.
			# In this case, get a random object to fill it in; we leave the
			# provided object_type variable set to None, as it affects the
			# behavior of _endpoint_sanity_checks later on.
			target_id = _pregenerated_id('message')

	# Fill in placeholder
	if placeholder:
		if object_type:
			_endpoint = endpoint.replace(placeholder, target_id)
		else:
			_endpoint = endpoint.replace(placeholder, target_id)
	else:
		_endpoint = endpoint

	return _endpoint

def _endpoint_sanity_checks(_endpoint, method, action, object_type_dict=None):
	"""
	Performs basic checks applicable to every endpoint.

	Arguments:
	  - endpoint (required) - the endpoint to test
	  - method (required) - GET/POST/PATCH/DELETE; must match action
	  - action (required) - flask_client.get/post/patch/delete
	  - object_type_dict - the object type to test, as a dict with a key-value
	                       pair representing the endpoint placeholder and
	                       object type, or in the case of POST endpoints just
	                       the object_type
	"""
	placeholder = None
	object_type = None
	if object_type_dict:
		placeholder = list(object_type_dict.keys())[0]
		object_type = list(object_type_dict.values())[0]

	# Try nonexistent ID (should return 404)
	if placeholder:
		print("       -> Fake ID test")
		missing_endpoint = _endpoint.replace(placeholder, 'fakeid')
		assert action(missing_endpoint).status == "404 NOT FOUND"

	# Try object with wrong object type (should return 400)
	if object_type:
		print("       -> Wrong object type test")
		if placeholder:
			if object_type == 'message':
				wrong_endpoint = _endpoint.replace(placeholder, _pregenerated_id('channel'))
			else:
				wrong_endpoint = _endpoint.replace(placeholder, _pregenerated_id('message'))
		else:
			wrong_endpoint = _endpoint
		if method == 'POST' or method == 'PATCH':
			if object_type == 'message':
				wrong_object = _pregenerated_dict('channel')
			else:
				wrong_object = _pregenerated_dict('message')
			assert action(wrong_endpoint, json=wrong_object).\
					status == "400 BAD REQUEST"
		else:
			assert action(wrong_endpoint).status == "400 BAD REQUEST"

#
# General test shorthands
#

def endpoint_get(flask_client, endpoint, object_type=None, use_posted=False):
	"""
	Performs tests on a GET endpoint.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - endpoint (required) - the endpoint to test
	  - object_type - dict containing one key and value: the key is the
	                  placeholder string, the value is the object type.
	                  If the endpoint accepts any object type, the object
	                  type must be set to None.
	  - use_posted - whether to use a posted object or a pregenerated one.
	"""
	print("  * Testing: GET " + endpoint)

	get = flask_client.get

	# Fill in placeholder
	original_endpoint = endpoint
	endpoint = _fill_placeholder_in_endpoint(original_endpoint, object_type,
											use_posted=use_posted)

	# Get the object dict that should be returned
	_object_type = list(object_type.values())[0]
	if use_posted:
		if _object_type:
			expected_object_dict = _posted_dict(_object_type)
		else:
			expected_object_dict = _posted_dict('message')
	else:
		if _object_type:
			expected_object_dict = _pregenerated_dict(_object_type)
		else:
			expected_object_dict = _pregenerated_dict('message')

	# First, test the endpoint in question:
	result = get(endpoint)
	try:
		assert result.status == "200 OK"
		assert result.json == expected_object_dict
	except AssertionError as e:
		print("Filled endpoint: " + endpoint)
		print("Data:\n" + str(result.json))
		raise e

	# Then, perform the usual checks, such as 404, wrong object type, etc.
	_endpoint_sanity_checks(original_endpoint, 'GET', get, object_type)

def endpoint_post(flask_client, endpoint, object_type=None, data=None,
					posts_object=True):
	"""
	Performs tests on a POST endpoint.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - endpoint (required) - the endpoint to test
	  - object_type - object type to test; None if the endpoint accepts
	                  any object type
	  - data - the data to send in the request
	  - posts_object - whether the resulting object should be added
	                   to PostedObjectDicts
	"""
	print("  * Testing: POST " + endpoint)

	post = flask_client.post

	if not data:
		if object_type:
			data = _pregenerated_example_dict(object_type)
		else:
			data = _pregenerated_example_dict('message')

	result = post(endpoint, json=data)
	try:
		assert result.status == "201 CREATED"
		assert result.json['id'] != data['id']
	except AssertionError as e:
		print("Filled endpoint: " + endpoint)
		print("Returned data:\n" + str(result.json))
		raise e

	if posts_object:
		PostedObjectDicts.items[result.json['object_type']] = result.json

	# Then, perform the usual checks, such as 404, wrong object type, etc.
	_endpoint_sanity_checks(endpoint, 'POST', post, {None: object_type})

def endpoint_patch(flask_client, endpoint, object_type=None, data=None):
	"""
	Performs tests on a PATCH endpoint.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - endpoint (required) - the endpoint to test
	  - object_type - dict containing one key and value: the key is the
	                  placeholder string, the value is the object type.
	                  If the endpoint accepts any object type, the object
	                  type must be set to None.
	  - data - the data to send in the request
	"""
	print("  * Testing: PATCH " + endpoint)

	_object_type = list(object_type.values())[0]
	if _object_type:
		original_object_dict = _posted_dict(_object_type)
	else:
		original_object_dict = _posted_dict('message')

	# Fill in placeholder
	original_endpoint = endpoint
	endpoint = _fill_placeholder_in_endpoint(original_endpoint, object_type,
											use_posted=True)

	patch = flask_client.patch

	if not data:
		data = {}

	try:
		result = patch(endpoint, json=data)
		assert result.status == "200 OK"
		assert result.json['id'] == original_object_dict['id']
		assert result.json != original_object_dict
		for key in data.keys():
			assert result.json[key] == data[key]
	except AssertionError as e:
		print("Filled endpoint: " + endpoint)
		print("Returned data:\n" + str(result.json))
		raise e

	# Then, perform the usual checks, such as 404, wrong object type, etc.
	_endpoint_sanity_checks(original_endpoint, 'PATCH', patch, object_type)

def endpoint_report(flask_client, endpoint, object_type):
	"""
	Performs tests on a report endpoint.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - endpoint (required) - the endpoint to test
	  - object_type - dict containing one key and value: the key is the
	                  placeholder string, the value is the object type.
	                  If the endpoint accepts any object type, the object
	                  type must be set to None.
	"""
	print("  * Testing: (REPORT) POST " + endpoint)

	report = flask_client.post

	# Fill in placeholder
	original_endpoint = endpoint
	endpoint = _fill_placeholder_in_endpoint(original_endpoint, object_type,
											use_posted=True)

	# Get report dict
	data = _pregenerated_dict('report')

	# Perform the action
	result = report(endpoint, json=data)
	try:
		assert result.status == "201 CREATED"
		assert result.json['id'] != data['id']
		assert result.json['object_type'] == 'report'
	except AssertionError as e:
		print("Filled endpoint: " + endpoint)
		print("Returned data:\n" + str(result.json))
		raise e

	# Then, perform the usual checks, such as 404, wrong object type, etc.
	_endpoint_sanity_checks(original_endpoint, 'POST', report, object_type)

def endpoint_delete(flask_client, endpoint, object_type=None):
	"""
	Performs tests on a DELETE endpoint.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - endpoint (required) - the endpoint to test
	  - object_type - dict containing one key and value: the key is the
	                  placeholder string, the value is the object type.
	                  If the endpoint accepts any object type, the object
	                  type must be set to None.
	"""
	print("  * Testing: DELETE " + endpoint)

	delete = flask_client.delete

	# Fill in placeholder
	original_endpoint = endpoint
	endpoint = _fill_placeholder_in_endpoint(original_endpoint, object_type,
											use_posted=True)

	# Get deleted object ID
	_object_type = list(object_type.values())[0]
	if _object_type:
		target_id = _posted_id(_object_type)
	else:
		target_id = _posted_id('message')

	# First, test the endpoint in question:
	result = delete(endpoint)
	try:
		assert result.status == "200 OK"
	except AssertionError as e:
		print("Filled endpoint: " + endpoint)
		print("Returned data:\n" + str(result.json))
		raise e

	assert flask_client.get('/api/v1/id/' + target_id).status == "404 NOT FOUND"

	if _object_type:
		del PostedObjectDicts.items[_object_type]
	else:
		del PostedObjectDicts.items['message']

	# Then, perform the usual checks, such as 404, wrong object type, etc.
	_endpoint_sanity_checks(original_endpoint, 'DELETE', delete, object_type)

#
# Conference children test callers
#

def endpoint_conference_child(flask_client, method, endpoint, object_type, data=None):
	"""
	Performs tests on conference child endpoints.

	Arguments:
	  - flask_client (required) - provided by the client pytest fixture
	  - method (required) - the method to test
	  - endpoint (required) - the endpoint to test
	  - object_type - dict containing one key and value: the key is the
	                  placeholder string, the value is the object type.
	                  If the endpoint accepts any object type, the object
	                  type must be set to None.
	  - data - data for PATCH request
	"""
	if method == 'GET':
		action = flask_client.get
	elif method == 'POST' or method == 'REPORT':
		action = flask_client.post
	elif method == 'PATCH':
		action = flask_client.patch
	elif method == 'DELETE':
		action = flask_client.delete

	# First, replace the <conference_id> placeholder with the actual conference
	# The conference is created with a POST call prior to the start of these
	# tests, so we get the conference ID from posted objects
	conference_id = _posted_id('conference')
	original_endpoint = endpoint
	final_endpoint = original_endpoint.replace('<conference_id>', conference_id)
	# This will be the endpoint we send off to the final test function.

	if method != 'POST':
		# Test fake conference ID
		_placeholder = list(object_type.keys())[0]
		_object_type = list(object_type.values())[0]
		if _object_type:
			target_id = _posted_id(_object_type)
		else:
			target_id = _posted_id('message')
		fake_conference_endpoint = original_endpoint.replace('<conference_id>', 'fakeid')
		fake_conference_endpoint = fake_conference_endpoint.replace(_placeholder, target_id)
		fake_conference_action = action(fake_conference_endpoint)
		assert fake_conference_action.status == "404 NOT FOUND"

		# Test object belonging to another conference
		if _object_type:
			target_id = _pregenerated_id(_object_type)
		else:
			target_id = _pregenerated_id('message')
		wrong_parent_endpoint = final_endpoint.replace(_placeholder, target_id)
		assert action(wrong_parent_endpoint).status == "400 BAD REQUEST"

	# Call the actual test function
	if method == 'GET':
		endpoint_get(flask_client, final_endpoint, object_type, use_posted=True)
	elif method == 'POST':
		endpoint_post(flask_client, final_endpoint, object_type)
	elif method == 'PATCH':
		endpoint_patch(flask_client, final_endpoint, object_type, data)
	elif method == 'REPORT':
		endpoint_report(flask_client, final_endpoint, object_type)
	elif method == 'DELETE':
		endpoint_delete(flask_client, final_endpoint, object_type)

#
# pytest tests
#

def test_special_endpoints(client):
	"""Test /api/v1/instance and /api/v1/stash/request."""
	# /api/v1/instance
	print("  * Testing: GET /api/v1/instance")
	instance_result = client.get('/api/v1/instance')
	assert instance_result.status == "200 OK"
	assert instance_result.json == drywall.db.get_object_as_dict_by_id('0')

	# /api/v1/stash/request
	print("  * Testing: POST /api/v1/stash/request")
	stash_data = {"id_list": [_pregenerated_id('account'), _pregenerated_id('message')]}
	stash_result = client.post('/api/v1/stash/request', json=stash_data)
	assert stash_result.status == "200 OK"
	assert stash_result.json == {
		"type": "stash",
		"id_list": [_pregenerated_id('account'), _pregenerated_id('message')],
		_pregenerated_id('account'): _pregenerated_dict('account'),
		_pregenerated_id('message'): _pregenerated_dict('message')
	}

def test_api_id(client):
	"""Test API endpoints related to objects and IDs."""
	endpoint_post(client, '/api/v1/id', None)
	endpoint_get(client, '/api/v1/id/<id>', {'<id>': None})
	endpoint_patch(client, '/api/v1/id/<id>', {'<id>': None}, {"content": "new_content"})
	endpoint_report(client, '/api/v1/id/<id>/report', {'<id>': None})
	endpoint_delete(client, '/api/v1/id/<id>', {'<id>': None})

def test_api_accounts(client):
	"""Test API endpoints related to accounts."""
	endpoint_post(client, '/api/v1/accounts', 'account')
	endpoint_get(client, '/api/v1/accounts/<account_id>', {"<account_id>": "account"})
	endpoint_patch(client, '/api/v1/accounts/<account_id>', {"<account_id>": "account"}, {"bio": "new_bio"})
	endpoint_report(client, '/api/v1/accounts/<account_id>/report', {"<account_id>": "account"})
	endpoint_delete(client, '/api/v1/accounts/<account_id>', {"<account_id>": "account"})

def test_api_conferences(client):
	"""Test API endpoints related to conferences."""
	endpoint_post(client, '/api/v1/conferences', 'conference')
	endpoint_get(client, '/api/v1/conferences/<conference_id>', {"<conference_id>": "conference"})
	endpoint_patch(client, '/api/v1/conferences/<conference_id>', {"<conference_id>": "conference"}, {"name": "new_name"})
	endpoint_report(client, '/api/v1/conferences/<conference_id>/report', {"<conference_id>": "conference"})
	endpoint_delete(client, '/api/v1/conferences/<conference_id>', {"<conference_id>": "conference"})

def test_api_conferences_children(client):
	"""Test API endpoints related to conference children."""
	# Recreate conference for conference child tests
	endpoint_post(client, '/api/v1/conferences', 'conference')

	# Conference members
	endpoint_conference_child(client, 'POST', '/api/v1/conferences/<conference_id>/members',
							object_type="conference_member")
	endpoint_conference_child(client, 'GET', '/api/v1/conferences/<conference_id>/members/<member_id>',
							object_type={"<member_id>": "conference_member"})
	endpoint_conference_child(client, 'PATCH', '/api/v1/conferences/<conference_id>/members/<member_id>',
							object_type={"<member_id>": "conference_member"},
							data={"nickname": "new_nickname"})
	endpoint_conference_child(client, 'REPORT', '/api/v1/conferences/<conference_id>/members/<member_id>/report',
							object_type={"<member_id>": "conference_member"})
	endpoint_conference_child(client, 'DELETE', '/api/v1/conferences/<conference_id>/members/<member_id>',
							object_type={"<member_id>": "conference_member"})

	# Conference channels
	endpoint_conference_child(client, 'POST', '/api/v1/conferences/<conference_id>/channels',
							object_type="channel")
	endpoint_conference_child(client, 'GET', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
							object_type={"<channel_id>": "channel"})
	endpoint_conference_child(client, 'PATCH', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
							object_type={"<channel_id>": "channel"},
							data={"name": "new_name"})
	endpoint_conference_child(client, 'REPORT', '/api/v1/conferences/<conference_id>/channels/<channel_id>/report',
							object_type={"<channel_id>": "channel"})
	endpoint_conference_child(client, 'DELETE', '/api/v1/conferences/<conference_id>/channels/<channel_id>',
							object_type={"<channel_id>": "channel"})

	# Conference invites
	endpoint_conference_child(client, 'POST', '/api/v1/conferences/<conference_id>/invites',
							object_type="invite")
	endpoint_conference_child(client, 'GET', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
							object_type={"<invite_id>": "invite"})
	endpoint_conference_child(client, 'PATCH', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
							object_type={"<invite_id>": "invite"},
							data={"code": "new_code"})
	endpoint_conference_child(client, 'REPORT', '/api/v1/conferences/<conference_id>/invites/<invite_id>/report',
							object_type={"<invite_id>": "invite"})
	endpoint_conference_child(client, 'DELETE', '/api/v1/conferences/<conference_id>/invites/<invite_id>',
							object_type={"<invite_id>": "invite"})

	# Conference roles
	endpoint_conference_child(client, 'POST', '/api/v1/conferences/<conference_id>/roles',
							object_type="role")
	endpoint_conference_child(client, 'GET', '/api/v1/conferences/<conference_id>/roles/<role_id>',
							object_type={"<role_id>": "role"})
	endpoint_conference_child(client, 'PATCH', '/api/v1/conferences/<conference_id>/roles/<role_id>',
							object_type={"<role_id>": "role"},
							data={"name": "new_name"})
	endpoint_conference_child(client, 'REPORT', '/api/v1/conferences/<conference_id>/roles/<role_id>/report',
							object_type={"<role_id>": "role"})
	endpoint_conference_child(client, 'DELETE', '/api/v1/conferences/<conference_id>/roles/<role_id>',
							object_type={"<role_id>": "role"})

	# Delete the conference
	endpoint_delete(client, '/api/v1/conferences/<conference_id>', {"<conference_id>": "conference"})

def test_api_channels(client):
	"""Test API endpoints related to channels."""
	endpoint_post(client, '/api/v1/channels', 'channel')
	endpoint_get(client, '/api/v1/channels/<channel_id>', {"<channel_id>": "channel"})
	endpoint_patch(client, '/api/v1/channels/<channel_id>', {"<channel_id>": "channel"}, {"name": "new_name"})
	endpoint_report(client, '/api/v1/channels/<channel_id>/report', {"<channel_id>": "channel"})
	endpoint_delete(client, '/api/v1/channels/<channel_id>', {"<channel_id>": "channel"})

def test_api_messages(client):
	"""Test API endpoints related to messages."""
	endpoint_post(client, '/api/v1/messages', 'message')
	endpoint_get(client, '/api/v1/messages/<message_id>', {"<message_id>": "message"})
	endpoint_patch(client, '/api/v1/messages/<message_id>', {"<message_id>": "message"}, {"content": "new_content"})
	endpoint_report(client, '/api/v1/messages/<message_id>/report', {"<message_id>": "message"})
	endpoint_delete(client, '/api/v1/messages/<message_id>', {"<message_id>": "message"})

def test_api_invites(client):
	"""Test API endpoints related to invites."""
	endpoint_post(client, '/api/v1/invites', 'invite')
	endpoint_get(client, '/api/v1/invites/<invite_id>', {"<invite_id>": "invite"})
	endpoint_patch(client, '/api/v1/invites/<invite_id>', {"<invite_id>": "invite"}, {"code": "new_code"})
	endpoint_report(client, '/api/v1/invites/<invite_id>/report', {"<invite_id>": "invite"})
	endpoint_delete(client, '/api/v1/invites/<invite_id>', {"<invite_id>": "invite"})

def test_api_roles(client):
	"""Test API endpoints related to roles."""
	endpoint_post(client, '/api/v1/roles', 'role')
	endpoint_get(client, '/api/v1/roles/<role_id>', {"<role_id>": "role"})
	endpoint_patch(client, '/api/v1/roles/<role_id>', {"<role_id>": "role"}, {"name": "new_name"})
	endpoint_report(client, '/api/v1/roles/<role_id>/report', {"<role_id>": "role"})
	endpoint_delete(client, '/api/v1/roles/<role_id>', {"<role_id>": "role"})

def test_api_reports(client):
	"""Test API endpoints related to reports."""
	endpoint_post(client, '/api/v1/reports', 'report')
	endpoint_get(client, '/api/v1/reports/<report_id>', {"<report_id>": "report"})
	endpoint_patch(client, '/api/v1/reports/<report_id>', {"<report_id>": "report"}, {"note": "new_note"})
	endpoint_delete(client, '/api/v1/reports/<report_id>', {"<report_id>": "report"})
