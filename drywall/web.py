# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about
pages. Authentication pages are defined in the auth module.
"""
from drywall import db
from drywall import app
from drywall import objects
from drywall import settings

from flask import flash, redirect, render_template, request, session, url_for
from email_validator import validate_email, EmailNotValidError

######################
# Index, information #
######################

@app.route('/')
def index_page():
	"""Index page."""
	instance = db.get_object_as_dict_by_id("0")
	return render_template("index.html",
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

@app.route('/about')
def about_page():
	"""About page."""
	instance = db.get_object_as_dict_by_id("0")
	return render_template("about/about.html",
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

@app.route('/about/rules')
def rules_page():
	"""Rules page."""
	instance = db.get_object_as_dict_by_id("0")
	return render_template("about/rules.html",
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

@app.route('/about/tos')
def tos_page():
	"""ToS page."""
	instance = db.get_object_as_dict_by_id("0")
	return render_template("about/tos.html",
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

@app.route('/client')
def client_page():
	"""Client page. If none is provided, redirects to user settings."""
	if settings.get('client_page'):
		return redirect(settings.get('client_page'))
	flash("Client has not been set up! You have been taken to the settings page.")
	return redirect(url_for('settings_page'))

#################
# User settings #
#################

@app.route('/settings')
def settings_page():
	"""Settings page."""
	if "user_id" in session:
		return redirect(url_for('settings_account'))
	return redirect(url_for('auth_login'))

@app.route('/settings/account', methods=["GET", "POST"])
def settings_account():
	"""Account settings."""
	if request.method == "POST":
		session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
		request_form = dict(request.form)
		account_dict = db.get_object_as_dict_by_id(session['user_id']).copy()
		user_dict = db.get_user_by_email(account_dict['email']).copy()
		username = request_form['username']
		try:
			email = validate_email(request_form['email']).email
		except EmailNotValidError as e:
			flash(str(e))
		old_email = account_dict['email']
		if account_dict['username'] != username:
			account_dict['username'] = username,
			# Weird bug: during testing, the username set itself to "('USERNAME',)"
			# no matter what I did. The following line avoids this, and hopefully
			# won't cause any trouble in the future.
			account_dict['username'] = tuple(account_dict['username'])[0]
			user_dict['username'] = account_dict['username']
		if account_dict['email'] != email:
			account_dict['email'] = email
			user_dict['email'] = email
		try:
			db.push_object(session['user_id'], objects.make_object_from_dict(account_dict, extend=session['user_id']))
			db.update_user(old_email, user_dict)
		except (KeyError, ValueError, TypeError) as e:
			flash(str(e))
		session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
		return redirect(url_for('settings_account'))
	if not "user_id" in session:
		return redirect(url_for('auth_login'))
	instance = db.get_object_as_dict_by_id("0")
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
	if not db.get_object_as_dict_by_id(session["user_id"]):
		return redirect(url_for('auth_logout'))
	user_dict = session['user_dict']
	return render_template("settings/account.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

