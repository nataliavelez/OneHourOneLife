#Upload NMF results
#Charley Wu, Jun 2021
import pymongo, os, bson, json, glob, pickle, gridfs, sys, argparse, pickle
from collections import Counter
from sklearn.preprocessing import normalize
from random import sample
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.sparse import csr_matrix, random
from bson.binary import Binary
from os.path import join as opj
from sklearn.decomposition import NMF
from sklearn.decomposition import PCA
from sklearn import metrics

#Import utilities
sys.path.append("..")
import dbfind #db search tool
import utils
db = dbfind.db 

dims = 10

############################################################
#Cleaned matrix
############################################################

jobMatrix = 'cleaned'
#Load cleaned matrix. This takes about 30 seconds
mat_id = list(db.cleaned_job_matrix.files.find())[db.cleaned_job_matrix.files.find().count()-1]['_id'] #get id
fs = gridfs.GridFS(db, collection='cleaned_job_matrix') 
mat_bin = fs.get(mat_id) #extract binary
mat_dict = pickle.load(mat_bin, encoding='latin1')
jobMatrixCleaned = mat_dict['mat']
itemIds = mat_dict['items']
avatarIds = mat_dict['avatars']
print('Loaded cleaned job matrix:')
print(jobMatrixCleaned.shape)
dat = jobMatrixCleaned


print("\n\n Starting analysis: %s %i \n\n" % (jobMatrix,dims))
#Fit model
#dat = dat[1:10000,:] #debug for testing on smaller data set=
model = NMF(n_components=dims, init='random', random_state=0).fit(dat)
#VarExplained = metrics.explained_variance_score(dat.toarray(), model.inverse_transform(model.transform(dat))) #variance explained
W = model.transform(dat) #Avatar embeddings
H = model.components_ #item embeddings

#Save outputs
Hdict = [{'item':itemIds[i], 'vec':H[:,i].tolist()} for i in range(len(itemIds))] #Item embeddings
Wdict = [{'avatar':avatarIds[i], 'vec':W[i,:].tolist()} for i in range(len(avatarIds))] #avatar embeddings

#Wipe existing conditions!!!!
db.item_embeddings.drop()
db.avatar_embeddings.drop()

#insert new data
db.item_embeddings.insert_many(Hdict)
db.avatar_embeddings.insert_many(Wdict)

#Which items most strongly defined each component?
filepath = 'jobspace/labels/%s/%i.txt' %  (jobMatrix,dims)
with open(filepath, 'w') as outfile:
    for C in range(H.shape[0]):
        comp = H[C,] #component
        items = comp.argsort()[-10:][::-1]#sort by weight; select the top 10 items
        outfile.write('%i\n' % C)
        for item in items:
            try:
                objname = dbfind.item(itemIds[item])[0][0] #relate to item id and then look up
                weight = str(comp[item])
                outfile.write(' : '.join([objname, weight])+'\n')
            except:
                outfile.write(' : '.join([str(int(item)), str(comp[item])])+'\n')
        outfile.write('\n')


############################################################
#Random Matrix
############################################################
jobMatrix = 'random'
#Load random matrix. This takes about 30 seconds
mat_id = list(db.randomized_job_matrix.files.find())[db.randomized_job_matrix.files.find().count()-1]['_id'] #get id
fs = gridfs.GridFS(db, collection='randomized_job_matrix') 
mat_bin = fs.get(mat_id) #extract binary
mat_dict = pickle.load(mat_bin, encoding='latin1')
randomMat = mat_dict['mat']
itemIds = mat_dict['items']
avatarIds = mat_dict['avatars']
print('Loaded random matrix:')
print(randomMat.shape)
dat = randomMat


print("\n\n Starting analysis: %s %i \n\n" % (jobMatrix,dims))
#Fit model
#dat = dat[1:10000,:] #debug for testing on smaller data set=
model = NMF(n_components=dims, init='random', random_state=0).fit(dat)
#VarExplained = metrics.explained_variance_score(dat.toarray(), model.inverse_transform(model.transform(dat))) #variance explained
W = model.transform(dat) #Avatar embeddings
H = model.components_ #item embeddings

#Save outputs
Hdict = [{'item':itemIds[i], 'vec':H[:,i].tolist()} for i in range(len(itemIds))] #Item embeddings
Wdict = [{'avatar':avatarIds[i], 'vec':W[i,:].tolist()} for i in range(len(avatarIds))] #avatar embeddings

#Wipe existing conditions!!!!
db.random_item_embeddings.drop()
db.random_avatar_embeddings.drop()

#insert new data
db.random_item_embeddings.insert_many(Hdict)
db.random_avatar_embeddings.insert_many(Wdict)

#Which items most strongly defined each component?
filepath = 'jobspace/labels/%s/%i.txt' %  (jobMatrix,dims)
with open(filepath, 'w') as outfile:
    for C in range(H.shape[0]):
        comp = H[C,] #component
        items = comp.argsort()[-10:][::-1]#sort by weight; select the top 10 items
        outfile.write('%i\n' % C)
        for item in items:
            try:
                objname = dbfind.item(itemIds[item])[0][0] #relate to item id and then look up
                weight = str(comp[item])
                outfile.write(' : '.join([objname, weight])+'\n')
            except:
                outfile.write(' : '.join([str(int(item)), str(comp[item])])+'\n')
        outfile.write('\n')
    