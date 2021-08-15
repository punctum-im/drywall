#!/bin/sh
# Minimal startup script for drywall
export FLASK_ENV=development
export FLASK_APP=drywall.api
flask run
