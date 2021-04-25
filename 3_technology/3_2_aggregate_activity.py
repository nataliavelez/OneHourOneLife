#!/usr/bin/env python
# coding: utf-8

'''
Aggregate activity by character and by community
Natalia Velez, April 2021
'''

import os, re, glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from os.path import join as opj
from scipy import sparse

# Make output directory
out_dir = opj('outputs/activity_agg')
print('Creating output directory: %s' % out_dir)
os.makedirs(out_dir, exist_ok = True)

# Find matrix files:
mtx_files = glob.glob('outputs/activity_in/*[0-9].txt')
mtx_files.sort()
print('Matrix files:')
print(*mtx_files[:10], sep='\n')
print('...\n')

# Find corresponding labels:
label_files = [f.replace('.txt', '_labels.txt') for f in mtx_files]
print('Label files:')
print(*label_files[:10], sep='\n')
print('...\n')

# Concatenate labels:
print('Loading labels...')
all_labels = [np.loadtxt(f) for f in label_files]
all_labels = np.concatenate(all_labels).astype(np.int)
print(all_labels)


# Sanity check: Are any labels repeated across log files?
unique_labels, label_counts = np.unique(all_labels, return_counts=True)
repeated_labels = unique_labels[label_counts > 1]
min_repeats = np.min(label_counts[label_counts > 1])
np.savetxt(opj(out_dir, 'avatarIDs.txt'), unique_labels, fmt='%i')

print('%i total entries' % len(all_labels))
print('%i unique avatar IDs' % len(unique_labels))
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

# Save as sparse matrix
sparse_activity = sparse.csr_matrix(unique_mtx)
sparse.save_npz(opj(out_dir, 'activity_matrix.npz'), sparse_activity)

# np.savetxt(opj(out_dir, 'activity_matrix.txt'), unique_mtx, fmt='%i') # Save dense matrix
