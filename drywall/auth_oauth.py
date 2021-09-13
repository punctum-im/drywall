# coding: utf-8
"""
Contains the necessary Authlib setup bits for OAuth2.

This code is, admittedly, a huge mess. If you're familiar with Authlib,
feel free to send a MR with cleanups where you deem necessary.
"""
from drywall.auth_models import User, Client, Token, AuthorizationCode
from drywall.auth import current_user
from drywall import app
from drywall import db

from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector, current_token
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc7009 import RevocationEndpoint
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc7662 import IntrospectionEndpoint
from flask import render_template, redirect, session, url_for
import flask
from sqlalchemy.orm import Session
from uuid import uuid4

# Client-related functions

def new_client(client_dict):
	"""
	Creates a new client from the provided client dict, which contains
	the following variables:

	- name (string) - contains the name of the client.
	- type (string) - 'userapp' or 'bot'
	- uri (string)  - contains URI
	- scopes (list) - list of chosen scopes
	- owner_id (id) - user ID of the creator

	This automatically creates an account in case of a bot account, and
	adds the resulting client to the database.

	Returns the created client.
	"""
	with Session(db.engine) as db_session:
		client = Client(
			client_id=str(uuid4()),
			client_id_issued_at = int(time.time()),
			type=client_dict['type'],
			owner_id=client_dict['owner_id']
		)

		client_metadata = {
			"client_name": client_dict['name'],
			"client_uri": client_dict['uri'],
			"scope": client_dict['scopes']
		}
		client.set_client_metadata(client_metadata)

		client.client_secret = generate_secret()

		db_session.add(client)
		db_session.commit()

#
# -*-*- AuthLib stuff starts here -*-*-
#

# Helper functions

def query_client(client_id):
	"""Gets a client by ID. Returns None if not found."""
	with Session(db.engine) as db_session:
		return db_session.query(Client).filter_by(client_id=client_id).first()

def save_token(token_data, request):
	"""Saves a token to the database."""
	if request.user:
		user_id = request.user.get_user_id()
	else:
		user_id = request.client.user_id
	with Session(db.engine) as db_session:
		token = Token(
			client_id=request.client.client_id,
			user_id=user_id,
			account_id=request.user.account_id,
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
		auth_code = AuthorizationCode(
			code=code,
			client_id=client.client_id,
			redirect_uri=request.redirect_uri,
			scope=request.scope,
			user_id=request.user.id,
		)
		db.session.add(auth_code)
		db.session.commit()
		return auth_code

	def query_authorization_code(self, code, client):
		item = AuthorizationCode.query.filter_by(code=code, client_id=client.client_id).first()
		if item and not item.is_expired():
				return item

	def delete_authorization_code(self, authorization_code):
		db.session.delete(authorization_code)
		db.session.commit()

	def authenticate_user(self, authorization_code):
		return User.query.get(authorization_code.user_id)


class RefreshTokenGrant(grants.RefreshTokenGrant):
	def authenticate_refresh_token(self, refresh_token):
		item = Token.query.filter_by(refresh_token=refresh_token).first()
		if item and item.is_refresh_token_valid():
				return item

	def authenticate_user(self, credential):
		return User.query.get(credential.user_id)

	def revoke_old_credential(self, credential):
		credential.revoked = True
		db.session.add(credential)
		db.session.commit()

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
	if not user and 'username' in request.form:
		username = flask.request.form.get('username')
		user = User.query.filter_by(username=username).first()
	if request.form['confirm']:
		grant_user = user
	else:
		grant_user = None
	return authorization_server.create_authorization_response(grant_user=grant_user)

@app.route('/oauth/revoke', methods=['POST'])
def revoke_token():
	"""OAuth2 token revocation endpoint."""
	return authorization_server.create_endpoint_response(_RevocationEndpoint.ENDPOINT_NAME)

@app.route('/oauth/token', methods=['POST'])
def issue_token():
	"""OAuth2 token issuing endpoint."""
	return authorization_server.create_token_response()
