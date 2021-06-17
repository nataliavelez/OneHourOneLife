#Run NMF validation
#Charley Wu, Mau 2021
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

#Log space integers
def gen_log_space(limit, n):
    result = [1]
    if n>1:  # just a check to avoid ZeroDivisionError
        ratio = (float(limit)/result[-1]) ** (1.0/(n-len(result)))
    while len(result)<n:
        next_value = result[-1]*ratio
        if next_value - result[-1] >= 1:
            # safe zone. next_value will be a different integer
            result.append(next_value)
        else:
            # problem! same integer. we need to find next_value by artificially incrementing previous value
            result.append(result[-1]+1)
            # recalculate the ratio so that the remaining values will scale correctly
            ratio = (float(limit)/result[-1]) ** (1.0/(n-len(result)))
    # round, re-adjust to 0 indexing (i.e. minus 1) and return np.uint64 array
    return np.array(list(map(lambda x: round(x)-1, result)), dtype=np.uint64)

dimArray = gen_log_space(3043,22)[2:] #remove the first two value, so we start on 2


#Loop through different inputs
for jobMatrix in ('cleaned', 'tfidf', 'random'):
    #Which job matrix to use?
    if jobMatrix == 'cleaned':
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
    elif jobMatrix == 'tfidf':
        #Load tfidf matrix. This takes about 30 seconds
        mat_id = list(db.tfidf_matrix.files.find())[db.tfidf_matrix.files.find().count()-1]['_id'] #get id
        fs = gridfs.GridFS(db, collection='tfidf_matrix') 
        mat_bin = fs.get(mat_id) #extract binary
        mat_dict = pickle.load(mat_bin, encoding='latin1')
        tfidfJobMatrixNormalized = mat_dict['mat']
        itemIds = mat_dict['items']
        avatarIds = mat_dict['avatars']
        print('Loaded tfidf matrix:')
        print(tfidfJobMatrixNormalized.shape)
        dat = tfidfJobMatrixNormalized
    elif jobMatrix == 'random':
        #Load random matrix. This takes about 30 seconds
        mat_id = list(db.cleaned_job_matrix.files.find())[db.randomized_job_matrix.files.find().count()-1]['_id'] #get id
        fs = gridfs.GridFS(db, collection='randomized_job_matrix') 
        mat_bin = fs.get(mat_id) #extract binary
        mat_dict = pickle.load(mat_bin, encoding='latin1')
        randomMat = mat_dict['mat']
        itemIds = mat_dict['items']
        avatarIds = mat_dict['avatars']
        print('Loaded random matrix:')
        print(randomMat.shape)
        dat = randomMat
    #Loop over different numbers of latent dimensions
    for dims in dimArray:
        print("\n\n Starting analysis: %s %i \n\n" % (jobMatrix,dims))
        #Fit model
        #dat = dat[1:10000,:] #debug for testing on smaller data set=
        model = NMF(n_components=dims, init='random', random_state=0).fit(dat)
        VarExplained = metrics.explained_variance_score(dat.toarray(), model.inverse_transform(model.transform(dat))) #variance explained
        W = model.transform(dat) #Avatar embeddings
        H = model.components_ #item embeddings

        #Save to database: Too large to save the full matrices, so I will only export the var explained for now
        #output = {'W': pickle.dumps(csr_matrix(W), protocol=2), 'H':pickle.dumps(csr_matrix(H), protocol=2), 'varExplained':VarExplained, 'n_components':dims, 'jobMatrix': jobMatrix}
        output = {'varExplained':VarExplained, 'n_components':int(dims), 'jobMatrix': jobMatrix}

        #SAVE to DATABASE
        #db.nmf_validation.drop() #DELETES ALL DATA
        db.nmf_validation.insert(output)

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

