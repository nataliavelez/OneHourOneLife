#!/usr/bin/env python
# coding: utf-8

# # Singular value decomposition
# Natalia Vélez, July 2020

# In[11]:

import os, re, glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.linalg import svd

# Find matrix files:

# In[12]:


mtx_files = glob.glob('outputs/jobmatrix/*[0-9].txt')
mtx_files.sort()
# mtx_files = mtx_files[:3] # Debug only!
print('Matrix files:')
print(*mtx_files[:10], sep='\n')
print('...')

# Find corresponding labels:

# In[13]:

label_files = [f.replace('.txt', '_labels.txt') for f in mtx_files]
print('Label files:')
print(*label_files[:10], sep='\n')
print('...')

# Concatenate labels:

# In[14]:

print('Loading labels...')
all_labels = [np.loadtxt(f) for f in label_files]
all_labels = np.concatenate(all_labels).astype(np.int)
print(all_labels)


# Sanity check: Are any labels repeated across log files?


unique_labels, label_counts = np.unique(all_labels, return_counts=True)
repeated_labels = unique_labels[label_counts > 1]
min_repeats = np.min(label_counts[label_counts > 1])

print('%i total entries' % len(all_labels))
print('%i unique player IDs' % len(unique_labels))
print('%i repeated labels (range %i-%i)' % (len(repeated_labels),
                                            min_repeats,
                                            np.max(label_counts)))


# Concatenate matrices:

# In[6]:


all_mtx = []
print('Loading matrix files...')
for f in tqdm(mtx_files):
    all_mtx.append(np.loadtxt(f))
print('Concatenating matrices...')
all_mtx = np.concatenate(all_mtx, axis=0).astype(int)
print(all_mtx.shape)


# Sum over repeated labels:

# In[7]:


unique_mtx = []
for group in tqdm(unique_labels):
    group_v = np.sum(all_mtx[all_labels == group],axis=0)
    unique_mtx.append(group_v)
unique_mtx = np.array(unique_mtx)
print('Reducing repeated labels:')
print(unique_mtx.shape)


# The main event: SVD!

# In[8]:


U,s,Vh = svd(unique_mtx, full_matrices=False)


# Check output (debug)
# print('Check: Can we reconstruct the original values from the SVD?')
# reconstruction = U.dot(np.diag(s)).dot(Vh)
# print(np.all(np.isclose(unique_mtx, reconstruction)))


# Save outputs to file:

np.savetxt('outputs/svd/U.txt', U)
np.savetxt('outputs/svd/s.txt', s)
np.savetxt('outputs/svd/Vh.txt', Vh)
np.savetxt('outputs/svd/input_mtx.txt',unique_mtx)
np.savetxt('outputs/svd/input_playerIDs.txt', unique_labels)

