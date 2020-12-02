# encoding: utf-8
"""
SQLite database backend using the sqlite3 module.
"""
import sqlite3
from drywall import settings
from drywall import objects

default_table_vars = "id PRIMARY KEY, object_type NOT NULL"
user_table_vars = "username UNIQUE, email PRIMARY KEY, password NOT NULL, account_id UNIQUE"
if settings.get('sqlite_db_path'):
	db_path = settings.get('sqlite_db_path')
else:
	db_path = 'drywall.db'

conn = sqlite3.connect(db_path)

if not conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='objects';").fetchone():
	print('[db_sqlite] Initializing tables...')
	conn.execute("CREATE TABLE IF NOT EXISTS objects ( " + default_table_vars + " );")
	conn.execute("CREATE TABLE IF NOT EXISTS users ( " + user_table_vars + " );")
	for table_name in ['instance', 'account', 'conference', 'channel', 'message', 'role', 'invite', 'conference_member']:
		print('[db_sqlite] Adding table ' + table_name + "...")
		columns = objects.default_nonrewritable_keys + objects.get_object_class_by_type(table_name).valid_keys
		columns = str(columns)[1:-1]
		conn.execute("CREATE TABLE IF NOT EXISTS " + table_name + " ( " + columns + " );")
	conn.commit()
	print('[db_sqlite] Done.')

def manipulate_object(id=None, object=None):
	"""
	Usage:
	    manipulate_object(object)
	    # ...or...
	    manipulate_object(object, id)
	Takes an object and optionally an ID, then replaces the object in the database
	with the provided object. If the object does not exist, it will be created.
	Returns the ID of the object.

	If you want to add an object to the database, use the add_object function,
	as it checks if the ID is already present in the database and errors out
	if it is.

	If you want to replace an object with a certain ID with another object,
	use the push_object function, as it errors out when the ID does not exist.

	Arguments:
	    object - object that will be pushed
	    id (optional) - ID to manipulate; if not passed it will be taken from
	                    the object
	"""
	conn = sqlite3.connect(db_path)

	if not id:
		id = vars(object)['id']
	object_dict = object.__dict__
	object_type = object_dict['object_type']

	for key, value in object_dict.items():
		conn.execute("UPDATE " + object_type + " set " + key + ' = "' + str(value) + '" where ID = "' + id + '"')

	conn.execute('UPDATE objects SET object_type = "' + object_type + '" WHERE id = "%s";' % (id))

	conn.commit()
	return object_dict

def add_object(object):
	"""
	Takes an object and inserts it into the database. Returns the inserted object.
	Returns False if the ID is already taken.
	"""
	conn = sqlite3.connect(db_path)

	object_dict = object.__dict__
	object_id = object_dict['id']
	if id_taken(object_id):
		return False
	object_type = object_dict['object_type']

	iter_list = list(object_dict.keys()).copy()
	for key in iter_list:
		if not key in objects.get_object_class_by_type(object_type).valid_keys and not key in objects.default_nonrewritable_keys:
			del object_dict[key]

	# NOTE: This saves every value as a string.
	columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in object_dict.keys())
	values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in object_dict.values())
	sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (object_type, columns, values)
	conn.execute(sql)

	conn.execute("INSERT INTO objects (id, object_type) VALUES (?, ?)",
	             (object_id, object_type))

	conn.commit()
	manipulate_object(id=object_id, object=object)

	return object_dict

def push_object(id, object):
	"""
	Takes an ID and an object, then overwrites the object with said ID in the
	database. Returns the pushed object.
	Returns False if the ID does not exist.
	"""
	if id_taken(str(id)):
		return manipulate_object(id=id, object=object)
	else:
		return False

def delete_object(id):
	"""
	Takes an object ID and deletes the object with the provided ID from the
	database. Returns the ID of the deleted object.
	Returns False if the ID does not exist.
	"""
	conn = sqlite3.connect(db_path)

	table_query = conn.execute('SELECT object_type FROM objects WHERE id = "%s";' % (id))
	table = table_query.fetchone()
	if not table:
		return False
	table = table[0]

	conn.execute('DELETE FROM objects WHERE id = "%s";' % (id))
	conn.execute('DELETE FROM ' + table + ' WHERE id = "%s";' % (id))
	conn.commit()
	return(id)

def id_taken(id):
	"""
	Takes an ID and returns True or False based on whether the ID was found in
	the database.
	"""
	conn = sqlite3.connect(db_path)

	tested_id = conn.execute('SELECT id FROM objects WHERE id = "%s";' % (id))
	tested_id_fetch = tested_id.fetchone()
	if tested_id_fetch:
		return True
	else:
		return False

def get_object_as_dict_by_id(id):
	"""
	Takes an object ID and returns a dict containing the object's content.
	Returns None if the ID is not found in the database.
	"""
	conn = sqlite3.connect(db_path)

	table_query = conn.execute('SELECT object_type FROM objects WHERE id = "%s";' % (id))
	table = table_query.fetchone()
	if not table:
		return None
	table = table[0]

	object_type_class = objects.get_object_class_by_type(table)

	conn.row_factory = sqlite3.Row

	object_query = conn.execute('SELECT * FROM %s WHERE id = "%s"' % (table, id))
	object_direct_result = dict(object_query.fetchone())

	object_result = object_direct_result.copy()
	for key, value in object_direct_result.items():
		if not value:
			del object_result[key]
			continue
		if not key == "id" and not key == "type" and not key == "object_type":
			key_type = object_type_class.key_types[key]
			if key_type == "number":
				object_result[key] = int(value)
			elif key_type == "list" or key_type == "id_list":
				object_result[key] = list(value[1:-1])

	return object_result

def get_object_by_key_value_pair(key_value_dict, limit_objects=False):
	"""
	Takes a dict with key and value pairs and returns objects that match
	(contain) all key-value pairs. Returns a list with dicts.

	Optional arguments:
	  - limit_objects (default: False) - If set to a number, limits the
	                                     search to the given amount of
	                                     objects.
	"""
	conn = sqlite3.connect(db_path)

	query_params = None
	for key, value in key_value_dict.items():
		if not query_params:
			query_params = key + ' = "' + value + '"'
		else:
			query_params = query_params + " AND " + key + ' = "' + value + '"'

	try:
		table = key_value_dict['object_type']
	except KeyError:
		raise KeyError("Could not find object_type key in provided dict")

	object_type_class = objects.get_object_class_by_type(table)

	conn.row_factory = sqlite3.Row

	object_query = conn.execute('SELECT * FROM %s WHERE %s' % (table, query_params))
	object_direct_result = []
	for row in object_query.fetchall():
		object_direct_result.append(dict(row))

	object_match = []
	for object in object_direct_result:
		object_result = object.copy()
		for key, value in object.items():
			if not value:
				del object_result[key]
				continue
			if not key == "id" and not key == "type" and not key == "object_type":
				key_type = object_type_class.key_types[key]
				if key_type == "number":
					object_result[key] = int(value)
				elif key_type == "list" or key_type == "id_list":
					object_result[key] = list(value[1:-1])
		object_match.append(object_result)

	if object_match:
		if limit_objects:
			return object_match[:limit_objects]
		else:
			return object_match
	return None

def get_user_by_email(email):
	"""
	Returns an user's username on the server by email. If not found, returns
	None.
	"""
	email_query = conn.execute('SELECT * FROM users WHERE email = "%s";' % (email))
	conn.commit()
	if email_query:
		return email_query.fetchone()
	return None

def quote(string):
	"""Surrounds value in quotes. Returns surrounded string."""
	return '"' + string + '"'

def add_user(user_dict):
	"""Adds a new user to the database."""
	query = """INSERT INTO users (username, email, password, account_id)
	           VALUES (%s, %s, %s, %s)""" % (quote(user_dict['username']),
	quote(user_dict['email']), quote(user_dict['password']),
	quote(user_dict['account_id']))
	conn.execute(query)
	conn.commit()
	return user_dict

def remove_user(email):
	"""Removes an user"""
	raise Exception('stub')
