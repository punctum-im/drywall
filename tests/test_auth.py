# coding: utf-8
"""
Contains tests and helper functions for basic authentication functions:
creating/editing/deleting accounts and OAuth clients.
"""
from drywall import auth
from drywall import auth_oauth
from drywall import db

import time

def generate_user():
	"""
	Creates a user and returns a list with its ID, password and
	a dict containing the values of the resulting User object.
	"""
	# Generate a random username, e-mail, password
	username = str(time.time()).replace('.', '')
	email = str(time.time()) + "@example.com"
	password = "testUser"

	# Create the user
	user_dict = auth.register_user(username, email, password)
	return [user_dict['id'], password, user_dict]

def generate_clients():
	"""
	Creates two clients for testing purposes: an user app and a bot.

	Returns a dict with two items:
		- app: dict containing values for a client with userapp type
		- bot: dict containing values for a client with userapp type
		- owner: User object that owns the clients
	"""
	clients = {}

	# Generate the owner
	clients['owner'] = generate_user()[2]

	# Create the user app
	app_dict = {
		"name": "TestUserApp",
		"description": "This is my test application!",
		"type": "userapp",
		"uri": "https://punctum.im/callback",
		"scopes": ["account:read", "account:write"],
		"owner_id": clients['owner']['id'],
		"owner_account_id": clients['owner']['account_id']
	}
	app = auth_oauth.create_client(app_dict)
	clients['app'] = app

	# Create the bot
	bot_dict = {
		"name": "TestBot",
		"description": "This is my test bot!",
		"type": "bot",
		"uri": "https://punctum.im/callback",
		"scopes": ["channel:read", "channel:write"],
		"owner_id": clients['owner']['id'],
		"owner_account_id": clients['owner']['account_id']
	}
	bot = auth_oauth.create_client(bot_dict)
	clients['bot'] = bot

	return clients

def test_auth_users():
	"""
	Test user functions: creating new users, editing user information, etc.
	"""
	# Call the usual generate_user function
	_user = generate_user()
	_user_id = _user[0]
	_user_dict = _user[2]
	_user_account_id = _user_dict['account_id']

	# Check if the generated user actually exists
	assert auth.get_user_by_id(_user_id) is not None
	assert db.get_object_as_dict_by_id(_user_account_id) is not None

	# Check if the user can be found using builtin functions
	assert auth.get_user_by_email(_user_dict['email']) == _user_dict
	assert auth.get_user_by_account_id(_user_account_id) == _user_dict

	# Make sure the newly-created user isn't an admin
	assert auth.is_account_admin(_user_account_id) is False

	# Try to edit user
	new_user_dict = _user[2].copy()
	new_user_dict['username'] = 'NewTestUsername'
	new_user_dict['email'] = 'newtestemail@example.com'
	edited_user_dict = auth.edit_user(_user_id, new_user_dict)

	assert edited_user_dict is not None
	assert edited_user_dict != _user_dict
	edited_user = auth.get_user_by_id(_user_id)
	assert edited_user is not None
	assert edited_user['username'] == 'NewTestUsername'
	assert edited_user['email'] == 'newtestemail@example.com'

	# User editing failcases
	new_user_dict['email'] = 'broken email'
	try:
		auth.edit_user(_user_id, new_user_dict)
	except ValueError:
		pass
	else:
		raise Exception("edit_user didn't raise an error with broken e-mail!")

	# Try to delete user
	# auth.remove_user(_user_id)
	# assert auth.get_user_by_id(_user_id) is None

def test_auth_accounts_web():
	"""
	Test web authentication pages: signing up, logging in and
	logging out.
	"""
	pass

def test_oauth_clients():
	"""Test client creation, editing, deletion, etc."""
	# Call the usual generate_clients function
	_clients = generate_clients()

	_app_dict = _clients["app"]
	_app_id = _app_dict['client_id']

	_bot_dict = _clients["bot"]
	_bot_id = _bot_dict['client_id']
	_bot_account_id = _bot_dict['bot_account_id']

	_owner_user_id = _clients['owner']['id']

	# Make sure the created clients are available in get_clients_owned_by_user
	owned_clients = auth_oauth.get_clients_owned_by_user(_owner_user_id)
	assert _app_dict in owned_clients
	assert _bot_dict in owned_clients

	# Try to update client
	update_dict = {"name": "NewTestClient", "scopes": ["account:read", "channel:write"]}
	edit_result = auth_oauth.edit_client(_bot_id, update_dict)
	assert edit_result != _bot_dict
	assert auth_oauth.get_client_by_id(_bot_id)['client_metadata']['client_name'] == 'NewTestClient'
	assert auth_oauth.get_client_by_id(_bot_id)['client_metadata']['scope'] == "account:read channel:write"
	assert db.get_object_as_dict_by_id(_bot_account_id)['username'] == 'NewTestClient'

	# Try to create/edit bot with invalid name
	try:
		bot_dict = {
			"name": "$.invalid.bot.name$",
			"type": "bot",
			"uri": "https://punctum.im/callback",
			"scopes": ["channel:read", "channel:write"],
			"owner_id": _clients['owner']['id'],
			"owner_account_id": _clients['owner']['account_id']
		}
		auth_oauth.create_client(bot_dict)
		auth_oauth.edit_client(_bot_id, {"name": "$.invalid.bot.name$"})
	except ValueError:
		pass
	else:
		raise Exception("Invalid bot name test failed!")

	# Test some fail cases
	assert auth_oauth.get_client_by_id('fakeid') is None
	assert auth_oauth.edit_client('fakeid', {"name": "FakeTestClient"}) is None
	assert auth_oauth.remove_client('fakeid') is None

	# Generate custom user for further tests
	_new_user_id = generate_user()[0]

	# Make sure user has no pre-owned clients or assigned tokens
	assert not auth_oauth.get_clients_owned_by_user(_new_user_id)
	assert not auth_oauth.get_auth_tokens_for_user(_new_user_id)

	# Test access permissions
	assert auth_oauth.get_client_if_owned_by_user(_new_user_id, 'fakeid') is None
	assert auth_oauth.get_client_if_owned_by_user(_new_user_id, _bot_id) is False
	assert auth_oauth.get_client_if_owned_by_user(_owner_user_id, _bot_id) is not False

	# Clean up
	# auth.remove_user(_new_user_id)

	# Try to remove clients
	auth_oauth.remove_client(_app_id)
	assert auth_oauth.get_client_by_id(_app_id) is None
	auth_oauth.remove_client(_bot_id)
	assert auth_oauth.get_client_by_id(_bot_id) is None
