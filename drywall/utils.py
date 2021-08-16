# encoding: utf-8
"""
Common utilities used in various modules.
"""

def missing_key_from_list_in_dict(test_list, test_dict):
	"""
	Takes a list and a dictionary and checks if all keys in the list are present
	in the dictionary. Raises a KeyError with the missing key if found, returns
	False otherwise.
	"""
	for key in test_list:
		if key not in test_dict:
			raise KeyError(key)
	return False

def any_key_from_list_in_dict(test_list, test_dict):
	"""
	Takes a list and a dictionary and checks if any of the keys from the list are
	present in the dict. Raises a KeyError with the key if found, returns False
	otherwise.
	"""
	for key in test_list:
		if key in test_dict:
			raise KeyError(key)
	return False

def validate_dict(dict_to_validate, valid_keys):
	"""
	Takes a dict and a list with valid key names and removes all invalid keys
	from the given dict. Returns the validated dict.
	"""
	validated_dict = dict_to_validate.copy()
	for key in dict_to_validate.keys():
		if key not in valid_keys:
			del validated_dict[key]
	return validated_dict

def fill_dict_with_dummy_values(fill_values, target_dict, dummy=False):
	"""
	Takes a list of value names and a dict and returns the dict with
	the selected values replaced with a dummy.
	"""
	ret_dict = target_dict.copy()
	for val in fill_values:
		if not val in ret_dict:
			ret_dict[val] = dummy
	return ret_dict

def replace_values_in_dict_by_value(replace_values, target_dict):
	"""
	Takes a dict with value-replacement pairs and replaces all values in the
	target dict with the replacement. Returns the resulting dict.
	"""
	ret_dict = target_dict.copy()
	for val, replacement in replace_values.items():
		for key, dict_val in target_dict.items():
			if str(dict_val) == val:
				ret_dict[key] = replacement
	return ret_dict

def powers_to_list(x):
	"""
	Takes a value that's a sum of powers of 2 and breaks it down to a list
	of powers of 2.

	(Shamelessly stolen from https://stackoverflow.com/a/30227161.)
	"""
	powers = []
	i = 1
	while i <= x:
		if i & x:
			powers.append(i)
		i <<= 1
	return powers

