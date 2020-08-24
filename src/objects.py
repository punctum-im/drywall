# coding: utf-8
"""
Defines classes for all objects in the protocol for easier
object creation.
Usage: import the file and define an object using one of the classes
"""
import sys
import id
import db_dummy as db

# Common functions
default_nonrewritable_keys = [ "id", "type", "object_type" ]

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
		final_dict['id'] = id.assign()
	else:
		final_dict['id'] = str(force_id)
	final_dict['type'] = self.type
	final_dict['object_type'] = self.object_type

	if patch_dict:
		try:
			self.nonrewritable_keys
		except:
			pass
		else:
			try:
				any_key_from_list_in_dict(default_nonrewritable_keys + self.nonrewritable_keys, patch_dict)
			except KeyError as e:
				raise ValueError(e)

		for key, value in patch_dict.items():
			if key in self.valid_keys:
				final_patch_dict[key] = value

	for key, value in object_dict.items():
		if key in self.valid_keys:
			final_dict[key] = value

	try:
		self.default_keys
	except:
		pass
	else:
		for key, value in self.default_keys.items():
			if key not in final_dict:
				final_dict[key] = value

	try:
		missing_key_from_list_in_dict(self.required_keys, final_dict)
	except KeyError as e:
		raise e

	if patch_dict:
		final_dict.update(final_patch_dict)

	return final_dict

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

	patch_dict=False

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

	# Unfortunately, there doesn't seem to be an easy way to convert an object
	# type name to an actual object, so we have to copy the same commands many
	# times in a bunch of elif statements. Let me know if there's an easier way
	# to do this.
	if object_type == "instance":
		try:
			final_object = Instance(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "account":
		try:
			final_object = Account(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "channel":
		try:
			final_object = Channel(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "message":
		try:
			final_object = Message(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "conference":
		try:
			final_object = Conference(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "conference_user":
		try:
			final_object = ConferenceUser(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "invite":
		try:
			final_object = Invite(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "role":
		try:
			final_object = Role(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError) as e:
			raise e
	elif object_type == "attachment":
		try:
			final_object = Attachment(object_dict, force_id=extend, patch_dict=patch_dict)
		except (KeyError,ValueError,TypeError) as e:
			raise e
	else:
		raise TypeError("Wrong object_type")
	# Sorry.
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
	nonrewritable_keys = ["address"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Instance object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		try:
			self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)
		except (KeyError, ValueError) as e:
			raise e
class Account:
	"""
	Contains information about an account.
	"""
	type = 'object'
	object_type = 'account'
	valid_keys = ["username", "short_status", "status", "bio", "index", "email", "bot", "bot_owner", "friends", "blocklist"]
	required_keys = ["username", "short_status", "email"]
	nonrewritable_keys = ["username"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Account object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)
		if self.__dict__['bot'] and not self.__dict__['bot_owner']:
			raise KeyError('bot_owner')

class Channel:
	"""
	Contains information about a channel.
	"""
	type = 'object'
	object_type = 'channel'
	valid_keys = ["name", "permissions", "channel_type", "parent_conference", "members", "icon", "description"]
	required_keys = ["name", "permissions", "channel_type"] # the rest is handled during init
	default_keys = { "permissions": "21101" }
	nonrewritable_keys = ["channel_type", "parent_conference"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Channel object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
	nonrewritable_keys = ["parent_channel", "author", "post_date", "edit_date", "edited"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Message object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
	default_keys = { "index": "false", "channels": [], "users": [], "roles": [], "permissions": "21101" }
	nonrewritable_keys = ["creation_date"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Conference object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
		  - patch_dict (default: False) - takes False or a dictionary with keys
		                                  that will be replaced in the object.
		                                  (You should probably also set force_id
		                                  if you use this.)
		"""
		self.__dict__ = init_object(self, object_dict, force_id=force_id, patch_dict=patch_dict)

class ConferenceUser:
	"""
	Contains information about a conference user.
	"""
	type = 'object'
	object_type = 'conference_user'
	valid_keys = ["user_id", "nickname", "roles", "permissions", "banned"]
	required_keys = ["user_id", "permissions"]
	default_keys = { "banned": "false", "roles": [], "permissions": "21101" }
	nonrewritable_keys = []

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a ConferenceUser object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
	nonrewritable_keys = ["conference_id", "creator"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Invite object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
	default_keys = { "color": "100, 100, 100", "permissions": "21101" }

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes a Role object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
	nonrewritable_keys = ["attachment_type"]

	def __init__(self, object_dict, force_id=False, patch_dict=False):
		"""
		Initializes an Attachment object.

		Optional arguments:
		  - force_id (default: False) - takes False or an ID, if an ID is given
		                                sets the object id to the specified ID,
		                                otherwise the ID is generated with the
		                                id.assign() function
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
			raise TypeError("Invalid attachment_type: " + attachment_type)
