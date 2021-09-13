# encoding: utf-8
"""
Contains code for authentication and OAuth2 support.
"""
from drywall.auth_models import User
from drywall import app
from drywall import config
from drywall import db
from drywall import objects
from drywall import utils

from flask import render_template, flash, request, redirect, session, url_for
from email_validator import validate_email, EmailNotValidError
from uuid import uuid4 # For client IDs
from secrets import token_hex # For client secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

# Helper functions

def current_user():
	"""Returns the logged-in user. Returns None if not logged in."""
	with Session(db.engine) as db_session:
		if 'user_id' in session:
			uid = session['user_id']
			return db_session.query(User).get(uid)
		return None

def can_account_access(account_id, object):
	"""
	Takes an account ID and an object dict and checks if the provided object
	can be accessed by the provided account.

	Note that this function uses Account object IDs, not user IDs.
	"""
	if not object:
		return False

	object_type = object['object_type']

	if object_type == 'message':
		return can_account_access(account_id, db.get_object_as_dict_by_id(object['parent_channel']))

	elif object_type == 'channel':
		channel_type = object['channel_type']
		if channel_type == 'text':
			return can_account_access(account_id, db.get_object_dict_by_id(object['parent_conference']))
		elif channel_type == 'direct_message':
			if account_id in object['members']:
				return True
			else:
				return False

	elif object_type == 'conference':
		conference_member = db.get_object_by_key_dict_value("conference_member", {"account_id": account_id})
		if not conference_member:
			return False

		if conference_member in object['members']:
			return True
		else:
			return False

	elif object_type in ['conference_member', 'role']:
		return can_account_access(account_id, db.get_object_dict_by_id(object['parent_conference']))

	elif object_type == 'report':
		if object['creator'] == account_id:
			return True
		elif is_account_admin(account_id):
			return True
		return False

	elif object_type in ['instance', 'account', 'invite', 'emoji']:
		return True

def is_account_admin(account_id):
	"""
	Gets an user by the provided account ID and checks if the user is an admin
	on the local instance. Returns True or False.
	"""
	with Session(db.engine) as db_session:
		try:
			user = db_session.query(User).filter(User.account_id == account_id).one()
		except NoResultFound:
			return False
		return user.is_admin

def get_user_by_account_id(account_id):
	"""
	Gets an user by the provided account ID.
	"""
	with Session(db.engine) as db_session:
		try:
			user = db_session.query(User).filter(User.account_id == account_id).one()
		except NoResultFound:
			return None
		return user.to_dict()

def login(user):
	"""
	Takes an User object and logs in as the provided user.
	"""
	if not isinstance(user, User):
		raise TypeError("Provided object is not an User")
	session.clear()
	session["user_id"] = user.id
	session["user_account_id"] = user.account_id

def get_user_by_email(email):
	"""
	Returns an User object with the provided e-mail address.
	If not found, returns None.
	"""
	with Session(db.engine) as db_session:
		try:
			user = db_session.query(User).filter(User.email == email).one()
		except NoResultFound:
			return None
		return user

def register_user(username, email, password):
	"""
	Registers a new user. Returns the Account object for the newly created
	user.

	Raises a ValueError if the username or email is already taken.
	"""
	# Do some basic validation
	if db.get_object_by_key_value_pair("account", {"username": username}):
		raise ValueError("Username taken.")
	if get_user_by_email(email):
		raise ValueError("E-mail already in use.")
	try:
		valid_email = validate_email(email).email
	except EmailNotValidError:
		raise ValueError("Provided e-mail is invalid.")

	# Create an Account object for the user
	account_object = {"type": "object", "object_type": "account",
						"username": username, "icon": "stub",
						"email": valid_email}
	account_object_valid = objects.make_object_from_dict(account_object)
	added_object = db.add_object(account_object_valid)
	account_id = added_object['id']

	# Add the user to the user database
	new_user = User(username=username, account_id=account_id,
				email=valid_email, password=generate_password_hash(password))

	with Session(db.engine) as db_session:
		db_session.add(new_user)
		db_session.commit()

	return new_user

# Pages

@app.route('/auth/login', methods=["GET", "POST"])
def auth_login():
	"""Login page."""
	if request.method == "POST":
		email = request.form["email"]
		password = request.form["password"]
		try:
			valid_email = validate_email(email).email
			user = get_user_by_email(valid_email)
			if not user:
				raise ValueError("User with provided email does not exist.")
			with Session(db.engine) as db_session:
				if not check_password_hash(user.password, password):
					raise ValueError("Invalid password.")
		except (ValueError, EmailNotValidError) as e:
			flash(str(e))
		else:
			login(user)
			return redirect(url_for("client_page"))

	if "user_id" in session:
		return redirect(url_for("client_page"))
	instance = db.get_object_as_dict_by_id("0")
	return render_template("auth/login.html",
							instance_name=instance["name"],
							instance_description=instance["description"],
							instance_domain=instance["address"])

@app.route('/auth/sign_up', methods=["GET", "POST"])
def auth_signup():
	"""Sign-up page."""
	if request.method == "POST":
		username = request.form["username"]
		email = request.form["email"]
		password = request.form["password"]
		try:
			valid_email = validate_email(email).email
			register_user(username, email, password)
		except (ValueError, EmailNotValidError) as e:
			flash(str(e))
		else:
			user = get_user_by_email(valid_email)
			login(user)
			return redirect(url_for("client_page"))

	instance = db.get_object_as_dict_by_id("0")
	return render_template("auth/sign_up.html",
							instance_name=instance["name"],
							instance_description=instance["description"],
							instance_domain=instance["address"])

@app.route('/auth/logout', methods=["GET", "POST"])
def auth_logout():
	"""Logout page."""
	session.clear()
	return redirect(url_for("index_page"))
