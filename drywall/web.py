# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about
pages. Authentication pages are defined in the auth module.
"""
from drywall import db
from drywall import app
from drywall import settings

from flask import redirect, render_template, session, url_for

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
	return redirect(url_for('login_page'))

@app.route('/settings/account')
def settings_account():
	"""Account settings."""
	if not "user_id" in session:
		return redirect(url_for('login_page'))
	instance = db.get_object_as_dict_by_id("0")
	return render_template("settings/account.html",
	                       user_name=db.get_object_as_dict_by_id(session['user_id']),
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

