# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about
pages. Authentication pages are defined in the auth module.
"""
from drywall import db
from drywall import app

from flask import render_template

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
