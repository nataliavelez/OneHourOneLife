#!/usr/bin/env python
# coding: utf-8

# # Singular value decomposition
# Natalia Vélez, July 2020

import matplotlib
matplotlib.use('Agg')

import os, re, glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.linalg import svd
from os.path import join as opj
from kneed import KneeLocator

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('white')
sns.set_context('paper')

# Make output directory
#out_dir = opj(os.environ['SCRATCH'], '
out_dir = opj('outputs/svd')
print('Creating output directory: %s' % out_dir)
os.makedirs(out_dir, exist_ok = True)

# Find matrix files:
mtx_files = glob.glob('outputs/jobmatrix/*[0-9].txt')
mtx_files.sort()
#mtx_files = mtx_files[:3] # Debug only!
print('Matrix files:')
print(*mtx_files[:10], sep='\n')
print('...')

# Find corresponding labels:
label_files = [f.replace('.txt', '_labels.txt') for f in mtx_files]
print('Label files:')
print(*label_files[:10], sep='\n')
print('...')

# Concatenate labels:
print('Loading labels...')
all_labels = [np.loadtxt(f) for f in label_files]
all_labels = np.concatenate(all_labels).astype(np.int)
print(all_labels)


# Sanity check: Are any labels repeated across log files?
unique_labels, label_counts = np.unique(all_labels, return_counts=True)
repeated_labels = unique_labels[label_counts > 1]
min_repeats = np.min(label_counts[label_counts > 1])
np.savetxt('outputs/svd/input_playerIDs.txt', unique_labels)

print('%i total entries' % len(all_labels))
print('%i unique player IDs' % len(unique_labels))
print('%i repeated labels (range %i-%i)' % (len(repeated_labels),
                                            min_repeats,
                                            np.max(label_counts)))


# Concatenate matrices:
all_mtx = []
print('Loading matrix files...')
for f in tqdm(mtx_files):
    all_mtx.append(np.loadtxt(f))
print('Concatenating matrices...')
all_mtx = np.concatenate(all_mtx, axis=0)
print(all_mtx.shape)


# Sum over repeated labels:
unique_mtx = []
for group in tqdm(unique_labels):
    group_v = np.sum(all_mtx[all_labels == group],axis=0)
    unique_mtx.append(group_v)
unique_mtx = np.array(unique_mtx)
print('Reducing repeated labels:')
print(unique_mtx.shape)
del all_mtx

## Normalization: TF-IDF
## (NV: Skipping!)
# def tf(row): return row/np.sum(row)

# def idf(col):
#     N = len(col)
#     df = np.sum(col > 0)+1
#     idf_val = np.log(N/df)+1

#     return np.ones(col.shape)*idf_val

# def tf_idf(m):
#     m_tf = np.apply_along_axis(tf, 1, m)
#     m_idf = np.apply_along_axis(idf, 0, m)
#     m_norm = np.multiply(m_tf, m_idf)
    
#     return m_norm

#norm_mtx = tf_idf(unique_mtx)
#print('Applying TF-IDF weighting:')
#print(norm_mtx.shape)
#del unique_mtx

# The main event: SVD!
U,s,Vh = svd(unique_mtx, full_matrices=False)

# Check output (debug)
print('Check: Can we reconstruct the original values from the SVD?')
reconstruction = U.dot(np.diag(s)).dot(Vh)
print(np.all(np.isclose(unique_mtx, reconstruction)))

# Find "knee" in singular values
print('Truncating outputs')
knee = KneeLocator(range(len(s)), s, curve='convex', direction='decreasing')
r = knee.knee
var_exp = np.cumsum(s)/np.sum(s)
print('Threshold: %i' % r)
print('Variance explained: %0.2f' % var_exp[r])

# Plotting the knee
fig,(ax1,ax2) = plt.subplots(1,2, figsize=(12,6))
ax1.plot(s)
ax1.axvline(knee.knee, linestyle='--', color='#aaaaaa')
ax1.text(r+200, np.max(s)/2, 'i = %i' % r, size=18)
ax1.set(xlabel = 'i', ylabel = 'Singular values')

# Variance explained
ax2.plot(var_exp)
ax2.axhline(var_exp[r], linestyle='--', color='gray')
ax2.axvline(r, linestyle='--', color='gray')
ax2.text(r+200, var_exp[r]-0.1, '%0.2f' % var_exp[r], size=18)
ax2.set(xlabel = 'i', ylabel = 'Variance explained')

sns.despine()
plt.savefig('outputs/svd/truncate_threshold.png')

# Truncate and save outputs
print('Truncating U')
print(U.shape)
U_hat = U[:,:r]
print(U_hat.shape)
np.savetxt('outputs/svd/U_hat.txt', U_hat)
del U

print('Truncating s')
print(s.shape)
s_hat = s[:r]
print(s_hat.shape)
np.savetxt('outputs/svd/s_hat.txt', s_hat)
del s

print('Truncating Vh')
print(Vh.shape)
Vh_hat = Vh[:r,:]
print(Vh_hat.shape)
np.savetxt('outputs/svd/Vh_hat.txt', Vh_hat)
del Vh
