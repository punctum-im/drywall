#!/bin/sh
# Minimal startup script for drywall
export FLASK_ENV=development
export FLASK_APP=drywall.api
export AUTHLIB_INSECURE_TRANSPORT=true
flask run
