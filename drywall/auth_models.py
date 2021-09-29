# coding: utf-8
"""
Contains SQLAlchemy models for authentication.
"""
from drywall import db_models
from drywall.db_models import Base

from authlib.common.encoding import json_loads, json_dumps
from authlib.oauth2.rfc6749 import ClientMixin, TokenMixin, AuthorizationCodeMixin
# FIXME: these functions appear to be missing, fix this once AuthLib 1.0 is out
# from authlib.oauth2.rfc6749 import scope_to_list, list_to_scope
from authlib.common.encoding import to_unicode
from datetime import time
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

class User(Base, SerializerMixin):
	"""
	Contains information about a registered user.
	Not to be confused with Account objects.
	"""
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True) # Integer, to differentiate from account IDs
	account_id = Column(String(255), ForeignKey('account.id'), nullable=False)
	account = relationship(db_models.Account)
	username = Column(String(255))
	email = Column(String(255))
	password = Column(Text)
	is_admin = Column(Boolean, default=False, nullable=False)

	def get_user_id(self):
		return self.id

class Client(Base, ClientMixin):
	"""Authlib-compatible Client model"""
	__tablename__ = 'clients'
	client_id = Column(String(48), index=True, primary_key=True) # in uuid4 format
	client_secret = Column(String(120))
	client_id_issued_at = Column(Integer, nullable=False, default=0)
	client_secret_expires_at = Column(Integer, nullable=False, default=0)
	_client_metadata = Column('client_metadata', Text)

	client_type = Column(String(255), nullable=False)

	owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
	owner = relationship('User')

	bot_account_id = Column(String(255), ForeignKey('account.id', ondelete='CASCADE'))
	bot_account = relationship('db_models.Account')

	# -*-*- AuthLib stuff begins here -*-*-
	def get_client_id(self):
		return self.client_id

	def get_default_redirect_uri(self):
		if self.redirect_uris:
			return self.redirect_uris[0]

	def get_allowed_scope(self, scope):
		if not scope:
			return ''
		allowed = set(self.scope.split())
		scopes = scope_to_list(scope)
		return list_to_scope([s for s in scopes if s in allowed])

	def check_redirect_uri(self, redirect_uri):
		return redirect_uri in self.redirect_uris

	def has_client_secret(self):
		return bool(self.client_secret)

	def check_client_secret(self, client_secret):
		return self.client_secret == client_secret

	def check_endpoint_auth_method(self, method, endpoint):
		if endpoint == 'token':
			return self.token_endpoint_auth_method == method
		return True

	def check_response_type(self, response_type):
		return response_type in self.response_types

	def check_grant_type(self, grant_type):
		return grant_type in self.grant_types

	@property
	def client_info(self):
		"""Implementation for Client Info in OAuth 2.0 Dynamic Client
		Registration Protocol via `Section 3.2.1`_.
		.. _`Section 3.2.1`: https://tools.ietf.org/html/rfc7591#section-3.2.1
		"""
		return dict(
			client_id=self.client_id,
			client_secret=self.client_secret,
			client_id_issued_at=self.client_id_issued_at,
			client_secret_expires_at=self.client_secret_expires_at,
		)

	@property
	def client_metadata(self):
		if 'client_metadata' in self.__dict__:
			return self.__dict__['client_metadata']
		if self._client_metadata:
			data = json_loads(self._client_metadata)
			self.__dict__['client_metadata'] = data
			return data
		return {}

	def set_client_metadata(self, value):
		self._client_metadata = json_dumps(value)

	@property
	def grant_types(self):
		return self.client_metadata.get('grant_types', [])

	@property
	def response_types(self):
		return self.client_metadata.get('response_types', [])

	@property
	def client_name(self):
		return self.client_metadata.get('client_name')

	@property
	def client_uri(self):
		return self.client_metadata.get('client_uri')

	@property
	def logo_uri(self):
		return self.client_metadata.get('logo_uri')

	@property
	def scope(self):
		return self.client_metadata.get('scope', '')

class Token(Base, TokenMixin):
	"""Authlib-compatible Token model"""
	__tablename__ = 'tokens'
	id = Column(String(255), primary_key=True) # In uuid4 format

	user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
	account_id = Column(String, ForeignKey('account.id', ondelete='CASCADE'))

	client_id = Column(String(48))
	token_type = Column(String(40))
	access_token = Column(String(255), unique=True, nullable=False)
	refresh_token = Column(String(255), index=True)
	scope = Column(Text, default='')
	issued_at = Column(
		Integer, nullable=False, default=lambda: int(time.time())
	)
	access_token_revoked_at = Column(Integer, nullable=False, default=0)
	refresh_token_revoked_at = Column(Integer, nullable=False, default=0)
	expires_in = Column(Integer, nullable=False, default=0)

	def check_client(self, client):
		return self.client_id == client.get_client_id()

	def get_scope(self):
		return self.scope

	def get_expires_in(self):
		return self.expires_in

	def is_revoked(self):
		return self.access_token_revoked_at or self.refresh_token_revoked_at

	def is_expired(self):
		if not self.expires_in:
			return False

		expires_at = self.issued_at + self.expires_in
		return expires_at < time.time()

	def is_refresh_token_valid(self):
		if self.is_expired() or self.is_revoked():
			return False
		return True

# FIXME: This should ideally be stored in a cache like Redis. Caching is
#        veeeery far on our TODO list though, so we've got time.
class AuthorizationCode(Base, AuthorizationCodeMixin):
	__tablename__ = 'authcodes'
	id = Column(Integer, primary_key=True)

	code = Column(String(120), unique=True, nullable=False)
	client_id = Column(String(48))
	redirect_uri = Column(Text, default='')
	response_type = Column(Text, default='')
	scope = Column(Text, default='')
	nonce = Column(Text)
	auth_time = Column(
		Integer, nullable=False,
		default=lambda: int(time.time())
	)

	user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
	account_id = Column(String(255), ForeignKey('account.id', ondelete='CASCADE'))

	code_challenge = Column(Text)
	code_challenge_method = Column(String(48))

	def is_expired(self):
		return self.auth_time + 300 < time.time()

	def get_redirect_uri(self):
		return self.redirect_uri

	def get_scope(self):
		return self.scope

	def get_auth_time(self):
		return self.auth_time

	def get_nonce(self):
		return self.nonce

# FIXME: temporary until authlib 1.0 is released
def list_to_scope(scope):
	"""Convert a list of scopes to a space separated string."""
	if isinstance(scope, (set, tuple, list)):
		return " ".join([to_unicode(s) for s in scope])
	if scope is None:
		return scope
	return to_unicode(scope)


def scope_to_list(scope):
	"""Convert a space separated string to a list of scopes."""
	if isinstance(scope, (tuple, list, set)):
		return [to_unicode(s) for s in scope]
	elif scope is None:
		return None
	return scope.strip().split()
