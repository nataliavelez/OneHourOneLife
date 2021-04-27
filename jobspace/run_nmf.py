#Run NMF
#Charley Wu, April 2021
import pymongo, os, bson, json, glob, pickle, gridfs, sys
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import Counter
import seaborn as sns
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.sparse import csr_matrix
from os.path import join as opj
from tqdm import notebook
from sklearn.decomposition import NMF
from sklearn.decomposition import PCA

sys.path.append("..")
import dbfind

#Database credentials
keyfile = '../6_database/credentials.key'
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
db = myclient.ohol

print(db)
print(db.list_collection_names())

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


#TODO: preprocessing

#TEST:
tfidfJobMatrixNormalized = activity_mtx[0:100000,:] #Try running it on 100,000 data points

#Define model
model = NMF(n_components=20, init='random', random_state=0)
W = model.fit_transform(tfidfJobMatrixNormalized)
H = model.components_





#TODO: iterate over different component numbers and see which is the best model 
#https://stackoverflow.com/questions/48148689/how-to-compare-predictive-power-of-pca-and-nmf
	



