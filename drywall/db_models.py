# The following tables have been generated by alchemify.py from the
# drywall utilities. For more information, see the documentation:
# https://punctum-im.github.io/drywall/dev/alchemify

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String, DateTime, Boolean, SmallInteger, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy_serializer import SerializerMixin
import datetime

Base = declarative_base()

class CustomSerializerMixin(SerializerMixin):
	# TODO: Ideally we'd just set datetime_format to None to set it to isoformat,
	#       but that leaves out the +00:00 suffix, because we're missing
	#       ".replace(tzinfo=datetime.timezone.utc)" from the call. We could
	#       set it manually, but that's less efficient than just hardcoding it
	#       here. We force UTC as the timezone, so it shouldn't cause any issues,
	#       but maybe we can negotiate a feature for this with upstream?
	tzinfo = datetime.timezone.utc
	datetime_format = '%Y-%m-%dT%H:%M:%S.%f+00:00'

# Main object lookup table
class Objects(Base):
	__tablename__ = 'objects'

	id = Column(String(255), primary_key=True)
	object_type = Column(String(255), nullable=False)

# instance
class Instance(Base, CustomSerializerMixin):
	__tablename__ = 'instance'

	id = Column('id', String(255), primary_key=True)
	address = Column(Text, nullable=False)
	server_software = Column(Text, nullable=False)
	name = Column(Text, nullable=False)
	description = Column(Text)

# account
class Account(Base, CustomSerializerMixin):
	__tablename__ = 'account'

	id = Column('id', String(255), primary_key=True)
	username = Column(Text, nullable=False, unique=True)
	short_status = Column(Integer, nullable=False)
	status = Column(Text)
	bio = Column(Text)
	index_user = Column(Boolean, default=False)
	email = Column(Text)
	bot = Column(Boolean, default=False)
	friends = Column(postgresql.ARRAY(String(255)))
	blocklist = Column(postgresql.ARRAY(String(255)))

# conference
class Conference(Base, CustomSerializerMixin):
	__tablename__ = 'conference'

	id = Column('id', String(255), primary_key=True)
	name = Column(Text, nullable=False)
	description = Column(Text)
	icon = Column(Text, nullable=False)
	owner = Column(String(255), ForeignKey('account.id'), nullable=False)
	index_conference = Column(Boolean, default=False)
	permissions = Column(SmallInteger, nullable=False)
	creation_date = Column(DateTime, nullable=False)
	channels = Column(postgresql.ARRAY(String(255)))
	users = Column(postgresql.ARRAY(String(255)))
	roles = Column(postgresql.ARRAY(String(255)))

# conference_member
class ConferenceMember(Base, CustomSerializerMixin):
	__tablename__ = 'conference_member'

	id = Column('id', String(255), primary_key=True)
	user_id = Column(String(255), ForeignKey('account.id'), nullable=False)
	nickname = Column(Text)
	parent_conference = Column(String(255), ForeignKey('conference.id'), nullable=False)
	roles = Column(postgresql.ARRAY(String(255)))
	permissions = Column(SmallInteger, nullable=False)
	banned = Column(Boolean, default=False)

# channel
class Channel(Base, CustomSerializerMixin):
	__tablename__ = 'channel'

	id = Column('id', String(255), primary_key=True)
	name = Column(Text, nullable=False)
	permissions = Column(SmallInteger, nullable=False)
	channel_type = Column(Text, nullable=False)
	parent_conference = Column(String(255), ForeignKey('conference.id'))
	members = Column(postgresql.ARRAY(String(255)))
	icon = Column(Text)
	description = Column(Text)

# message
class Message(Base, CustomSerializerMixin):
	__tablename__ = 'message'

	id = Column('id', String(255), primary_key=True)
	content = Column(Text, nullable=False)
	parent_channel = Column(String(255), ForeignKey('channel.id'), nullable=False)
	author = Column(String(255), ForeignKey('account.id'), nullable=False)
	post_date = Column(DateTime, nullable=False)
	edit_date = Column(DateTime)
	edited = Column(Boolean, nullable=False, default=False)
	attached_files = Column(postgresql.ARRAY(String(255)))
	reactions = Column(postgresql.ARRAY(String(255)))
	reply_to = Column(String(255), ForeignKey('message.id'))
	replies = Column(postgresql.ARRAY(String(255)))

# invite
class Invite(Base, CustomSerializerMixin):
	__tablename__ = 'invite'

	id = Column('id', String(255), primary_key=True)
	code = Column(Text, nullable=False, unique=True)
	conference_id = Column(String(255), ForeignKey('conference.id'), nullable=False)
	creator = Column(String(255), ForeignKey('account.id'), nullable=False)

# role
class Role(Base, CustomSerializerMixin):
	__tablename__ = 'role'

	id = Column('id', String(255), primary_key=True)
	name = Column(Text, nullable=False)
	permissions = Column(SmallInteger, nullable=False)
	color = Column(Text, nullable=False)
	description = Column(Text)
	parent_conference = Column(String(255), ForeignKey('conference.id'), nullable=False)

# report
class Report(Base, CustomSerializerMixin):
	__tablename__ = 'report'

	id = Column('id', String(255), primary_key=True)
	target = Column(String(255), ForeignKey('objects.id', ondelete="CASCADE"), nullable=False)
	note = Column(Text)
	submission_date = Column(DateTime, nullable=False)

# User
class User(Base, SerializerMixin):
	__tablename__ = "users"

	account_id = Column(String(255), nullable=False, unique=True)
	email = Column(String(255), primary_key=True)
	username = Column(String(255), nullable=False, unique=True)
	password = Column(Text, nullable=False)

# Helper functions

def object_type_to_model(object_type):
	"""
	Takes an object_type string and returns the ORM model class for that
	object type.
	"""

	if object_type == 'instance':
		return Instance
	elif object_type == 'account':
		return Account
	elif object_type == 'conference':
		return Conference
	elif object_type == 'conference_member':
		return ConferenceMember
	elif object_type == 'channel':
		return Channel
	elif object_type == 'message':
		return Message
	elif object_type == 'invite':
		return Invite
	elif object_type == 'role':
		return Role
	elif object_type == 'report':
		return Report
	else:
		raise TypeError('Incorrect object_type')

# End of auto-generated tables
