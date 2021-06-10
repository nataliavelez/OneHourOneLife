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
from scipy.sparse import csr_matrix
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


#Arg parser # Parallel version 
# parser = argparse.ArgumentParser(description='Validation of Non-negative matrix factorization')
# parser.add_argument('-d','--dims', type=int, help='Number of latent dimensions', default=5)
# parser.add_argument('-m', '--matrix', help='version of activity matrix, either [cleaned] or [tfidf]', type=str, required=True)

# args = parser.parse_args()
# argsdict = vars(args)

# dims = argsdict['dims']
# jobMatrix = argsdict['matrix']

#Running it sequentially
for jobMatrix in ('cleaned', 'tfidf'):
    for dims in range(5,30+1):
        print("\n\n Starting analysis: %s %i \n\n" % (jobMatrix,dims))
        #Which job matrix to use?
        if jobMatrix == 'cleaned':
            #Load cleaned matrix. This takes about 30 seconds
            mat_id = list(db.cleaned_job_matrix.files.find())[0]['_id'] #get id
            fs = gridfs.GridFS(db, collection='cleaned_job_matrix') 
            mat_bin = fs.get(mat_id) #extract binary
            mat_dict = pickle.load(mat_bin, encoding='latin1')
            jobMatrixCleaned = mat_dict['mat']
            itemIds = mat_dict['items']
            avatarIds = mat_dict['avatars']
            print('Loaded Job matrix:')
            print(jobMatrixCleaned.shape)
            dat = jobMatrixCleaned
        elif jobMatrix == 'tfidf':
            #Load tfidf matrix. This takes about 30 seconds
            mat_id = list(db.tfidf_matrix.files.find())[0]['_id'] #get id
            fs = gridfs.GridFS(db, collection='tfidf_matrix') 
            mat_bin = fs.get(mat_id) #extract binary
            mat_dict = pickle.load(mat_bin, encoding='latin1')
            tfidfJobMatrixNormalized = mat_dict['mat']
            itemIds = mat_dict['items']
            avatarIds = mat_dict['avatars']
            print('Loaded Job matrix:')
            print(tfidfJobMatrixNormalized.shape)
            dat = tfidfJobMatrixNormalized

        #Fit model
        #dat = dat[1:10000,:] #debug for testing on smaller data set=
        model = NMF(n_components=dims, init='random', random_state=0).fit(dat)
        VarExplained = metrics.explained_variance_score(dat.toarray(), model.inverse_transform(model.transform(dat))) #variance explained
        W = model.transform(dat) #Avatar embeddings
        H = model.components_ #item embeddings

        #Save to database: Too large to save the full matrices, so I will only export the var explained for now
        #output = {'W': pickle.dumps(csr_matrix(W), protocol=2), 'H':pickle.dumps(csr_matrix(H), protocol=2), 'varExplained':VarExplained, 'n_components':dims, 'jobMatrix': jobMatrix}
        output = {'varExplained':VarExplained, 'n_components':dims, 'jobMatrix': jobMatrix}

        #SAVE to DATABASE
        #db.nmf_validation.drop() #DELETES ALL DATA
        db.nmf_validation.insert(output)

        #Which items most strongly defined each component?
        filepath = 'jobspace/outputs/%s/%i.txt' %  (jobMatrix,dims)
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

