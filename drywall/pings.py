# coding: utf-8
"""
This file defines pings.
"""

import simplejson as json
from flask import Response

def response_from_error(error_code, error_message=None):
	"""
	Creates a Flask Response object for the specified error code.

	Optional variables:
	  - error_message - custom error message (if none provided, a default
	                    will be used
	"""
	error = Error(error_code, error_message).__dict__
	error_response_code = error['response_code']
	return Response(json.dumps(error), status=error_response_code, mimetype='application/json')

class Error:
	def __init__(self, error_code, error_message=None):
		self.type = "ping"
		self.ping_type = "error"
		self.error_code = error_code
		# Generic error messages (can be overriden if needed)
		if error_code == 0:
			self.error = "No error"
			self.response_code = 200
		elif error_code == 1:
			self.error = "Server-side error"
			self.response_code = 500
		elif error_code == 2:
			self.error = "No data provided, or Content-Type is not application/json"
			self.response_code = 400
		elif error_code == 3:
			self.error = "Not permitted to access object"
			self.response_code = 403
		elif error_code == 4:
			self.error = "Object with given ID not found"
			self.response_code = 404
		elif error_code == 5:
			self.error = "Object type not supported by endpoint"
			self.response_code = 400
		elif error_code == 6:
			self.error = "Attempted to change non-rewritable variable"
			self.response_code = 400
		elif error_code == 7:
			self.error = "Missing required variable"
			self.response_code = 400
		elif error_code == 8:
			self.error = "Object does not belong to object"
			self.response_code = 400
		elif error_code == 9:
			self.error = "Object with ID provided in a variable that takes an ID does not exist"
			self.response_code = 404
		elif error_code == 10:
			self.error = "Object with the ID provided in a variable that takes an ID is not of the correct type for this variable"
			self.response_code = 400
		elif error_code == 11:
			self.error = "Too many objects provided"
			self.response_code = 400
		else:
			raise TypeError("Wrong error_code")

		if error_message:
			self.error = str(error_message)
