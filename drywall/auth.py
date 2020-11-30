# encoding: utf-8
"""
Contains authentication code and endpoints.
"""
from drywall import app
from drywall import db
from drywall import objects

import hashlib
from flask import render_template, flash, request
from email_validator import validate_email, EmailNotValidError

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
	              "password": password }
	db.add_user(user_dict)

@app.route('/auth/sign_up', methods=["GET", "POST"])
def auth_signup():
	"""Sign-up page."""
	if request.method == "POST":
		username = request.form["username"]
		email = request.form["email"]
		password = request.form["password"]
		try:
			valid_email = validate_email(email)
			register_user(username, valid_email, password)
		except (ValueError, EmailNotValidError) as e:
			flash(str(e))

	instance = db.get_object_as_dict_by_id("0")
	return render_template("auth/sign_up.html",
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])
