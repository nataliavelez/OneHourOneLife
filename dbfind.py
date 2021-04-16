# Helper functions to make database queries easier
# Charley Wu, April 2021
import pymongo
import os
from pathlib import Path

keypath = (Path(__file__).parent / "6_database/").resolve()
keyfile = os.path.join(keypath,'credentials.key')
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
db = myclient.ohol

#TODO:
#avatar
#player
#community

def item(query, target='id', fields=['name']):
	"""Look up what an item id (or item name, etc...) refers to or a list of ids
		target specifies the field you want to query, and query is the target
	 You can specify a list of field names to return
	 The default to return just the 'name' field
	 Or an empty list returns all fields
	"""
	output = []
	if isinstance(query, list):
		#If id is a list
		query = db.objects.find({target:query})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	else:
		#Single id case
		query = db.objects.find({target:query})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	return(output)

