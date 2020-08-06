# coding: utf-8
# id.py - contains functions related to assigning, checking, handling
#         and checking IDs.

import uuid

def assign():
	"""
	Assigns an ID. Returns the ID as a string.

	We currently use UUID4 to generate IDs, which *should* help prevent
	collisions. In the future, this function can be extended to make use of
	an ID server with snowflake IDs, but this is currently unnecesary.

	Optionally, if we want to make *absolutely* sure there will be no
	collisions, we could add a function that check for the ID's presence
	in the database, but this would slow everything down.
	"""
	id=uuid.uuid4()
	return str(id)
