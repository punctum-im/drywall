# coding: utf-8
"""
Contains the necessary Authlib setup bits for OAuth2.

This code is, admittedly, a huge mess. If you're familiar with Authlib,
feel free to send a MR with cleanups where you deem necessary.
"""
from drywall.auth_models import User, Client, Token, AuthorizationCode
from drywall.auth import current_user, username_valid
from drywall import app
from drywall import db
from drywall import objects
# FIXME: temporary until authlib 1.0 is released
from drywall.auth_models import list_to_scope

from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc7009 import RevocationEndpoint
from authlib.oauth2.rfc7636 import CodeChallenge
from flask import render_template, redirect, url_for
import flask
from secrets import token_urlsafe
from sqlalchemy.orm import Session
import time
from uuid import uuid4

# Client-related functions

def get_clients_owned_by_user(owner_id):
	"""
	Returns a list of Client dicts owned by the user with the provided ID.

	Returns None if none are found.
	"""
	clients = []
	with Session(db.engine) as db_session:
		query = db_session.query(Client).\
				filter(Client.owner_id == owner_id).all() # noqa: ET126
		if not query:
			return []
		for client in query:
			clients.append(client.to_dict())
		return clients

def get_auth_tokens_for_user(user_id):
	"""
	Returns a list of AuthorizationCode objects which act on behalf of
	the user with the provided ID.

	Returns None if none are found.
	"""
	tokens = []
	with Session(db.engine) as db_session:
		query = db_session.query(AuthorizationCode).\
				filter(AuthorizationCode.user_id == user_id).all() # noqa: ET126
		if not query:
			return []
		for token in query:
			tokens.append(token)
		return tokens

def get_client_by_id(client_id):
	"""
	Returns a dict from a Client object with the provided ID.

	Returns None if a client with the given ID is not found.
	"""
	with Session(db.engine) as db_session:
		client = db_session.query(Client).get(client_id)
		if not client:
			return None
		return client.to_dict()

def get_client_if_owned_by_user(user_id, client_id):
	"""
	Returns a dict from a Client object if the user with the provided ID
	is its owner.

	Returns False if the client is not owned by the user.
	Returns None if a client with the given ID is not found.
	"""
	client = get_client_by_id(client_id)
	if not client:
		return None
	if not client['owner_id'] == user_id:
		return False
	return client

def create_client(client_dict):
	"""
	Creates a new client from the provided client dict, which contains
	the following variables:

	- name (string) - contains the name of the client.
	- description (string) - contains the description.
	- type (string) - 'userapp' or 'bot'
	- uri  (string) - contains URI
	- scopes (list) - list of chosen scopes
	- owner_id (id) - user ID of the creator
	- owner_account_id (id) - account ID of the creator

	This automatically creates an account in case of a bot account, and
	adds the resulting client to the database.

	Returns the created client.
	"""
	if 'description' not in client_dict.keys():
		client_dict['description'] = ""

	with Session(db.engine) as db_session:
		client = Client(
			client_id=str(uuid4()),
			client_id_issued_at=int(time.time()),
			client_type=client_dict['type'],
			owner_id=client_dict['owner_id']
		)

		client_metadata = {
			"client_name": client_dict['name'],
			"client_description": client_dict['description'],
			"client_uri": client_dict['uri'],
			"scope": list_to_scope(client_dict['scopes'])
		}
		client.set_client_metadata(client_metadata)

		client.client_secret = token_urlsafe(32)

		if client_dict['type'] == 'bot':
			if not username_valid(client_dict['name']):
				raise ValueError('Invalid username for bot account!')
			account_dict = {
				"object_type": "account",
				"username": client_dict['name'],
				"bot": True,
				"bot_owner": client_dict['owner_account_id']
			}
			account_object = objects.make_object_from_dict(account_dict)
			db.add_object(account_object)
			client.bot_account_id = vars(account_object)['id']

		db_session.add(client)
		db_session.commit()
		return client.to_dict()

def edit_client(client_id, client_dict):
	"""
	Updates the client in the database with the provided variables.

	Returns the updated client as a dict.
	"""
	with Session(db.engine) as db_session:
		client = db_session.query(Client).get(client_id)
		if not client:
			return None

		client_metadata = client.client_metadata.copy()
		for val in ['name', 'description', 'uri', 'scopes']:
			if val in client_dict:
				if val == 'scopes':
					client_metadata["scope"] = list_to_scope(client_dict['scopes'])
				else:
					client_metadata["client_" + val] = client_dict[val]
		client.set_client_metadata(client_metadata)

		if client.client_type == 'bot' and 'name' in client_dict:
			account_id = client.bot_account_id
			account = db.get_object_as_dict_by_id(account_id)
			if account['username'] != client_dict['name']:
				if not username_valid(client_dict['name']):
					raise ValueError('Invalid username for bot account!')
				account['username'] = client_dict['name']
				account_object = objects.make_object_from_dict(account, extend=account_id)
				db.push_object(account_id, account_object)

		db_session.commit()
		# FIXME: This should return client.to_dict() but that doesn't update
		#        client_metadata for some reason.
		return get_client_by_id(client_id)

def remove_client(client_id):
	"""
	Removes a client by ID. Returns the deleted client's ID.
	"""
	with Session(db.engine) as db_session:
		client = db_session.query(Client).get(client_id)
		if not client:
			return None
		db_session.delete(client)
		db_session.commit()
	return client_id

#
# -*-*- AuthLib stuff starts here -*-*-
#

# Helper functions

def query_client(client_id):
	"""Gets a Client object by ID. Returns None if not found."""
	with Session(db.engine) as db_session:
		return db_session.query(Client).filter_by(client_id=client_id).first()

def save_token(token_data, request):
	"""Saves a token to the database."""
	if request.user:
		user_id = request.user.get_user_id()
		account_id = request.user.account_id
	else:
		user_id = request.client.user_id
		user_id = request.client.account_id
	with Session(db.engine) as db_session:
		token = Token(
			client_id=request.client.client_id,
			user_id=user_id,
			account_id=account_id,
			**token_data
		)
		db_session.add(token)
		db_session.commit()


# Initialize the authorization server.
authorization_server = AuthorizationServer(
	app, query_client=query_client, save_token=save_token
)

authorization_server.init_app(app)

# Implement available grants
# In our case, these are: AuthorizationCode, Implicit, RefreshToken
class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
	TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic', 'client_secret_post']

	def save_authorization_code(self, code, request):
		client = request.client
		with Session(db.engine) as db_session:
			auth_code = AuthorizationCode(
				code=code,
				client_id=client.client_id,
				redirect_uri=request.redirect_uri,
				scope=request.scope,
				user_id=request.user.id,
				account_id=request.user.account_id,
			)
			db_session.add(auth_code)
			db_session.commit()
			return auth_code

	def query_authorization_code(self, code, client):
		with Session(db.engine) as db_session:
			item = db_session.query(AuthorizationCode).filter_by(code=code, client_id=client.client_id).first()
			if item and not item.is_expired():
					return item

	def delete_authorization_code(self, authorization_code):
		with Session(db.engine) as db_session:
			db_session.delete(authorization_code)
			db_session.commit()

	def authenticate_user(self, authorization_code):
		with Session(db.engine) as db_session:
			return db_session.query(User).get(authorization_code.user_id)


class RefreshTokenGrant(grants.RefreshTokenGrant):
	def authenticate_refresh_token(self, refresh_token):
		with Session(db.engine) as db_session:
			item = db_session.query(Token).filter_by(refresh_token=refresh_token).first()
			if item and item.is_refresh_token_valid():
				return item

	def authenticate_user(self, credential):
		with Session(db.engine) as db_session:
			return db_session.query(User).get(credential.user_id)

	def revoke_old_credential(self, credential):
		with Session(db.engine) as db_session:
			credential.revoked = True
			db_session.add(credential)
			db_session.commit()


# Register all the grant endpoints
authorization_server.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=False)])
authorization_server.register_grant(grants.ImplicitGrant)
authorization_server.register_grant(RefreshTokenGrant)

# Add revocation endpoint
class _RevocationEndpoint(RevocationEndpoint):
	def query_token(self, token, token_type_hint, client):
		q = Token.query.filter_by(client_id=client.client_id)
		if token_type_hint == 'access_token':
				return q.filter_by(access_token=token).first()
		elif token_type_hint == 'refresh_token':
				return q.filter_by(refresh_token=token).first()
		# without token_type_hint
		item = q.filter_by(access_token=token).first()
		if item:
				return item
		return q.filter_by(refresh_token=token).first()

	def revoke_token(self, token):
		token.revoked = True
		db.session.add(token)
		db.session.commit()


authorization_server.register_endpoint(_RevocationEndpoint)

# Define resource server/resource protector
class _BearerTokenValidator(BearerTokenValidator):
	def authenticate_token(self, token_string):
		return Token.query.filter_by(access_token=token_string).first()

	def request_invalid(self, request):
		return False

	def token_revoked(self, token):
		return token.revoked


require_oauth = ResourceProtector()
require_oauth.register_token_validator(_BearerTokenValidator())

# Flask endpoints

@app.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
	"""
	OAuth2 authorization endpoint. Shows an authentication dialog for the
	logged-in user, which allows them to see the permissions required
	by the app they're authenticating.
	"""
	user = current_user()
	if not user:
		return redirect(url_for('auth_login', next=flask.request.url))
	if flask.request.method == 'GET':
		try:
			grant = authorization_server.validate_consent_request(end_user=user)
		except OAuth2Error as error:
			return error.error
		return render_template('auth/oauth_authorize.html', user=user, grant=grant)
	grant_user = user
	return authorization_server.create_authorization_response(grant_user=grant_user)

@app.route('/oauth/revoke', methods=['POST'])
def revoke_token():
	"""OAuth2 token revocation endpoint."""
	return authorization_server.create_endpoint_response(_RevocationEndpoint.ENDPOINT_NAME)

@app.route('/oauth/token', methods=['POST'])
def issue_token():
	"""OAuth2 token issuing endpoint."""
	return authorization_server.create_token_response()
