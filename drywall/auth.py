# encoding: utf-8
"""
Contains code for authentication and OAuth2 support.
"""
from drywall.auth_models import User, Client, Token, AuthorizationCode
from drywall import app
from drywall import config
from drywall import db
from drywall import objects
from drywall import utils

from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector, current_token
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc7009 import RevocationEndpoint
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc7662 import IntrospectionEndpoint
from flask import render_template, flash, request, redirect, session, url_for
from email_validator import validate_email, EmailNotValidError
from uuid import uuid4 # For client IDs
from secrets import token_hex # For client secrets
# We're using these functions for now; if anyone has any suggestions for
# whether this is secure or not, see issue #3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

#################
# User accounts #
#################

def register_user(username, email, password):
	"""
	Registers a new user. Returns the Account object for the newly created
	user.

	Raises a ValueError if the username or email is already taken.
	"""
	# Do some basic validation
	if db.get_object_by_key_value_pair("account", {"username": username}):
		raise ValueError("Username taken.")
	if db.get_user_by_email(email):
		raise ValueError("E-mail already in use.")
	# Create an Account object for the user
	account_object = {"type": "object", "object_type": "account",
						"username": username, "icon": "stub", "email": email}
	account_object_valid = objects.make_object_from_dict(account_object)
	added_object = db.add_object(account_object_valid)
	account_id = added_object['id']
	# Add the user to the user database
	user_dict = {"username": username, "account_id": account_id, "email": email,
				"password": generate_password_hash(password)}
	db.add_user(user_dict)

@app.route('/auth/sign_up', methods=["GET", "POST"])
def auth_signup():
	"""Sign-up page."""
	if request.method == "POST":
		username = request.form["username"]
		email = request.form["email"]
		password = request.form["password"]
		try:
			valid_email = validate_email(email).email
			register_user(username, valid_email, password)
		except (ValueError, EmailNotValidError) as e:
			flash(str(e))
		else:
			session.clear()
			user = db.get_user_by_email(valid_email)
			session["user_id"] = user["account_id"]
			return redirect(url_for("client_page"))

	instance = db.get_object_as_dict_by_id("0")
	return render_template("auth/sign_up.html",
							instance_name=instance["name"],
							instance_description=instance["description"],
							instance_domain=instance["address"])

@app.route('/auth/login', methods=["GET", "POST"])
def auth_login():
	"""Login page."""
	if request.method == "POST":
		email = request.form["email"]
		password = request.form["password"]
		try:
			valid_email = validate_email(email).email
			user = db.get_user_by_email(valid_email)
			if not user:
				raise ValueError("User with provided email does not exist.")
			if not check_password_hash(user['password'], password):
				raise ValueError("Invalid password.")
		except (ValueError, EmailNotValidError) as e:
			flash(str(e))
		else:
			session.clear()
			session["user_id"] = user["account_id"]
			return redirect(url_for("client_page"))

	if "user_id" in session:
		return redirect(url_for("client_page"))
	instance = db.get_object_as_dict_by_id("0")
	return render_template("auth/login.html",
							instance_name=instance["name"],
							instance_description=instance["description"],
							instance_domain=instance["address"])

@app.route('/auth/logout', methods=["GET", "POST"])
def auth_logout():
	"""Logout page."""
	session.clear()
	return redirect(url_for("index_page"))

####################
# OAuth2 (Authlib) #
####################
# This code is, admittedly, a huge mess. If you're familiar with Authlib,
# feel free to send a MR with cleanups where you deem necessary.

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

# Initialize the authorization server.
def query_client(client_id):
	return Client.query.filter_by(id=client_id).first()

def save_token(token_data, request):
	if request.user:
		user_id = request.user.get_user_id()
	else:
		# client_credentials grant_type
		user_id = request.client.user_id
		# or, depending on how you treat client_credentials
		user_id = None
	token = Token(
		client_id=request.client.client_id,
		user_id=user_id,
		**token_data
	)
	db.session.add(token)
	db.session.commit()

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

# Define endpoints
class MyRevocationEndpoint(RevocationEndpoint):
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

# Register endpoints to authorization server
authorization_server.register_endpoint(MyRevocationEndpoint)
# FIXME invocation docs are borked. figure out how the sqlalchemy imports do it

# Add Flask-compatible endpoints
@app.route('/oauth/revoke', methods=['POST'])
def revoke_token():
	return authorization_server.create_endpoint_response(MyRevocationEndpoint.ENDPOINT_NAME)

# @app.route('/oauth/introspect', methods=['POST'])
# def introspect_token():
# 	return authorization_server.create_endpoint_response(MyIntrospectionEndpoint.ENDPOINT_NAME)

# Define resource server/resource protector
class MyBearerTokenValidator(BearerTokenValidator):
	def authenticate_token(self, token_string):
		return Token.query.filter_by(access_token=token_string).first()

	def request_invalid(self, request):
		return False

	def token_revoked(self, token):
		return token.revoked

require_oauth = ResourceProtector()
require_oauth.register_token_validator(MyBearerTokenValidator())

# Other OAuth endpoints
@app.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
	user = current_user()
	if not user:
		return redirect(url_for('login', next=request.url))
	if request.method == 'GET':
		try:
			grant = authorization_server.validate_consent_request(end_user=user)
		except OAuth2Error as error:
			return error.error
		return render_template('oauth/authorize.html', user=user, grant=grant)
	if not user and 'username' in request.form:
		username = request.form.get('username')
		user = User.query.filter_by(username=username).first()
	if request.form['confirm']:
		grant_user = user
	else:
		grant_user = None
	return authorization_server.create_authorization_response(grant_user=grant_user)

@app.route('/oauth/token', methods=['POST'])
def issue_token():
	return authorization_server.create_token_response()
