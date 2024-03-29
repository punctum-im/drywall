# coding: utf-8
"""
This file contains definitions of all the API paths and is meant to be ran as a
Flask app.
"""
from drywall import config

from flask import Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = config.get("secret")
