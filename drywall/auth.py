# encoding: utf-8
"""
Contains code for authentication and OAuth2 support.
"""
from drywall import app
from drywall import db
from drywall import objects
from drywall import utils
from drywall import web

import hashlib
from flask import render_template, flash, request, redirect, session, url_for
from email_validator import validate_email, EmailNotValidError
from uuid import uuid4 # For client IDs
from secrets import token_hex # For client secrets
# We're using these functions for now; if anyone has any suggestions for
# whether this is secure or not, see issue #3
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

##########
# OAuth2 #
##########

client_keys = ['client_id', 'client_secret', 'name', 'description', 'owner']

def create_client(client_dict):
	"""Creates a client from a basic client dict."""
	client_dict['client_id'] = uuid4()
	client_dict['client_secret'] = token_hex(16)
	if "user_id" in session:
		client_dict['owner'] = session["user_id"]
	return db.add_client(utils.validate_dict(client_dict, client_keys))

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
	if db.get_object_by_key_value_pair({"object_type": "account", "username": username}):
		raise ValueError("Username taken.")
	if db.get_user_by_email(email):
		raise ValueError("E-mail already in use.")
	# Create an Account object for the user
	account_object = { "type": "object", "object_type": "account",
	                   "username": username, "icon": "stub", "email": email }
	account_object_valid = objects.make_object_from_dict(account_object)
	added_object = db.add_object(account_object_valid)
	account_id = added_object['id']
	# Add the user to the user database
	user_dict = { "username": username, "account_id": account_id, "email": email,
	              "password": generate_password_hash(password) }
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
