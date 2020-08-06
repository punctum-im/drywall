# coding: utf-8
"""
Defines classes for all objects in the protocol for easier
object creation.
Usage: import the file and define an object using one of the classes
"""

import id
import db_dummy as db

def make_object_from_dict(object_dict):
	"""
	Takes a dict (for example from a POST/PATCH request) and creates an object
	using one of the available classes. Returns the created object.

	This can be used to do error checking and normalize any objects submitted
	through the API.
	"""

	object_type = object_dict["object_type"]
	args = ""
	# Unfortunately, there doesn't seem to be an easy way to convert an object
	# type name to an actual object, so we have to copy the same commands many
	# times in a bunch of elif statements. Let me know if there's an easier way
	# to do this.
	if object_type == "instance":
		for key, value in object_dict.items():
			if Instance.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Instance(args)
	elif object_type == "account":
		for key, value in object_dict.items():
			if Account.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Account(args)
	elif object_type == "channel":
		for key, value in object_dict.items():
			if Channel.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Channel(args)
	elif object_type == "message":
		for key, value in object_dict.items():
			if Message.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Message(args)
	elif object_type == "conference":
		for key, value in object_dict.items():
			if Conference.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Conference(args)
	elif object_type == "conference_user":
		for key, value in object_dict.items():
			if ConferenceUser.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = ConferenceUser(args)
	elif object_type == "invite":
		for key, value in object_dict.items():
			if Invite.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Invite(args)
	elif object_type == "role":
		for key, value in object_dict.items():
			if Role.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Role(args)
	elif object_type == "attachment":
		for key, value in object_dict.items():
			if Attachment.__valid_variable__(key):
				args += key + '="' + value + '"'
		object = Attachment(args)
	else:
		raise TypeError("Wrong object_type")
	# Sorry.
	return object

class Instance:
	"""Contains information about an instance."""
	def __init__(self, address, software, name, description, _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'instance'
		self.address = str(address)
		self.server_software = str(software)
		self.name = str(name)
		self.description = str(description)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["address", "server_software", "name", "description"]:
			if var == test:
				return True
			else:
				return False

class Account:
	"""Contains information about an account."""
	def __init__(self, username, short_status, email, status="", bio="", index="false", bot="false", bot_owner="", friends=[], blocklist=[], _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'account'
		self.username = str(username)
		self.short_status = int(short_status)
		self.status = str(status)
		self.bio = str(bio)
		self.index = str(index)
		self.email = str(email)
		self.bot = str(bot)
		if bot and not bot_owner:
			print("No bot owner provided.")
			return 1
		else:
			self.bot_owner = str(bot_owner)
		self.friends = friends
		self.blocklist = blocklist
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["username", "short_status", "status", "bio", "index", "email", "bot", "bot_owner", "friends", "blocklist"]:
			if var == test:
				return True
			else:
				return False

class Channel:
	"""Contains information about a channel."""
	def __init__(self, name, permissions, channel_type, parent_conference, members, icon, description="", _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'channel'
		self.name = str(name)
		self.description = str(description)
		self.permissions = str(permissions)
		self.channel_type = str(channel_type)
		if self.channel_type == "text" or self.channel_type == "media":
			self.parent_conference = str(parent_conference)
		elif self.channel_type == "direct_message":
			self.members = list(members)
			self.icon = str(icon)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["name", "description", "permissions", "channel_type", "parent_conference", "members", "icon"]:
			if var == test:
				return True
			else:
				return False

class Message:
	"""Contains a message."""
	def __init__(self, content, parent_channel, author, post_date, edited="false", attachment="", edit_date="", reactions=[], _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'message'
		self.content = str(content)
		self.parent_channel = str(content)
		self.author = str(author)
		self.post_date = str(post_date)
		self.edit_date = str(edit_date)
		self.edited = edited
		self.reactions = reactions
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["content", "parent_channel", "author", "post_date", "edit_date", "edited", "reactions"]:
			if var == test:
				return True
			else:
				return False


class Conference:
	def __init__(self, name, icon, owner, default_permissions, creation_date, description="", index="false", channels=[], users=[], roles=[], _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'conference'
		self.name = str(name)
		self.description = str(description)
		self.icon = str(icon)
		self.owner = str(owner)
		self.index = str(index)
		self.default_permissions = str(default_permissions)
		self.creation_date = str(creation_date)
		self.channels = channels
		self.users = users
		self.roles = roles
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["name", "description", "icon", "owner", "index", "default_permissions", "creation_date", "channels", "users", "roles"]:
			if var == test:
				return True
			else:
				return False


class ConferenceUser:
	def __init__(self, user_id, nickname="", roles=[], permissions="", banned="false", _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'conference_user'
		self.nickname = str(nickname)
		self.roles = roles
		self.permissions = str(permissions)
		self.banned = str(banned)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["nickname", "roles", "permissions", "banned"]:
			if var == test:
				return True
			else:
				return False


class Invite:
	def __init__(self, name, conference_id, creator, _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'invite'
		self.name = str(name)
		self.conference_id = str(conference_id)
		self.creator = str(creator)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["name", "conference_id", "creator"]:
			if var == test:
				return True
			else:
				return False

class Role:
	def __init__(self, name, permissions, color="100, 100, 100", description="", _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'role'
		self.name = str(name)
		self.permissions = str(permissions)
		self.color = str(color)
		self.description = str(description)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["name", "permissions", "color", "description"]:
			if var == test:
				return True
			else:
				return False

class Attachment:
	def __init__(self, attachment_type, quoted_message="", media_link="", title="", description="", color="", image="", embed_type=0, _id=None):
		if _id:
			if not db.id_taken(_id):
				self.id = str(_id)
			else:
				raise ValueError("ID taken")
		else:
			self.id = id.assign()
		self.type = 'object'
		self.object_type = 'attachment'
		self.attachment_type = str(attachment_type)
		# Unfortunately attachments have various types, each with different fields (some required),
		# so we have to do some extra error checking here.
		if attachment_type == "quote":
			if not quoted_message:
				raise KeyError("Missing argument: quoted_message")
			else:
				self.quoted_message = str(quoted_message)
		elif attachment_type == "media":
			if not media_link:
				raise KeyError("Missing argument: media_link")
			else:
				self.media_link = str(media_link)
		elif attachment_type == "embed":
			if not title:
				raise KeyError("Missing argument: title")
			else:
				self.title = str(title)
			if embed_type == 0:
				raise KeyError("Missing argument: embed_type")
			else:
				self.embed_type = int(embed_type)
			self.description = str(description)
			self.color = str(color)
			self.image = str(image)
	def __vaild_variable__(var):
		"""
		Takes a variable name and returns True if it's a variable that can be
		given to the object. Returns False otherwise.
		"""
		for test in ["attachment_type", "quoted_message", "media_link", "title", "embed_type", "description", "color", "image"]:
			if var == test:
				return True
			else:
				return False
