# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about
pages. Authentication pages are defined in the auth module.
"""
from drywall import db
from drywall import app
from drywall import objects
from drywall import settings

from flask import redirect, render_template, request, session, url_for
from email_validator import validate_email, EmailNotValidError

def update_user():
	"""Updates the user dict stored in session storage"""
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])

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
		user_dict = db.get_object_as_dict_by_id(session['user_id'])
		user_dict['username'] == request.form['username'],
		user_dict['email'] == validate_email(request.form['email']).email
		db.push_object(session['user_id'], objects.make_object_from_dict(user_dict, extend=session['user_id']))
		update_user()
	if not "user_id" in session:
		return redirect(url_for('auth_login'))
	instance = db.get_object_as_dict_by_id("0")
	update_user()
	user_dict = session['user_dict']
	return render_template("settings/account.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

