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
#player
#community

def item(query, target='id', fields=['name']):
	"""Look up what an item id (or item name, etc...) refers to or a list of ids
		target specifies the field you want to query, and query is the search term
	 You can specify a list of field names to return
	 The default to return just the 'name' field
	 Or an empty list returns all fields
	"""
	output = []
	if isinstance(query, list):
		#If id is a list
		query = db.objects.find({target:{"$in":query}})
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

def avatar(query, target='avatar', fields=[]):
	"""Look up what an avatar id or a list of ids
	 target specifies the field you want to query, and query is the search term
	 You can specify a list of field names to return
	 The default to return just the 'name' field
	 Or an empty list returns all fields
	"""
	output = []
	if isinstance(query, list):
		#If id is a list
		query = db.lifelogs.find({target:{"$in":query}})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	else:
		#Single id case
		query = db.lifelogs.find({target:query})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	return(output)



def transition(query, direction='downstream', fields = []):
	'''Query the upstream or downstream items based on allowed transitions
	'''
	output = []
	#define query target and fields to return based on downstream vs. upstream option
	if direction=='downstream':
		target = 'origTarget'
		if len(fields)==0:
			fields = ['newTarget']
	elif  direction == 'upstream':
		target = 'newTarget'
		if len(fields)==0:
			fields = ['origTarget']
	#are we querying a single target or a list?
	if isinstance(query, list):
		#If id is a list
		query = db.transitions.find({target:{"$in":query}})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	else:
		#Single id case
		query = db.transitions.find({target:query})
		for q in query:
			if len(fields)==0:
				output.append(q) #Return everything if fields is empty
			else:
				output.append([q[f] for f in fields])
	return(output)


def itemVec(query):
	"""Look up item embeddings for a specific item id or list of items ids
	"""
	output = []
	if isinstance(query, list):
		#If id is a list
		query = db.item_embeddings.find({'item':{"$in":query}})
		for q in query:
				output.append(q['vec']) 
	else:
		#Single id case
		query = db.item_embeddings.find({'item':query})
		for q in query:
			output.append(q['vec']) 
	return(output)

def avatarVec(query):
	"""Look up avatar embeddings for a specific avatar id or list of avatar ids
	"""
	output = []
	if isinstance(query, list):
		#If id is a list
		query = db.avatar_embeddings.find({'avatar':{"$in":query}})
		for q in query:
				output.append(q['vec']) 
	else:
		#Single id case
		query = db.avatar_embeddings.find({'avatar':query})
		for q in query:
			output.append(q['vec']) 
	return(output)
