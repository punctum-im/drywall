# coding: utf-8
"""
This file contains definitions of all the API paths and is meant to be ran as a
Flask app.
"""
import simplejson as json

from flask import Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
import drywall.api
