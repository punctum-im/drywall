# coding: utf-8
"""
This file contains definitions of all the API paths and is meant to be ran as a
Flask app.
"""
import objects, id, settings
import db_dummy as db
import sys
from flask import Flask, Response, request
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
version = "0.1"

# Define our instance.
if not db.id_taken('0'):
	instance_object = objects.Instance(settings.get('instance_domain'), "drywall " + version, settings.get('instance_name'), settings.get('instance_description'), _id="0")
	db.add_object(instance_object)
instance = db.get_object_as_dict_by_id('0')

@app.route('/api/v1/instance')
def api_return_instance():
	return db.get_object_as_dict_by_id('0')

@app.route('/api/v1/id/<id>')
def api_return_object_by_id(id):
	object_dict = db.get_object_as_dict_by_id(str(id))
	if object_dict:
		return object_dict
	else:
		return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')

@app.route('/api/v1/id/<id>/type')
def api_return_object_type_by_id(id):
	try:
		object_dict = db.get_object_as_dict_by_id(str(id))
	except KeyError:
		return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')

	ret_dict = {}
	for key, value in object_dict.items():
		if key == "id" or key == "type" or key == "object_type" or key == "channel_type" or key == "attachment_type" or key == "embed_type":
			ret_dict[key] = value
	return ret_dict

@app.route('/api/v1/stash/request')
def api_return_stash():
	if not request.json:
		return Response('{"error": "No input, or content type is not application/json"}', status=400, mimetype='application/json')
	else:
		if request.json['id_list']:
			id_list = request.json['id_list']
		else:
			return Response('{"error": "Malformed JSON data (there should be a key called id_list containing a list of IDs)"}', status=400, mimetype='application/json')
	try:
		stash_dict = db.create_stash(id_list)
	except ValueError:
		return Response('{"error": "Too much IDs or no IDs provided (max. 100 IDs)"}', status=400, mimetype='application/json')
	except KeyError:
		return Response('{"error": "' + str(sys.exc_info()[1]) + '"}', status=404, mimetype='application/json')
	return stash_dict

@app.route('/api/v1/accounts/<id>')
def api_return_account_by_id(id):
	try:
		object_dict = api_return_object_by_id(id)
	except KeyError:
		return Response('{"error": "No object with given ID found"}', status=404, mimetype='application/json')

	if object_dict['object_type'] == "account":
		return object_dict
	else:
		return Response('{"error": "Provided ID does not belong to an account."}', status=400, mimetype='application/json')
