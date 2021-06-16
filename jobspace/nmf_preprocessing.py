#Run NMF
#Charley Wu, April 2021
import pymongo
import os
import bson
import json
import glob
import pickle
import gridfs
import sys
from collections import Counter
from sklearn.preprocessing import normalize
from random import sample
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.sparse import csr_matrix
from bson.binary import Binary
from os.path import join as opj
from sklearn.decomposition import NMF
from sklearn.decomposition import PCA
from sklearn import metrics

sys.path.append("..")
import dbfind #db search tool
import utils
db = dbfind.db 
print(db)
print(db.list_collection_names())


#### Load Data ########

# Get pointer from activity_matrix.files
activity_file = list(db.activity_matrix.files.find())
activity_id = activity_file[0]['_id']
print('File metadata:')
print(activity_file)

#Load sparse matrix
fs = gridfs.GridFS(db, collection='activity_matrix')
activity_bin = fs.get(activity_id)
activity_mtx = pickle.load(activity_bin, encoding='latin1')
print('Loaded activity matrix:')
print(activity_mtx)

#Get item and avatar ids
itemIds = db.activity_labels.find_one()['items'] #item ids for each column of the sparse activity matrix
avatarIds = db.activity_labels.find_one()['avatars'] #avatar ids for each row of the sparse activity matrix

#### Preprocessing ########

#exclusion list for players who didn't make it out of infancy or disconnected
exclusionIds = [q['avatar'] for q in db.lifelogs.find({"$or":[ {"age":{"$lt":4}}, {"cause_of_death":'disconnected'}]}, {'avatar'})]
len(exclusionIds) #note, not all overlapping with the ids in the activity matrix, since many of these never generated any map change data

#Find the ids (rows in sparse activity_mtx) to delete
deleteIds = np.nonzero(np.in1d(avatarIds,exclusionIds))[0]
len(deleteIds)

#Delete excluded avatars
activity_mtx = utils.delete_from_csr(activity_mtx, row_indices = deleteIds.tolist())
for index in sorted(deleteIds.tolist(), reverse=True):
    del avatarIds[index]

#Check that all data is the right shape
print(activity_mtx.shape)
print(len(avatarIds))

#Now delete items with no interactions (if any)
deleteIds = np.where(activity_mtx.sum(axis = 0)==0)[1]
len(deleteIds)

#Delete excluded items
activity_mtx = utils.delete_from_csr(activity_mtx, col_indices = deleteIds.tolist())
for index in sorted(deleteIds.tolist(), reverse=True):
    del itemIds[index]

#Final shape
print(activity_mtx.shape)
print(len(itemIds))

#pre-processing finished
jobMatrixCleaned = activity_mtx

cleanedDict = {'mat' : jobMatrixCleaned, 
            'items' : itemIds,
            'avatars': avatarIds}

#Save on database
print('Saving cleaned matrix to database')
db.cleaned_job_matrix.drop() #drop previous collection
fs = gridfs.GridFS(db, collection='cleaned_job_matrix')
fs.put(Binary(pickle.dumps(cleanedDict, protocol=2), subtype=128))


#### Construct Randomized Matrix ########
print('Saving building random matrix')
shuffledMat = jobMatrixCleaned #copy over
index = np.arange(np.shape(jobMatrixCleaned)[1]) #column indices
counter = 0
for row in np.arange(np.shape(jobMatrixCleaned)[0]):
   np.random.shuffle(index) #shuffle column indices
   shuffledMat[row,:] = jobMatrixCleaned[row,index]
   print(counter, end='')

print('')

randomDict = {'mat' : shuffledMat, 
            'items' : itemIds,
            'avatars': avatarIds}

#Save on database
print('Saving random matrix to database')
db.randomized_job_matrix.drop() #drop previous collection
fs = gridfs.GridFS(db, collection='randomized_job_matrix')
fs.put(Binary(pickle.dumps(randomDict, protocol=2), subtype=128))

#### TF-IDF normalization ########
print('Starting TFIDF normalization')
#Term frequency: let's use augmented frequency, which prevents a bias towards longer documents (i.e., players who have many item interactions)
#Each row vector v undergoes the following transformation:  tf(v) = 0.5 + (0.5*v)/(max(v))
TF = jobMatrixCleaned.toarray() #convert to array
TF = TF/jobMatrixCleaned.max(axis=1).toarray() #divide by max
TF *= 0.5 
TF += 0.5


#Inverse document frequency
#np.log(sum(itemVec)/len(itemVec[itemVec>0]))
IDFcolsums = jobMatrixCleaned.sum(axis = 0)
nonNegCounts = Counter(jobMatrixCleaned.nonzero()[1]) #Count non-negative elements in each column
nonNeg = np.ones(jobMatrixCleaned.shape[1])
nonNeg[list(nonNegCounts.keys())] = list(nonNegCounts.values())
IDF = np.log(IDFcolsums / nonNeg)

tfIdfMat = np.multiply(TF, IDF)

tfidfJobMatrix = jobMatrixCleaned.multiply(tfIdfMat)  #now compute tfidf

tfidfJobMatrix

#Normalized rows
tfidfJobMatrixNormalized = normalize(tfidfJobMatrix, norm='l1', axis=1)

tfidfDict = {'mat' : tfidfJobMatrixNormalized, 
            'items' : itemIds,
            'avatars': avatarIds}

#Save on database
print('saving TFIDF matrix')
db.tfidf_matrix.drop() #drop previous collection
fs = gridfs.GridFS(db, collection='tfidf_matrix')
fs.put(Binary(pickle.dumps(tfidfDict, protocol=2), subtype=128))



