# coding: utf-8
"""
Tests the database dummy.
"""
import db_dummy as db
import id
import objects

print('Testing db.add_object...')
print(db.add_object.__doc__)
print(db.add_object(objects.Invite(name="a", conference_id="b", creator="c")))
find = db.add_object(objects.Invite(name="d", conference_id="e", creator="f"))
print(find)

print('Database contents:')
print(db.db)

print('Testing db.get_object_as_dict_by_id...')
print(db.get_object_as_dict_by_id.__doc__)
print(db.get_object_as_dict_by_id(find))

print('Testing db.push_object...')
print(db.push_object.__doc__)
print(db.push_object(find, objects.Invite(name="x", conference_id="y", creator="z", _id=find)))
print("New object's contents:")
print(db.get_object_as_dict_by_id(find))
