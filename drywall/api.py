# coding: utf-8
"""
This file contains API path definitions for all API paths.
"""
from drywall import db
from drywall import objects
from drywall import pings
from drywall import app
from drywall import config
from drywall import auth # noqa: F401
from drywall import web  # noqa: F401
from drywall.auth import require_oauth

import simplejson as json
from flask import Response, request

VERSION = "0.1"

# Define our instance.
instance_dict = {"type": "object", "object_type": "instance",
                 "address": config.get('instance_domain'),
                 "server_software": "drywall " + VERSION,
                 "name": config.get('instance_name'),
                 "description": config.get('instance_description')}
created_instance_object = objects.make_object_from_dict(instance_dict, extend="0",
                          ignore_nonexistent_id_in_extend=True)
if not db.id_taken("0"):
	db.add_object(created_instance_object)
else:
	db.push_object(id="0", object=created_instance_object)

# Function templates

def api_get(object_id, object_type=None):
	"""
	Gets an object by ID and returns the required object.
	"""
	object = db.get_object_as_dict_by_id(object_id)
	if not object:
		return pings.response_from_error(4)
	if object_type and not object['object_type'] == object_type:
		return pings.response_from_error(5)
	return object

def api_patch(object_id, object_type=None):
	"""
	Patches an object by ID and returns the required object.
	"""
	if not db.get_object_as_dict_by_id(object_id):
		return pings.response_from_error(4)

	patch_dict = request.json
	if not patch_dict:
		return pings.response_from_error(2)

	try:
		object = objects.make_object_from_dict(patch_dict, extend=object_id)
	except TypeError as e:
		return pings.response_from_error(10, error_message=e)
		# TODO: differentiate between the possible typeerrors
	except KeyError as e:
		return pings.response_from_error(7, error_message=e)
	except ValueError as e:
		return pings.response_from_error(6, error_message=e)

	if object_type and not object.__dict__['object_type'] == object_type:
		return pings.response_from_error(5)

	db.push_object(object_id, object)

	return object.__dict__

def api_post(object_dict, object_type=None):
	"""
	Takes an object and posts it to the server.
	"""
	if not object_dict:
		return pings.response_from_error(2)
	if object_type and not object_dict['object_type'] == object_type:
		return pings.response_from_error(5)

	try:
		object = objects.make_object_from_dict(object_dict)
	except TypeError as e:
		return pings.response_from_error(10, error_message=e)
		# TODO: differentiate between the possible typeerrors
	except KeyError as e:
		return pings.response_from_error(7, error_message=e)

	db.add_object(object)

	return Response(json.dumps(object.__dict__), status=201, mimetype='application/json')

def api_delete(object_id, object_type=None):
	"""
	Deletes an object by ID.
	"""
	object = db.get_object_as_dict_by_id(object_id)
	if not object:
		return pings.response_from_error(4)
	if object_type and not object['object_type'] == object_type:
		return pings.response_from_error(5)

	return {"id": db.delete_object(object_id)}

def api_get_patch_delete(object_id, object_type=None):
	"""
	Gets/patches an object by ID depending on the method.
	"""
	if request.method == "GET":
		return api_get(object_id, object_type=object_type)
	elif request.method == "PATCH":
		return api_patch(object_id, object_type=object_type)
	elif request.method == "DELETE":
		return api_delete(object_id, object_type=object_type)

def api_post_conference_child(conference_id, object_type, object_data):
	"""
	Template for POST /api/v1/conference/<conference_id>/<object_type> APIs
	"""
	if not object_data:
		return pings.response_from_error(2)
	data = object_data.copy()
	if object_data['object_type'] == "invite":
		data['conference_id'] = conference_id
	else:
		data['parent_conference'] = conference_id
	return api_post(object_data, object_type=object_type)

def api_get_patch_delete_conference_child(conference_id, object_type, object_id):
	"""
	Template for GET/PATCH/DELETE actions on conference members, invites, roles
	etc.
	"""
	try:
		object_get = api_get(object_id, object_type=object_type)
		object_get_id = object_get['id']
	except:
		return object_get
	if object_type == "invite":
		conference_id_key = "conference_id"
	else:
		conference_id_key = "parent_conference"
	if object_get[conference_id_key] != conference_id:
		error_message = "The given " + object_type + " does not belong to the given conference"
		return pings.response_from_error(8, error_message=error_message)
	if request.method == "GET":
		return object_get
	else:
		return api_get_patch_delete(object_get_id, object_type=object_type)

def api_report(report_dict, object_id, object_type=None):
	"""Template for /api/v1/<type>/<id>/report endpoints."""
	api_get(object_id, object_type=object_type)

	new_report_dict = {"target": object_id}
	if 'note' in report_dict:
		new_report_dict['note'] = report_dict['note']
	report = objects.make_object_from_dict(new_report_dict)

	db.add_object(report)
	return Response(json.dumps(report.__dict__), status=201, mimetype='application/json')

def api_report_conference_child(conference_id, report_dict, object_id, object_type):
	"""
	Template for POST /api/v1/conference/<conference_id>/<object_type> APIs
	"""
	try:
		object_get = api_get(object_id, object_type=object_type)
		object_get['id']
	except:
		return object_get
	if object_type == "invite":
		conference_id_key = "conference_id"
	else:
		conference_id_key = "parent_conference"
	if object_get[conference_id_key] != conference_id:
		error_message = "The given " + object_type + " does not belong to the given conference"
		return pings.response_from_error(8, error_message=error_message)
	return api_report(report_dict, object_id, object_type)

##
# API methods
##

# Objects, IDs and our instance

@app.route('/api/v1/instance')
def api_get_instance():
	"""Returns information about the instance (ID 0)."""
	return db.get_object_as_dict_by_id("0")

@app.route('/api/v1/id', methods=['POST'])
def api_post_by_id():
	"""Takes an object and creates the object on the server."""
	return api_post(request.json)

@app.route('/api/v1/id/<object_id>', methods=['GET', 'PATCH', 'DELETE'])
def api_get_patch_delete_by_id(object_id):
	"""
	Takes an object ID and returns/patches/deletes the object with the
	provided ID.
	"""
	return api_get_patch_delete(object_id=object_id)

@app.route('/api/v1/id/<object_id>/report', methods=['POST'])
def api_report_by_id(object_id):
	"""
	Takes an object ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, object_id)

@app.route('/api/v1/stash/request', methods=['POST'])
def api_stash_request():
	"""
	Creates and returns a new stash.
	"""
	data_dict = request.json
	if not data_dict:
		return pings.response_from_error(2)
	if not data_dict['id_list']:
		return pings.response_from_error(7)

	id_list = data_dict['id_list']

	try:
		stash = objects.create_stash(id_list)
	except ValueError:
		return pings.response_from_error(11)
	except KeyError as e:
		return pings.response_from_error(9, error_message=str(e))

	return stash

# TODO: Federation, authentication, clients
# Probably will be in separate files, but I'll note it down here for now

# Accounts

@app.route('/api/v1/accounts', methods=['POST'])
def api_post_account():
	"""
	Takes an Account object and creates it on the server.
	"""
	return api_post(request.json, object_type="account")

@app.route('/api/v1/accounts/<account_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_account(account_id):
	"""
	Takes the ID of an Account object and returns the object with
	the provided ID if it's an account.
	"""
	return api_get_patch_delete(object_id=account_id, object_type="account")

@app.route('/api/v1/accounts/<account_id>/report', methods=['POST'])
def api_report_account(account_id):
	"""
	Takes an account ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, account_id, object_type="account")

# TODO: /api/v1/accounts/<account_id>/block
# Requires authentication

# Conferences

@app.route('/api/v1/conferences', methods=['POST'])
def api_post_conference():
	"""
	Takes a Conference object and creates it on the server.
	"""
	return api_post(request.json, object_type="conference")

@app.route('/api/v1/conferences/<conference_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_conference(conference_id):
	"""
	Takes the ID of a Conference object and returns the object with
	the provided ID if it's a conference.
	"""
	return api_get_patch_delete(object_id=conference_id, object_type="conference")

@app.route('/api/v1/conferences/<conference_id>/report', methods=['POST'])
def api_report_conference(conference_id):
	"""
	Takes a conference ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, conference_id, object_type="conference")

@app.route('/api/v1/conferences/<conference_id>/members', methods=['POST'])
def api_post_conference_member(conference_id):
	"""
	Takes a ConferenceMember object and creates it on the server.
	Assigns the provided conference ID as the parent_conference.
	"""
	return api_post_conference_child(conference_id, "conference_member", request.json)

@app.route('/api/v1/conferences/<conference_id>/members/<member_id>',
           methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_conference_member(conference_id, member_id):
	"""
	Gets/patches/deletes a ConferenceMember in the conference by ID.
	"""
	return api_get_patch_delete_conference_child(conference_id, "conference_member", member_id)

@app.route('/api/v1/conferences/<conference_id>/members/<member_id>/report', methods=['POST'])
def api_report_conference_member(conference_id, member_id):
	"""
	Takes an conference member ID and report data and reports the object with
	the provided ID.
	"""
	return api_report_conference_child(conference_id, request.json, member_id, object_type="conference_member")

@app.route('/api/v1/conferences/<conference_id>/channels', methods=['POST'])
def api_post_conference_channel(conference_id):
	"""
	Takes a Channel object and creates it on the server.
	Assigns the provided conference ID as the parent_conference.
	"""
	return api_post_conference_child(conference_id, "channel", request.json)

@app.route('/api/v1/conferences/<conference_id>/channels/<channel_id>',
           methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_conference_channel(conference_id, channel_id):
	"""
	Gets/patches/deletes a channel in the conference by ID.
	"""
	return api_get_patch_delete_conference_child(conference_id, "channel", channel_id)

@app.route('/api/v1/conferences/<conference_id>/channels/<channel_id>/report', methods=['POST'])
def api_report_conference_channel(conference_id, channel_id):
	"""
	Takes a channel ID and report data and reports the object with the
	provided ID.
	"""
	return api_report_conference_child(conference_id, request.json, channel_id, object_type="channel")

@app.route('/api/v1/conferences/<conference_id>/roles', methods=['POST'])
def api_post_conference_role(conference_id):
	"""
	Takes a Role object and creates it on the server.
	Assigns the provided conference ID as the parent_conference.
	"""
	return api_post_conference_child(conference_id, "role", request.json)

@app.route('/api/v1/conferences/<conference_id>/roles/<role_id>',
           methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_conference_role(conference_id, role_id):
	"""
	Gets/patches/deletes a role in the conference by ID.
	"""
	return api_get_patch_delete_conference_child(conference_id, "role", role_id)

@app.route('/api/v1/conferences/<conference_id>/roles/<role_id>/report', methods=['POST'])
def api_report_conference_role(conference_id, role_id):
	"""
	Takes a role ID and report data and reports the object with the
	provided ID.
	"""
	return api_report_conference_child(conference_id, request.json, role_id, object_type="role")

@app.route('/api/v1/conferences/<conference_id>/invites', methods=['POST'])
def api_post_conference_invite(conference_id):
	"""
	Takes a Invite object and creates it on the server.
	Assigns the provided conference ID as the parent_conference.
	"""
	return api_post_conference_child(conference_id, "invite", request.json)

@app.route('/api/v1/conferences/<conference_id>/invites/<invite_id>',
           methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_conference_invite(conference_id, invite_id):
	"""
	Gets/patches/deletes a invite in the conference by ID.
	"""
	return api_get_patch_delete_conference_child(conference_id, "invite", invite_id)

@app.route('/api/v1/conferences/<conference_id>/invites/<invite_id>/report', methods=['POST'])
def api_report_conference_invite(conference_id, invite_id):
	"""
	Takes an invite ID and report data and reports the object with the
	provided ID.
	"""
	return api_report_conference_child(conference_id, request.json, invite_id, object_type="invite")

# Channels

@app.route('/api/v1/channels', methods=['POST'])
def api_post_channel():
	"""
	Takes a Channel object and creates it on the server.
	"""
	return api_post(request.json, object_type="channel")

@app.route('/api/v1/channels/<channel_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_channel(channel_id):
	"""
	Takes the ID of a Channel object and returns the object with
	the provided ID if it's a channel.
	"""
	return api_get_patch_delete(object_id=channel_id, object_type="channel")

@app.route('/api/v1/channels/<channel_id>/report', methods=['POST'])
def api_report_channel(channel_id):
	"""
	Takes a channel ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, channel_id, object_type="channel")

# Messages

@app.route('/api/v1/messages', methods=['POST'])
def api_post_message():
	"""
	Takes a Message object and creates it on the server.
	"""
	return api_post(request.json, object_type="message")

@app.route('/api/v1/messages/<message_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_message(message_id):
	"""
	Takes the ID of a Message object and returns the object with
	the provided ID if it's a message.
	"""
	return api_get_patch_delete(object_id=message_id, object_type="message")

@app.route('/api/v1/messages/<message_id>/report', methods=['POST'])
def api_report_message(message_id):
	"""
	Takes a message ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, message_id, object_type="message")

# Invite

@app.route('/api/v1/invites', methods=['POST'])
def api_post_invite():
	"""
	Takes an Invite object and creates it on the server.
	"""
	return api_post(request.json, object_type="invite")

@app.route('/api/v1/invites/<invite_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_invite(invite_id):
	"""
	Takes the ID of an Invite object and returns the object with
	the provided ID if it's an invite.
	"""
	return api_get_patch_delete(object_id=invite_id, object_type="invite")

@app.route('/api/v1/invites/<invite_id>/report', methods=['POST'])
def api_report_invite(invite_id):
	"""
	Takes an invite ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, invite_id, object_type="invite")

# TODO: /api/v1/invites/<invite_id>/join
# Needs authentication

# Roles

@app.route('/api/v1/roles', methods=['POST'])
def api_post_role():
	"""
	Takes a Role object and creates it on the server.
	"""
	return api_post(request.json, object_type="role")

@app.route('/api/v1/roles/<role_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_role(role_id):
	"""
	Takes the ID of a Role object and returns the object with
	the provided ID if it's a role.
	"""
	return api_get_patch_delete(object_id=role_id, object_type="role")

@app.route('/api/v1/roles/<role_id>/report', methods=['POST'])
def api_report_role(role_id):
	"""
	Takes an role ID and report data and reports the object with the
	provided ID.
	"""
	return api_report(request.json, role_id, object_type="role")

# Reports

@app.route('/api/v1/reports', methods=['POST'])
def api_post_report():
	"""
	Takes a Report object and creates it on the server.
	"""
	return api_post(request.json, object_type="report")

@app.route('/api/v1/reports/<report_id>', methods=["GET", "PATCH", "DELETE"])
def api_get_patch_delete_report(report_id):
	"""
	Takes the ID of a Report object and returns the object with
	the provided ID if it's a report.
	"""
	return api_get_patch_delete(object_id=report_id, object_type="report")
