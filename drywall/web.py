# encoding: utf-8
"""
Contains endpoints for the backend's default pages, such as the about
pages. Authentication pages are defined in the auth module.
"""
from drywall import app
from drywall import auth
from drywall import config
from drywall import db
from drywall import objects
from drywall import utils

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
	if config.get('client_page'):
		return redirect(config.get('client_page'))
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
	if "user_id" not in session:
		return redirect(url_for('auth_login'))
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
	                       instance_domain=instance["address"],
	                       settings_subpage=False,
	                       settings_category="account")

scopebox_scopes = {"account-read": "account:read", # noqa: E305
    "account-write": "account:write",
    "conference-read": "conference:read",
    "conference-moderate": "conference:moderate",
    "channel-read": "channel:read",
    "channel-write": "channel:write",
    "channel-moderate": "channel:moderate",
    "message-write": "message:write",
    "message-moderate": "message:moderate",
    "invite-create": "invite:create",
    "conference-member-write-nick": "conference_member:write_nick",
    "conference-member-moderate-nick": "conference_member:moderate_nick",
    "conference-member-kick": "conference_member:kick",
    "conference-member-ban": "conference_member:ban",
    "role-moderate": "role-moderate"}

def web_scopebox_to_scopes(form_dict, cleanup_form_dict=False):
	"""Turns a scopebox's output from a web form to a valid scopes value."""
	scopes = {}
	if cleanup_form_dict:
		ret_form_dict = form_dict.copy()
	for scope, proper_scope in scopebox_scopes.items():
		if scope in form_dict and form_dict[scope] == 'on':
			scopes[proper_scope] = True
			if cleanup_form_dict:
				del ret_form_dict[scope]
	if cleanup_form_dict:
		return (scopes, ret_form_dict)
	else:
		return scopes

@app.route('/settings/clients', methods=["GET", "POST"])
def settings_clients():
	"""OAuth client settings."""
	if "user_id" not in session:
		return redirect(url_for('auth_login'))
	instance = db.get_object_as_dict_by_id("0")
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
	if not db.get_object_as_dict_by_id(session["user_id"]):
		return redirect(url_for('auth_logout'))
	user_dict = session['user_dict']
	return render_template("settings/clients.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       user_apps=db.get_clients_for_user(user_dict['id'], 'owner'),
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"],
	                       settings_subpage=False,
	                       settings_category="clients")

@app.route('/settings/clients/new', methods=["GET", "POST"])
def settings_clients_new():
	"""New app creation."""
	if "user_id" not in session:
		return redirect(url_for('auth_login'))
	instance = db.get_object_as_dict_by_id("0")
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
	if not db.get_object_as_dict_by_id(session["user_id"]):
		return redirect(url_for('auth_logout'))
	user_dict = session['user_dict']
	if len(db.get_clients_for_user(user_dict['id'], 'owner')) >= 25:
		flash("Maximum amount of apps (25) has been reached. Remove unused apps and try again.")
		return redirect(url_for('settings_clients'))
	if request.method == "POST":
		client_dict_info = web_scopebox_to_scopes(dict(request.form), cleanup_form_dict=True)
		client_dict = client_dict_info[1]
		client_dict["scopes"] = client_dict_info[0]
		client_dict["owner"] = session["user_id"]
		auth.create_client(client_dict)
		return redirect(url_for('settings_clients'))
	return render_template("settings/clients_new.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"],
	                       settings_subpage=True,
	                       settings_category="clients")

@app.route('/settings/clients/<client_id>', methods=["GET", "POST"])
def settings_clients_edit(client_id):
	"""App editing."""
	if "user_id" not in session:
		return redirect(url_for('auth_login'))
	if client_id == "":
		return redirect(url_for('settings_clients'))
	user_dict = session['user_dict']
	user_apps = db.get_clients_for_user(user_dict['id'], 'owner')
	app_dict = None
	for oauth_app in user_apps:
		if oauth_app["client_id"] == client_id:
			app_dict = oauth_app
			break
	if not app_dict:
		return render_template("settings/clients_404.html"), 404
	app_scopes = app_dict["scopes"].copy()
	app_scopes = utils.replace_values_in_dict_by_value({"True": "checked"}, app_scopes)
	app_scopes = utils.fill_dict_with_dummy_values(scopebox_scopes.values(), app_scopes, dummy="")
	if request.method == "POST":
		client_dict_info = web_scopebox_to_scopes(dict(request.form), cleanup_form_dict=True)
		client_dict = client_dict_info[1]
		client_dict["type"] = app_dict["type"]
		client_dict["scopes"] = client_dict_info[0]
		client_dict["owner"] = app_dict["owner"]
		if client_dict["type"] == "bot":
			client_dict["account_id"] = app_dict["account_id"]
		client_dict["client_id"] = app_dict["client_id"]
		client_dict["client_secret"] = app_dict["client_secret"]
		auth.edit_client(app_dict["client_id"], client_dict)
		return redirect('/settings/clients')
	instance = db.get_object_as_dict_by_id("0")
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
	if not db.get_object_as_dict_by_id(session["user_id"]):
		return redirect(url_for('auth_logout'))
	return render_template("settings/clients_edit.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       app_dict=app_dict,
	                       app_scopes=app_scopes,
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"],
	                       settings_subpage=True,
	                       settings_category="clients")

@app.route('/settings/clients/<client_id>/remove', methods=["GET", "POST"])
def settings_clients_edit_remove(client_id):
	"""App removal (not to be confused with revoking)."""
	if "user_id" not in session:
		return redirect(url_for('auth_login'))
	if client_id == "":
		return redirect(url_for('settings_clients'))
	user_dict = session['user_dict']
	user_apps = db.get_clients_for_user(user_dict['id'], 'owner')
	app_dict = None
	for oauth_app in user_apps:
		if oauth_app["client_id"] == client_id:
			app_dict = oauth_app
			break
	if not app_dict:
		return render_template("settings/clients_404.html"), 404
	if request.method == "POST":
		db.remove_client(app_dict["client_id"])
		flash("Removed " + app_dict["name"] + ".")
		return redirect('/settings/clients')
	instance = db.get_object_as_dict_by_id("0")
	session["user_dict"] = db.get_object_as_dict_by_id(session["user_id"])
	if not db.get_object_as_dict_by_id(session["user_id"]):
		return redirect(url_for('auth_logout'))
	return render_template("settings/clients_remove.html",
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       app_dict=app_dict,
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"],
	                       settings_subpage=True,
	                       settings_category="clients")
