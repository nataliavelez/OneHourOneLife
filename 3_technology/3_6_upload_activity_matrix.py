#!/usr/bin/env python
# coding: utf-8

# # Upload activity matrix
# Natalia Vélez, April 2021
# 
# In this notebook, we'll create four new collections in the OHOL database:
# * `activity_matrix.{files, chunks}`: Full activity matrix stored in GridFS 
# * `activity_vectors`: Activity matrix split into vectors by avatar
# * `activity_labels`: Contains list of item,avatar labels

import pymongo, sys, bson, pickle
import numpy as np
import gridfs
from tqdm import notebook


# Load data:
item_labels = np.loadtxt('outputs/activity_features.txt', dtype=np.int).tolist()
avatar_labels = np.loadtxt('outputs/activity_agg/avatarIDs.txt', dtype=np.int).tolist()
activity_matrix = np.loadtxt('outputs/activity_agg/activity_matrix.txt', dtype=np.int)

print('Item labels: %s' % len(item_labels))
print('Avatar labels: %s' % len(avatar_labels))
print('Activity matrix: %s' % str(activity_matrix.shape))


# ## Upload to database

# Connect:
keyfile = '../6_database/credentials.key'
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
db = myclient.ohol

print(db)
print(db.list_collection_names())


# Upload labels:
print('Uploading avatar and item labels')
print(db.activity_labels.drop()) # Drop old collection
labels = {'avatars': avatar_labels, 'items': item_labels}
labels_collection = db.activity_labels
labels_collection.insert(labels)

# Upload whole matrix through GridFS:
# print('Uploading whole activity matrix')
# print(db.activity_matrix.files.drop()) # Drop old collection
# print(db.activity_matrix.chunks.drop())
# fs = gridfs.GridFS(db, collection='activity_matrix')
# mtx_bin = bson.binary.Binary(pickle.dumps(activity_matrix, protocol=2), subtype=128)
# mtx_fs = fs.put(mtx_bin, filename='activity_matrix')
# del mtx_bin # free up space

# Upload each row separately:
print('Uploading activity vectors piecemeal')
print(db.activity_vectors.drop()) # Drop old collection
vectors_collection = db.activity_vectors
for avatar,vec in notebook.tqdm(zip(avatar_labels, activity_matrix), total=len(avatar_labels)):
	vectors_collection.insert_one({'avatar': avatar, 'activity': vec.tolist()})
