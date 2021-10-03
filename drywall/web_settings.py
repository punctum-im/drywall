# coding: utf-8
"""
Contains the endpoints for user account settings.

For sign-up/log-in pages, see the auth submodule.
For OAuth-related pages (/oauth/*), see the auth_oauth submodule.
For information pages (/about/*), see the web submodule.
"""
from drywall import app
from drywall import auth
from drywall import auth_oauth
from drywall import auth_models
from drywall import db
from drywall import utils

from flask import flash, redirect, render_template, request, session, url_for

# Helper functions

def _settings_sanity_checks():
	"""Sanity checks for settings pages."""
	# If not logged in, send to log-in page
	if "user_id" not in session:
		return redirect(url_for('auth_login'))

	# Log out user in case the user's account has been deleted
	session["account_dict"] = db.get_object_as_dict_by_id(session["account_id"])
	if not session["account_dict"]:
		return redirect(url_for('auth_logout'))

	return False

def _settings_render(template, category, is_subpage=False, **kwargs):
	"""Template for rendering simple settings pages."""
	instance = db.get_object_as_dict_by_id("0")
	user_dict = session['account_dict']
	return render_template(template,
	                       user_dict=user_dict,
	                       user_name=user_dict["username"],
	                       user_email=user_dict["email"],
	                       instance_name=instance["name"],
	                       instance_description=instance["description"],
	                       instance_domain=instance["address"],
	                       settings_subpage=is_subpage,
	                       settings_category=category,
						   **kwargs)

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

# Account settings

@app.route('/settings')
def settings_redirect():
	"""Settings page."""
	if "user_id" in session:
		return redirect(url_for('settings_account'))
	return redirect(url_for('auth_login'))

@app.route('/settings/account', methods=["GET", "POST"])
def settings_account():
	"""Account settings."""
	_sanity_check = _settings_sanity_checks()
	if _sanity_check:
		return _sanity_check

	if request.method == "POST":
		session["account_dict"] = db.get_object_as_dict_by_id(session["account_id"])
		edit_dict = dict(request.form)
		edit_dict['account_id'] = session["account_id"]
		try:
			auth.edit_user(session["user_id"], edit_dict)
		except (KeyError, ValueError, TypeError) as e:
			flash(str(e))
		session["account_dict"] = db.get_object_as_dict_by_id(session["account_id"])
		return redirect(url_for('settings_account'))

	return _settings_render("settings/account.html", "account")

# Client settings

@app.route('/settings/clients', methods=["GET", "POST"])
def settings_clients():
	"""OAuth client settings."""
	_sanity_check = _settings_sanity_checks()
	if _sanity_check:
		return _sanity_check
	return _settings_render("settings/clients.html", "clients",
							apps_owned=auth_oauth.get_clients_owned_by_user(session["user_id"]))

@app.route('/settings/clients/new', methods=["GET", "POST"])
def settings_clients_new():
	"""New app creation."""
	_sanity_check = _settings_sanity_checks()
	if _sanity_check:
		return _sanity_check

	if len(auth_oauth.get_clients_owned_by_user(session['user_id'])) >= 25:
		flash("Maximum amount of apps (25) has been reached. Remove unused apps and try again.")
		return redirect(url_for('settings_clients'))

	if request.method == "POST":
		# Prepare a client dict with all the information from the provided form
		client_dict_info = web_scopebox_to_scopes(dict(request.form), cleanup_form_dict=True)
		client_dict = client_dict_info[1]
		client_dict["scopes"] = list(client_dict_info[0].keys())
		client_dict["owner_id"] = session["user_id"]
		client_dict["owner_account_id"] = session["account_id"]
		client_dict["uri"] = 'FIXME'

		# Attempt to create a client
		try:
			auth_oauth.create_client(client_dict)
		except ValueError as e:
			flash(str(e))
			return redirect(url_for('settings_clients_new'))

		# Once done, return to client settings
		return redirect(url_for('settings_clients'))

	return _settings_render("settings/clients_new.html", "clients", is_subpage=True)

@app.route('/settings/clients/<client_id>', methods=["GET", "POST"])
def settings_clients_edit(client_id):
	"""App editing."""
	_sanity_check = _settings_sanity_checks()
	if _sanity_check:
		return _sanity_check

	app_dict = auth_oauth.get_client_if_owned_by_user(session['user_id'], client_id)
	if not app_dict:
		return render_template("settings/clients_404.html"), 404

	_app_scopes = auth_models.scope_to_list(app_dict['client_metadata']["scope"])
	app_scopes = {}
	for scope in _app_scopes:
		app_scopes[scope] = "checked"

	if request.method == "POST":
		client_dict_info = web_scopebox_to_scopes(dict(request.form), cleanup_form_dict=True)
		client_dict = client_dict_info[1]
		client_dict["scopes"] = list(client_dict_info[0].keys())
		auth_oauth.edit_client(app_dict["client_id"], client_dict)
		return redirect('/settings/clients')

	return _settings_render("settings/clients_edit.html", "clients", is_subpage=True,
							app_dict=app_dict, app_scopes=app_scopes)

@app.route('/settings/clients/<client_id>/remove', methods=["GET", "POST"])
def settings_clients_edit_remove(client_id):
	"""App removal (not to be confused with revoking)."""
	_sanity_check = _settings_sanity_checks()
	if _sanity_check:
		return _sanity_check

	app_dict = auth_oauth.get_client_if_owned_by_user(session['user_id'], client_id)
	if not app_dict:
		return render_template("settings/clients_404.html"), 404

	if request.method == "POST":
		auth_oauth.remove_client(app_dict['client_id'])
		flash("Removed " + app_dict['client_metadata']["client_name"] + ".")
		return redirect('/settings/clients')

	return _settings_render("settings/clients_remove.html", "clients", is_subpage=True, app_dict=app_dict)
