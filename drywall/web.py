# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about pages.

For sign-up/log-in pages, see the auth submodule.
For OAuth-related pages (/oauth/*), see the auth_oauth submodule.
For user settings (/settings/*), see the web_settings submodule.
"""
from drywall import app
from drywall import config
from drywall import db
from drywall import web_settings # noqa: F401

from flask import flash, redirect, render_template, url_for

def _info_page(template):
	"""Shorthand for info page initialization."""
	instance = db.get_object_as_dict_by_id("0")
	return render_template(template,
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"])

@app.route('/')
def index_page():
	"""Index page."""
	return _info_page("index.html")

@app.route('/about')
def about_page():
	"""About page."""
	return _info_page("about/about.html")

@app.route('/about/rules')
def rules_page():
	"""Rules page."""
	return _info_page("about/rules.html")

@app.route('/about/tos')
def tos_page():
	"""ToS page."""
	return _info_page("about/tos.html")

@app.route('/client')
def client_page():
	"""Client page. If none is provided, redirects to user settings."""
	if config.get('client_page'):
		return redirect(config.get('client_page'))
	flash("Client has not been set up! You have been taken to the settings page.")
	return redirect(url_for('settings_redirect'))
