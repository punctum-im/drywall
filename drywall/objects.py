# coding: utf-8
"""
Defines classes for all objects in the protocol for easier
object creation.
Usage: import the file and define an object using one of the classes
"""
from drywall import db_dummy as db

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

def missing_key_from_list_in_dict(test_list, test_dict):
	"""
	Takes a list and a dictionary and checks if all keys in the list are present
	in the dictionary. Raises a KeyError with the missing key if found, returns
	False otherwise.
	"""
	for key in test_list:
		if key not in test_dict:
			raise KeyError(key)
	return False

def any_key_from_list_in_dict(test_list, test_dict):
	"""
	Takes a list and a dictionary and checks if any of the keys from the list are
	present in the dict. Raises a KeyError with the key if found, returns False
	otherwise.
	"""
	for key in test_list:
		if key in test_dict:
			raise KeyError(key)
	return False

def init_object(self, object_dict, force_id=False, patch_dict=False):
	"""
	Common initialization function shared by all objects. Returns a dict.
	For use in the __init__ function in classes.
	"""
	final_dict = {}
	final_patch_dict = {}

	# This is done like this to avoid breakage when the ID = 0.
	if str(force_id) == "False":
		final_dict['id'] = assign_id()
	else:
		final_dict['id'] = str(force_id)
	final_dict['type'] = self.type
	final_dict['object_type'] = self.object_type

	if patch_dict:
		# Check for non-rewritable keys
		if self.nonrewritable_keys:
			try:
				any_key_from_list_in_dict(default_nonrewritable_keys + self.nonrewritable_keys, patch_dict)
			except KeyError as e:
				raise ValueError(e)
		for key, value in patch_dict.items():
			if key in self.valid_keys:
				if self.key_types[key] == 'id':
					test_object = db.get_object_as_dict_by_id(value)
					if not test_object:
						raise TypeError("No object with the ID given in the key '" + key + "' was found.")
					elif not test_object['object_type'] == self.id_key_types[key]:
						raise TypeError("The object given in the key '" + key + "' does not have the correct object type. (is " + test_object['object_type'] + ", should be " + self.id_key_types[key] + ")")
				final_patch_dict[key] = value

	# Add all valid keys
	for key, value in object_dict.items():
		if key in self.valid_keys:
			if self.key_types[key] == 'id':
				test_object = db.get_object_as_dict_by_id(value)
				if test_object is None:
					raise TypeError("No object with the ID given in the key '" + key + "' was found.")
				elif not test_object['object_type'] == self.id_key_types[key]:
					raise TypeError("The object given in the key '" + key + "' does not have the correct object type. (is " + test_object['object_type'] + ", should be " + self.id_key_types[key] + ")")
			final_dict[key] = value

	# Add default keys if needed
	try:
		self.default_keys
	except:
		pass
	else:
		for key, value in self.default_keys.items():
			if key not in final_dict:
				final_dict[key] = value

	# Check for missing keys
	try:
		missing_key_from_list_in_dict(self.required_keys, final_dict)
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
	if object_type == 'instance':
		return Instance
	elif object_type == "account":
		return Account
	elif object_type == "channel":
		return Channel
	elif object_type == "message":
		return Message
	elif object_type == "conference":
		return Conference
	elif object_type == "conference_member":
		return ConferenceMember
	elif object_type == "invite":
		return Invite
	elif object_type == "role":
		return Role
	elif object_type == "attachment":
		return Attachment
	else:
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
	except (KeyError, ValueError) as e:
		raise e

	return final_object

######################
# Objects begin here #
######################

class Instance:
	"""
	Contains information about an instance.
	"""
	type = 'object'
	object_type = 'instance'
	valid_keys = ["address", "server_software", "name", "description"]
	required_keys = ["address", "server_software", "name"]
	key_types = {"address": "string", "server_software": "string", "name": "string", "description": "string"}
	nonrewritable_keys = ["address"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Instance object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class Account:
	"""
	Contains information about an account.
	"""
	type = 'object'
	object_type = 'account'
	valid_keys = ["username", "short_status", "status", "bio", "index", "email", "bot", "bot_owner", "friends", "blocklist"]
	required_keys = ["username", "short_status", "email"]
	key_types = {"username": "string", "short_status": "number", "status": "string", "bio": "string", "email": "string", "bot": "boolean", "bot_owner": "id", "friends": "id_list", "blocklist": "id_list"}
	id_key_types = {"bot_owner": "account", "friends": "account", "blocklist": "account"}
	nonrewritable_keys = ["username"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Account object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)
		if "bot" in self.__dict__ and self.__dict__["bot"] == "true" and not self.__dict__["bot_owner"]:
			raise KeyError('bot_owner')

class Channel:
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

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Channel object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)
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

class Message:
	"""
	Contains information about a message.
	"""
	type = 'object'
	object_type = 'message'
	valid_keys = ["content", "parent_channel", "author", "post_date", "edit_date", "edited", "attachment", "reactions"]
	required_keys = ["content", "parent_channel", "author", "post_date", "edited"]
	key_types = {"content": "string", "parent_channel": "id", "author": "id", "post_date": "string", "edited": "boolean"}
	id_key_types = {"parent_channel": "channel", "author": "account"}
	nonrewritable_keys = ["parent_channel", "author", "post_date", "edit_date", "edited"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Message object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class Conference:
	"""
	Contains information about a conference.
	"""
	type = 'object'
	object_type = 'conference'
	valid_keys = ["name", "description", "icon", "owner", "index", "permissions", "creation_date", "channels", "users", "roles"]
	required_keys = ["name", "icon", "owner", "permissions", "creation_date"]
	default_keys = {"index": "false", "channels": [], "users": [], "roles": [], "permissions": "21101"}
	key_types = {"name": "string", "description": "string", "icon": "string", "owner": "id", "index": "boolean", "permissions": "permission_map", "creation_date": "string", "channels": "id_list", "users": "id_list", "roles": "id_list"}
	id_key_types = {"owner": "account", "channels": "channel", "users": "account", "roles": "role"}
	nonrewritable_keys = ["creation_date"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Conference object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class ConferenceMember:
	"""
	Contains information about a conference member.
	"""
	type = 'object'
	object_type = 'conference_member'
	valid_keys = ["user_id", "nickname", "roles", "permissions", "banned"]
	required_keys = ["user_id", "permissions"]
	default_keys = {"banned": "false", "roles": [], "permissions": "21101"}
	key_types = {"user_id": "id", "nickname": "string", "roles": "id_list", "permissions": "permission_map", "banned": "boolean"}
	id_key_types = {"user_id": "account", "roles": "role"}
	nonrewritable_keys = []

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a ConferenceMember object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class Invite:
	"""
	Contains information about an invite.
	"""
	type = 'object'
	object_type = 'invite'
	valid_keys = ["name", "conference_id", "creator"]
	required_keys = ["name", "conference_id", "creator"]
	key_types = {"name": "string", "conference_id": "id", "creator": "id"}
	id_key_types = {"conference_id": "conference", "creator": "account"}
	nonrewritable_keys = ["conference_id", "creator"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Invite object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class Role:
	"""
	Contains information about a role.
	"""
	type = 'object'
	object_type = 'role'
	valid_keys = ["name", "permissions", "color", "description"]
	required_keys = ["name", "permissions", "color"]
	key_types = {"name": "string", "permissions": "permission_map", "color": "string"}
	default_keys = {"color": "100, 100, 100", "permissions": "21101"}

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Role object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class Attachment:
	"""
	Contains information about an attachment.
	"""
	type = 'object'
	object_type = 'attachment'
	valid_keys = ["attachment_type", "quoted_message", "media_link", "title", "embed_type", "description", "color", "image"]
	required_keys = ["attachment_type"]
	key_types = {"attachment_type": "string", "quoted_message": "id", "media_link": "string", "title": "string", "embed_type": "number", "description": "string", "color": "string", "image": "string"}
	id_key_types = {"quoted_message": "message"}
	nonrewritable_keys = ["attachment_type"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Attachment object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                assign_id() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)
		# Unfortunately attachments have various types, each with different fields (some required),
		# so we have to do some extra error checking here.
		__attachment_type = self.__dict__["attachment_type"]
		if __attachment_type == "quote":
			if "quoted_message" not in self.__dict__:
				raise KeyError("quoted_message")
		elif __attachment_type == "media":
			if "media_link" not in self.__dict__:
				raise KeyError("media_link")
		elif __attachment_type == "embed":
			if "title" not in self.__dict__:
				raise KeyError("title")
			if "embed_type" not in self.__dict__:
				raise KeyError("embed_type")
		else:
			raise TypeError("Invalid attachment_type: " + __attachment_type)
