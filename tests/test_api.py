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

@pytest.fixture
def pregenerate_objects():
	"""
	Uses the generate_objects function to generate some objects. Returns
	the results of said command.
	"""
	return generate_objects()

def test_api_id(pregenerate_objects, client):
	"""Test the ID-related APIs."""
	pregenerated_object_dict = pregenerate_objects[0]
	pregenerated_object_ids = pregenerate_objects[1]

	# GET /api/v1/instance
	assert client.get('/api/v1/instance').status == "200 OK"

	# GET /api/v1/id/<id>
	account_get = client.get('/api/v1/id/' + pregenerated_object_ids['account'])
	assert account_get.status == "200 OK"
	assert account_get.get_json() == pregenerated_object_dict['account']

	# PATCH /api/v1/id/<id>
	message_patch_dict = {"content": "customcontent"}
	message_patch = client.patch('/api/v1/id/' + pregenerated_object_ids['message'], json=message_patch_dict)
	message_get = client.get('/api/v1/id/' + pregenerated_object_ids['message'])
	assert message_patch.status == "200 OK"
	assert message_get.get_json() != pregenerated_object_dict['message']
	assert message_get.get_json()['content'] == "customcontent"

	# POST /api/v1/id
	message_json = pregenerated_object_dict['message']
	object_post = client.post('/api/v1/id', json=message_json)
	object_post_json = object_post.get_json()
	assert object_post.status == "200 OK"
	assert 'error' not in object_post_json
	assert object_post_json['id'] != pregenerated_object_dict['message']['id']
	assert object_post_json['type'] == "object"
	assert object_post_json['object_type'] == "message"

	# GET /api/v1/id/<id>/type
	attachment_get = client.get('/api/v1/id/' + pregenerated_object_ids['attachment'] + '/type')
	attachment_json = attachment_get.get_json()
	assert attachment_get.status == "200 OK"
	assert "quoted_message" not in attachment_json
	assert "id" in attachment_json
	assert "type" in attachment_json
	assert "object_type" in attachment_json
	assert "attachment_type" in attachment_json

	# GET /api/v1/stash/request
	object_ids = list()
	for object_id in pregenerated_object_ids.values():
		object_ids.append(object_id)
	stash_request = {"id_list": object_ids}
	stash_get = client.get('/api/v1/stash/request', json=stash_request)
	stash_json = stash_get.get_json()
	assert stash_get
	for object_id in object_ids:
		assert object_id in stash_json

def test_api_accounts(pregenerate_objects, client):
	"""Tests account-related APIs."""
	pregenerated_object_dict = pregenerate_objects[0]
	pregenerated_object_ids = pregenerate_objects[1]
	account_id = pregenerated_object_ids['account']
	account_name = pregenerated_object_dict['account']['username']

	# GET /api/v1/accounts/<id>
	assert client.get('/api/v1/accounts/' + account_id).status == "200 OK"
	assert client.get('/api/v1/accounts/' + pregenerated_object_ids['message']).status == "400 BAD REQUEST"

	# TODO: POST /api/v1/accounts/<bot_id>/invite
	# This function is not correctly implemented yet, and does not return
	# anything if everything goes right.

	# GET /api/v1/accounts/by-name/<name>
	assert client.get('/api/v1/accounts/by-name/' + account_name).status == "200 OK"

	# PATCH /api/v1/accounts/by-name/<name>
	account_patch = client.patch('/api/v1/accounts/by-name/' + account_name, json={"bio": "custombio"})
	account_json = account_patch.get_json()
	assert account_patch.status == "200 OK"
	assert account_json['bio'] == "custombio"
