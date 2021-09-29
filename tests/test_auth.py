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
	username = str(time.time())
	email = str(time.time()) + "@example.com"
	password = "testUser"

	# Create the user
	user_dict = auth.register_user(username, email, password)
	return [user_dict['id'], password, user_dict]

def generate_clients():
	"""
	Creates two clients for testing purposes: an user app and a bot.

	Returns a dict with two items:
		- app: list where [0] is the ID and [1] is the dict
		- bot: list where [0] is the ID, [1] is the dict and [2] is
			   the account ID
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
	clients['app'] = auth_oauth.create_client(app_dict)

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
	clients['bot'] = auth_oauth.create_client(bot_dict)

	return clients

def test_auth_accounts():
	"""
	Test account functions: creating new accounts, editing account
	information, etc.
	"""
	# Call the usual generate_user function
	_user = generate_user()

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
