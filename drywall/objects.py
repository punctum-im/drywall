# encoding: utf-8
"""
Defines classes for all objects in the protocol for easier
object creation.
Usage: import the file and define an object using one of the classes
"""
from drywall import db
from drywall import utils

import datetime
import uuid    # for assign_id function

# Common functions
default_nonrewritable_keys = ["id", "type", "object_type"]

def assign_id():
	"""
	Assigns an ID. Returns the ID as a string.

	We currently use UUID4 to generate IDs, which *should* help prevent
	collisions. In the future, this function can be extended to make use of
	an ID server with snowflake IDs, but this is currently unnecesary.

	Optionally, if we want to make *absolutely* sure there will be no
	collisions, we could add a function that check for the ID's presence
	in the database, but this would slow everything down.
	"""
	id = uuid.uuid4()
	return str(id)

def _validate_id_key(self, key, value):
	"""Shorthand function to validate ID keys."""
	test_object = db.get_object_as_dict_by_id(value)
	if not test_object:
		raise TypeError("No object with the ID given in the key '" + key + "' was found. (" + value + ")")
	elif self.id_key_types[key] != "any" and not test_object['object_type'] == self.id_key_types[key]:
		raise TypeError("The object given in the key '" + key + "' does not have the correct object type. (is " + test_object['object_type'] + ", should be " + self.id_key_types[key] + ")")

def _strip_invalid_keys(self, object_dict):
	"""
	Takes an object dict, removes all invalid values and performs a few
	checks.

	This function is used in the init_object function to avoid redundancy.
	To properly validate an object dict, turn it into an object with the
	make_object_from_dict function. This will automatically ensure that
	all necessary checks have been done.
	"""

	final_dict = {}
	for key, value in object_dict.items():
		if key in self.valid_keys:
			# Validate ID keys
			if self.key_types[key] == 'id':
				_validate_id_key(self, key, value)
			elif self.key_types[key] == 'id_list':
				for id_value in value:
					_validate_id_key(self, key, id_value)

			# Validate unique keys
			if self.unique_keys:
				if key in self.unique_keys:
					unique_key_violations = db.get_object_by_key_value_pair(self.object_type, {key: value})
					if unique_key_violations:
						unique_check_fail = False
						for mention in unique_key_violations:
							if mention['id'] != object_dict['id']:
								unique_check_fail = True
						if unique_check_fail:
							raise TypeError("The value in the '" + key + "' key is already taken.")

			final_dict[key] = value

	return final_dict

def init_object(self, object_dict, force_id=False, patch_dict=False, federated=False):
	"""
	Common initialization function shared by all objects. Returns a dict.
	For use in the __init__ function in classes.

	Raises:
	- TypeError - "No object with the ID given in the key <key> was found."
	- TypeError - "The object given in the key <key> does not have the
	               correct type."
	- ValueError - attempted to rewrite a non-rewritable key
	- KeyError - missing key
	"""
	init_dict = {}

	if patch_dict and not force_id:
		force_id = object_dict['id']

	# This is done like this to avoid breakage when the ID = 0.
	if str(force_id) == "False":
		init_dict['id'] = assign_id()
	else:
		init_dict['id'] = str(force_id)
	self.id = init_dict['id']
	init_dict['type'] = self.type
	init_dict['object_type'] = self.object_type

	for var in ['id', 'type', 'object_type']:
		if var not in object_dict or object_dict[var] != init_dict[var]:
			object_dict[var] = init_dict[var]

	if patch_dict:
		current_object = db.get_object_as_dict_by_id(object_dict['id'])
		# Check for non-rewritable keys
		if self.nonrewritable_keys:
			try:
				utils.any_key_from_list_in_dict(default_nonrewritable_keys + self.nonrewritable_keys, patch_dict)
			except KeyError as e:
				found_key = e.args[0]
				if found_key in current_object and patch_dict[found_key] != current_object[found_key]:
					raise ValueError(e)
		final_patch_dict = _strip_invalid_keys(self, patch_dict)

	# Add all valid keys
	clean_object_dict = _strip_invalid_keys(self, object_dict)
	final_dict = {**clean_object_dict, **init_dict}

	# Add default keys if needed
	if self.default_keys:
		for key, value in self.default_keys.items():
			if key not in final_dict:
				final_dict[key] = value

	# Check for missing keys
	try:
		utils.missing_key_from_list_in_dict(self.required_keys, final_dict)
	except KeyError as e:
		raise e

	if patch_dict:
		final_dict.update(final_patch_dict)

	return final_dict

def get_object_class_by_type(object_type):
	"""
	Takes an object type and returns the applicable object.
	Returns None if there is no object with the given type.
	"""
	try:
		return class_to_object[object_type]
	except KeyError:
		return None

def make_object_from_dict(passed_object_dict, extend=False, ignore_nonexistent_id_in_extend=False):
	"""
	Takes a dict (for example from a POST/PATCH request) and creates an object
	using one of the available classes. Returns the created object.

	This can be used to do error checking and normalize any objects submitted
	through the API.

	Optional arguments:
	  - extend (default: False) - for use with PATCH; takes an ID, if not False
	                              takes keys from the original object with
	                              the given ID.
	  - ignore_nonexistent_id_in_extend (default: False) - if True, does not
	                                    raise errors when the ID given in the
	                                    extend variable does not exist
	"""

	patch_dict = False

	if str(extend) == "False":
		object_dict = passed_object_dict
	else:
		if ignore_nonexistent_id_in_extend:
			object_dict = passed_object_dict
		else:
			object_dict = db.get_object_as_dict_by_id(extend)
			if not object_dict:
				raise NameError("Object with passed ID not found")
			patch_dict = passed_object_dict

	object_type = object_dict["object_type"]
	object_class = get_object_class_by_type(object_type)
	if object_class is None:
		raise TypeError("Nonexistent object_class")

	try:
		final_object = object_class(object_dict, force_id=extend, patch_dict=patch_dict)
	except (KeyError, ValueError, TypeError) as e:
		raise e

	return final_object

###############
# Permissions #
###############

class Permissions:
	"""Contains information about permissions."""
	# Permission shorthands
	shorthands = {
		'see_channel': 1,
		'read_channel': 2,
		'write_channel': 4,
		'embed': 8,
		'moderate_messages': 16,
		'create_invite': 32,
		'modify_channel': 64,
		'change_nickname': 128,
		'moderate_nicknames': 256,
		'kick': 512,
		'ban': 1024,
		'edit_roles': 2048,
		'edit_conference': 4096
	}
	shorthands_numerical = {v: k for k, v in shorthands.items()}

	# Scopes to permission numbers
	scopes = {
		"conference:read": 1,   # See channel
		"conference:moderate": 4096, # Modify conference
		"channel:read": 2,      # Read messages in/connect to channel
		"channel:write": 4,     # Send messages to/speak in channel
		"channel:moderate": 64, # Modify channel information
		"message:read": 2,      # Alias for channel:read
		"message:embed": 8,     # Upload/add attachments
		"message:moderate": 16, # Pin messages, delete other users' messages
		"invite:create": 32,    # Create and modify invites
		"conference_member:write_nick": 128, # Change own nickname
		"conference_member:moderate_nick": 256, # Change other users' nicknames
		"conference_member:kick": 512, # Kick users
		"conference_member:ban": 1024, # Ban users
		"role:moderate": 2048, # Modify and assign roles
	}

	def __init__(self, value=0):
		"""Initializes a permission map."""
		validate_permissions(value)
		self.value = value

	def validate(self):
		validate_permissions(self.value)

	def break_down_to_values(self):
		"""Turns permission value in map to a list with seperate values"""
		return utils.powers_to_list(self.value)

	def value_to_shorthands(self):
		"""Turns permission value in map to shorthands"""
		num_list = self.break_down_to_values()
		str_list = []
		for key in num_list:
			str_list.append(self.shorthands_numerical[key])
		return str_list

def validate_permissions(value):
	"""Validates whether the permission value is correct or not."""
	if value <= 8191 and value >= 0 and isinstance(value, int):
		return value
	else:
		raise ValueError


######################
# Objects begin here #
######################

class Object:
	"""Core functions for objects."""
	type = 'object'
	# !!! vvv Set these in your object
	object_type = None
	valid_keys = []
	key_types = {} # key name: key type; see docs for key types
	# !!! ^^^ Set these in your object
	required_keys = []
	id_key_types = {}
	default_keys = []
	nonrewritable_keys = []
	unique_keys = []

	def __init__(self, object_dict, force_id=False, patch_dict=False, federated=False):
		"""
		Initializes an object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		  - federated (default: False) - TBD
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict, federated=federated)

class Instance(Object):
	"""
	Contains information about an instance.
	"""
	type = 'object'
	object_type = 'instance'
	valid_keys = ["address", "server_software", "name", "description"]
	required_keys = ["address", "server_software", "name"]
	key_types = {"address": "string", "server_software": "string", "name": "string", "description": "string"}
	nonrewritable_keys = ["address"]

class Account(Object):
	"""
	Contains information about an account.
	"""
	type = 'object'
	object_type = 'account'
	valid_keys = ["username", "short_status", "status", "bio", "index_user", "email", "bot", "friends", "blocklist"]
	required_keys = ["username", "short_status"]
	key_types = {"username": "string", "short_status": "number", "status": "string", "bio": "string", "email": "string", "bot": "boolean", "index_user": "boolean", "friends": "id_list", "blocklist": "id_list"}
	default_keys = {"short_status": 0, "index_user": False, "bot": False}
	id_key_types = {"friends": "account", "blocklist": "account"}
	nonrewritable_keys = ["username"]
	unique_keys = ["username"]

class Channel(Object):
	"""
	Contains information about a channel.
	"""
	type = 'object'
	object_type = 'channel'
	valid_keys = ["name", "permissions", "channel_type", "parent_conference", "members", "icon", "description"]
	required_keys = ["name", "permissions", "channel_type"] # the rest is handled during init
	default_keys = {"permissions": "21101"}
	key_types = {"name": "string", "permissions": "permission_map", "channel_type": "string", "parent_conference": "id", "members": "id_list", "icon": "string", "description": "string"}
	id_key_types = {"parent_conference": "conference", "members": "conference_member"}
	nonrewritable_keys = ["channel_type", "parent_conference"]

	def __init__(self, object_dict, force_id=False, patch_dict=False, federated=False):
		__doc__ = Object.__doc__ # noqa: F841
		super().__init__(object_dict, force_id=force_id, patch_dict=patch_dict, federated=federated)
		__channel_type = self.__dict__['channel_type']
		if __channel_type == 'text' or __channel_type == 'media':
			if 'parent_conference' not in self.__dict__:
				raise KeyError('parent_conference')
		elif __channel_type == 'direct_message':
			if 'members' not in self.__dict__:
				raise KeyError('members')
			if 'icon' not in self.__dict__:
				raise KeyError('icon')
		else:
			raise KeyError('invalid channel type ' + __channel_type)

class Message(Object):
	"""
	Contains information about a message.
	"""
	type = 'object'
	object_type = 'message'
	valid_keys = ["content", "parent_channel", "author", "post_date", "edit_date", "edited", "attached_files", "reactions", "reply_to", "replies"]
	required_keys = ["content", "parent_channel", "author", "post_date", "edited"]
	key_types = {"content": "string", "parent_channel": "id", "author": "id", "post_date": "datetime", "edited": "boolean", "edit_date": "datetime", "attached_files": "list", "reactions": "list", "reply_to": "id", "replies": "id_list"}
	default_keys = {"edited": False}
	id_key_types = {"parent_channel": "channel", "author": "account", "reply_to": "message", "replies": "message"}
	nonrewritable_keys = ["parent_channel", "author", "post_date", "edit_date", "edited"]

	def __init__(self, object_dict, force_id=False, patch_dict=False, federated=False):
		__doc__ = Object.__doc__ # noqa: F841
		super().__init__(object_dict, force_id=force_id, patch_dict=patch_dict, federated=federated)
		if patch_dict:
			self.__dict__['edited'] = True
			self.__dict__['edit_date'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
		else:
			self.__dict__['post_date'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
			if 'edit_date' in self.__dict__.keys() and not self.__dict__['edited']:
				self.__dict__.pop('edit_date')

class Conference(Object):
	"""
	Contains information about a conference.
	"""
	type = 'object'
	object_type = 'conference'
	valid_keys = ["name", "description", "icon", "owner", "index_conference", "permissions", "creation_date", "channels", "users", "roles"]
	required_keys = ["name", "icon", "owner", "permissions", "creation_date"]
	default_keys = {"index_conference": False, "channels": [], "users": [], "roles": [], "permissions": "21101"}
	key_types = {"name": "string", "description": "string", "icon": "string", "owner": "id", "index_conference": "boolean", "permissions": "permission_map", "creation_date": "datetime", "channels": "id_list", "users": "id_list", "roles": "id_list"}
	id_key_types = {"owner": "account", "channels": "channel", "users": "account", "roles": "role"}
	nonrewritable_keys = ["creation_date"]

	def __init__(self, object_dict, force_id=False, patch_dict=False, federated=False):
		__doc__ = Object.__doc__ # noqa: F841
		super().__init__(object_dict, force_id=force_id, patch_dict=patch_dict, federated=federated)
		self.__dict__['creation_date'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

class ConferenceMember(Object):
	"""
	Contains information about a conference member.
	"""
	type = 'object'
	object_type = 'conference_member'
	valid_keys = ["account_id", "nickname", "parent_conference", "roles", "permissions", "banned"]
	required_keys = ["account_id", "permissions", "parent_conference"]
	default_keys = {"banned": False, "roles": [], "permissions": "21101"}
	key_types = {"account_id": "id", "nickname": "string", "parent_conference": "id", "roles": "id_list", "permissions": "permission_map", "banned": "boolean"}
	id_key_types = {"account_id": "account", "roles": "role", "parent_conference": "conference"}
	nonrewritable_keys = []

class Invite(Object):
	"""
	Contains information about an invite.
	"""
	type = 'object'
	object_type = 'invite'
	valid_keys = ["code", "conference_id", "creator"]
	required_keys = ["code", "conference_id", "creator"]
	key_types = {"code": "string", "conference_id": "id", "creator": "id"}
	id_key_types = {"conference_id": "conference", "creator": "account"}
	nonrewritable_keys = ["conference_id", "creator"]
	unique_keys = ["code"]

class Role(Object):
	"""
	Contains information about a role.
	"""
	type = 'object'
	object_type = 'role'
	valid_keys = ["name", "permissions", "color", "description", "parent_conference"]
	required_keys = ["name", "permissions", "color", "parent_conference"]
	key_types = {"name": "string", "permissions": "permission_map", "color": "string", "description": "string", "parent_conference": "id"}
	id_key_types = {"parent_conference": "conference"}
	default_keys = {"color": "100, 100, 100", "permissions": "21101"}

class Report(Object):
	"""
	Contains information about a report.
	"""
	type = 'object'
	object_type = 'report'
	valid_keys = ["target", "note", "submission_date"]
	required_keys = ["target", "submission_date"]
	key_types = {"target": "id", "note": "string", "submission_date": "datetime"}
	id_key_types = {"target": "any"}
	nonrewritable_keys = ["target"]

	def __init__(self, object_dict, force_id=False, patch_dict=False, federated=False):
		__doc__ = Object.__doc__ # noqa: F841
		super().__init__(object_dict, force_id=force_id, patch_dict=patch_dict, federated=federated)
		self.__dict__['submission_date'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()


# Class to object type mapping
# These are ordered this way to avoid issues with missing dependencies
# in case they're created in order (like in the case of tests)
class_to_object = {
	'instance': Instance,
	'account': Account,
	'conference': Conference,
	'role': Role,
	'conference_member': ConferenceMember,
	'channel': Channel,
	'message': Message,
	'invite': Invite,
	'report': Report
}

object_types = class_to_object.keys()
objects = class_to_object.values()

def create_stash(id_list):
	"""
	Takes up to 100 object IDs and returns a dict containing each ID alongside
	the content of the associated object.

	Raises a KeyError with the missing ID if an ID is not found.

	Raises a ValueError if the ID limit is exceeded.
	"""
	if len(id_list) > 100:
		raise ValueError

	stash = {}
	stash['type'] = "stash"
	stash['id_list'] = id_list
	for id in id_list:
		object_dict = db.get_object_as_dict_by_id(id)
		if object_dict:
			stash[id] = object_dict
		else:
			raise KeyError('ID does not exist: ' + id)

	return stash
