#!/usr/bin/env python3
# coding: utf-8
"""
Tests for the API.
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

class PregeneratedObjects:
	"""Contains pregenerated objects and their IDs."""
	pregenerated_objects = generate_objects()
	dicts = pregenerated_objects[0]
	ids = pregenerated_objects[1]

def test_api_id(client):
	"""Test the ID-related APIs."""

	# GET /api/v1/instance
	assert client.get('/api/v1/instance').status == "200 OK"

	# GET /api/v1/id/<id>
	account_get = client.get('/api/v1/id/' + PregeneratedObjects.ids['account'])
	assert account_get.status == "200 OK"
	assert account_get.get_json() == PregeneratedObjects.dicts['account']
	nonexistent_get = client.get('/api/v1/id/fakeid')
	assert nonexistent_get.status == "404 NOT FOUND"

	# PATCH /api/v1/id/<id>
	message_patch_dict = {"content": "customcontent"}
	message_patch = client.patch('/api/v1/id/' + PregeneratedObjects.ids['message'], json=message_patch_dict)
	message_get = client.get('/api/v1/id/' + PregeneratedObjects.ids['message'])
	assert message_patch.status == "200 OK"
	assert message_get.get_json() != PregeneratedObjects.dicts['message']
	assert message_get.get_json()['content'] == "customcontent"
	nonexistent_patch = client.patch('/api/v1/id/fakeid', json=message_patch_dict)
	assert nonexistent_patch.status == "404 NOT FOUND"
	patch_with_no_json = client.patch('/api/v1/id/' + PregeneratedObjects.ids['message'])
	assert patch_with_no_json.status == "400 BAD REQUEST"

	# POST /api/v1/id
	message_json = PregeneratedObjects.dicts['message']
	object_post = client.post('/api/v1/id', json=message_json)
	object_post_json = object_post.get_json()
	assert object_post.status == "200 OK"
	assert 'error' not in object_post_json
	assert object_post_json['id'] != PregeneratedObjects.dicts['message']['id']
	assert object_post_json['type'] == "object"
	assert object_post_json['object_type'] == "message"
	object_post_no_json = client.post('/api/v1/id')
	assert object_post_no_json.status == "400 BAD REQUEST"

	# GET /api/v1/id/<id>/type
	attachment_get = client.get('/api/v1/id/' + PregeneratedObjects.ids['attachment'] + '/type')
	attachment_json = attachment_get.get_json()
	assert attachment_get.status == "200 OK"
	assert "quoted_message" not in attachment_json
	assert "id" in attachment_json
	assert "type" in attachment_json
	assert "object_type" in attachment_json
	assert "attachment_type" in attachment_json
	nonexistent_type_get = client.get('/api/v1/id/fakeid/type')
	assert nonexistent_type_get.status == "404 NOT FOUND"

	# GET /api/v1/stash/request
	object_ids = list()
	for object_id in PregeneratedObjects.ids.values():
		object_ids.append(object_id)
	stash_request = {"id_list": object_ids}
	stash_get = client.get('/api/v1/stash/request', json=stash_request)
	stash_json = stash_get.get_json()
	assert stash_get
	for object_id in object_ids:
		assert object_id in stash_json
	stash_get_no_json = client.get('/api/v1/stash/request')
	assert stash_get_no_json.status == "400 BAD REQUEST"

def test_api_accounts(client):
	"""Tests account-related APIs."""
	account_id = PregeneratedObjects.ids['account']
	account_name = PregeneratedObjects.dicts['account']['username']
	account_dict = PregeneratedObjects.dicts['account']

	# GET /api/v1/accounts/<id>
	assert client.get('/api/v1/accounts/' + account_id).status == "200 OK"
	assert client.get('/api/v1/accounts/' + account_id).get_json() == account_dict
	assert client.get('/api/v1/accounts/' + PregeneratedObjects.ids['message']).status == "400 BAD REQUEST"
	assert client.get('/api/v1/accounts/fakeid').status == "404 NOT FOUND"

	# PATCH /api/v1/accounts/<id>
	account_id_patch = client.patch('/api/v1/accounts/' + account_id, json={"bio": "custombio"})
	account_id_patch_json = account_id_patch.get_json()
	account_patch_dict_target = {}
	for key, value in account_dict.items():
		account_patch_dict_target[key] = value
	account_patch_dict_target['bio'] = "custombio"
	assert account_id_patch.status == "200 OK"
	assert account_id_patch_json == account_patch_dict_target
	assert client.patch('/api/v1/accounts/' + PregeneratedObjects.ids['message'], json={"bio": "custombio"}).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/accounts/' + account_id).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/accounts/fakeid').status == "404 NOT FOUND"

	# TODO: POST /api/v1/accounts/<bot_id>/invite
	# This function is not correctly implemented yet, and does not return
	# anything if everything goes right.

	# GET /api/v1/accounts/by-name/<name>
	account_name_get = client.get('/api/v1/accounts/by-name/' + account_name)
	assert account_name_get.status == "200 OK"
	assert account_name_get.get_json() == account_patch_dict_target
	assert client.get('/api/v1/accounts/by-name/fakename').status == "404 NOT FOUND"

	# PATCH /api/v1/accounts/by-name/<name>
	account_patch = client.patch('/api/v1/accounts/by-name/' + account_name, json={"bio": "custombio2"})
	account_json = account_patch.get_json()
	account_patch_dict_target['bio'] = "custombio2"
	assert account_patch.status == "200 OK"
	assert account_patch.get_json() == account_patch_dict_target
	account_patch_fake_name = client.patch('/api/v1/account/by-name/fakename', json={"bio": "custombio2"})
	assert account_patch_fake_name.status == "404 NOT FOUND"
	account_patch_no_json = client.patch('/api/v1/accounts/by-name/' + account_name)
	assert account_patch_no_json.status == "400 BAD REQUEST"

def test_api_messages(client):
	"""Tests message-related APIs."""
	message_id = PregeneratedObjects.ids['message']
	message_dict = PregeneratedObjects.dicts['message']
	message_dict['content'] = "customcontent"

	# GET /api/v1/messages/<id>
	message_get = client.get('/api/v1/messages/' + message_id)
	assert message_get.get_json() == message_dict
	assert message_get.status == "200 OK"
	assert client.get('/api/v1/messages/' + PregeneratedObjects.ids['account']).status == "400 BAD REQUEST"
	assert client.get('/api/v1/messages/fakeid').status == "404 NOT FOUND"

	# PATCH /api/v1/messages/<id>
	message_id_patch = client.patch('/api/v1/messages/' + message_id, json={"content": "customcontent2"})
	message_id_patch_json = message_id_patch.get_json()
	assert message_id_patch.status == "200 OK"
	message_patch_dict_target = {}
	for key, value in message_dict.items():
		message_patch_dict_target[key] = value
	message_patch_dict_target['content'] = "customcontent2"
	assert message_id_patch_json == message_patch_dict_target
	assert client.patch('/api/v1/messages/' + PregeneratedObjects.ids['account'], json={"content": "customcontent2"}).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/messages/' + message_id).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/messages/fakeid').status == "404 NOT FOUND"

	# POST /api/v1/messages
	message_post = client.post('/api/v1/messages', json=message_dict)
	assert message_post.status == "200 OK"
	message_post_id = message_post.get_json()['id']
	message_post_target_dict = message_post.get_json()
	message_post_target_dict['id'] = message_post_id
	assert message_post.get_json() == message_post_target_dict

def test_api_conferences(client):
	"""Tests conference-related APIs."""
	conference_id = PregeneratedObjects.ids['conference']
	conference_dict = PregeneratedObjects.dicts['conference']

	# GET /api/v1/conferences/<id>
	conference_get = client.get('/api/v1/conferences/' + conference_id)
	assert conference_get.get_json() == conference_dict
	assert conference_get.status == "200 OK"
	assert client.get('/api/v1/conferences/' + PregeneratedObjects.ids['account']).status == "400 BAD REQUEST"
	assert client.get('/api/v1/conferences/fakeid').status == "404 NOT FOUND"

	# PATCH /api/v1/conferences/<id>
	conference_id_patch = client.patch('/api/v1/conferences/' + conference_id, json={"name": "customname"})
	conference_id_patch_json = conference_id_patch.get_json()
	assert conference_id_patch.status == "200 OK"
	conference_patch_dict_target = {}
	for key, value in conference_dict.items():
		conference_patch_dict_target[key] = value
	conference_patch_dict_target['name'] = "customname"
	assert conference_id_patch_json == conference_patch_dict_target
	assert client.patch('/api/v1/conferences/' + PregeneratedObjects.ids['account'], json={"name": "customname"}).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/conferences/' + conference_id).status == "400 BAD REQUEST"
	assert client.patch('/api/v1/conferences/fakeid').status == "404 NOT FOUND"

	# POST /api/v1/conferences
	conference_post = client.post('/api/v1/conferences', json=conference_dict)
	assert conference_post.status == "200 OK"
	conference_post_id = conference_post.get_json()['id']
	conference_post_target_dict = conference_post.get_json()
	conference_post_target_dict['id'] = conference_post_id
	assert conference_post.get_json() == conference_post_target_dict

