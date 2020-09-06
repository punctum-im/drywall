# coding: utf-8
"""
This file contains definitions of all the API paths and is meant to be ran as a
Flask app.
"""
from drywall import objects
from drywall import settings
from drywall import db_dummy as db

from flask import Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
import drywall.api

VERSION = "0.1"

# Define our instance.
if not db.id_taken('0'):
	instance_dict = {"type": "object", "object_type": "instance", "address": settings.get('instance_domain'), "server_software": "drywall " + VERSION, "name": settings.get('instance_name'), "description": settings.get('instance_description')}
	created_instance_object = objects.make_object_from_dict(instance_dict, extend=0, ignore_nonexistent_id_in_extend=True)
	if not db.add_object(created_instance_object):
		raise ValueError('Unable to create the object')
instance = db.get_object_as_dict_by_id('0')
