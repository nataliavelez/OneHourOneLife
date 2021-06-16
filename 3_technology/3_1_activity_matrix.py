#!/usr/bin/env python
# coding: utf-8

# # Activity matrices
# Natalia Vélez, June 2020

# In[1]:


import glob, re, sys, time, os
import pandas as pd
import numpy as np
from tqdm import tqdm

# ## Find data

# Parse inputs (to convert to script):

# In[2]:
_, idx = sys.argv
idx = int(idx)
# idx = 4 # Debug only
with open('outputs/seed_changes.txt', 'r') as handle:
    seed_data = handle.read().splitlines()
    
seed_data = [int(s) for s in seed_data]
seed = seed_data[idx]
if idx == len(seed_data)-1:
    print('Most recent seed reached')
    next_seed = int(time.time())
else:
    next_seed = seed_data[idx+1]
    
print('Processing map changes between t = <%i, %i>' % (seed, next_seed))


# Read features:

# In[3]:


feature_f = 'outputs/activity_features.txt'
with open(feature_f, 'r') as handle:
    features = handle.read().splitlines()
    
print('Found %i unique items' % len(features))
print(*features[:50], sep='\t')


# Find map change files:

# In[4]:


def str_extract(pattern, s): return re.search(pattern,s).group(0)
def seed_match(f): 
    start_t = int(str_extract('(?<=start-)[0-9]+', f))
    return ((start_t-seed) > -2) & (start_t < next_seed)

map_files = glob.glob('outputs/maplog/*.tsv')
map_files = [f for f in map_files if seed_match(f)]
map_files.sort()

print('Found %i map files' % len(map_files))
print(*map_files[:5], sep='\n')
print('...')


# ## Assemble job matrices
# 
# Helper 

# In[5]:


def map_crosstab(f):
    map_df = pd.read_csv(f, sep='\t')

    # Trim invalid objects
    map_df = map_df[map_df.avatar > 0] # No player attached to event
    map_df = map_df[map_df.object_id != '0'] # Interact w/ empty square 

    # Clean up modifiers
    map_df['object_id'] = map_df.object_id.str.replace(r'^(f)|([u-v][0-9]+$)', '')

    # Convert to number
    map_df['object_id'] = map_df['object_id'].astype(np.int64)
    map_df['object_id'] = np.where(map_df['object_id'] > 5000, 9999, map_df['object_id'])
    map_df['object_id'] = map_df['object_id'].astype(str)

    # Make objectID and playerID into categorical variables
    map_df['object_id'] = pd.Categorical(map_df['object_id'], categories=features)
    map_df['avatar'] = map_df['avatar'].astype(np.int64)
    map_df['avatar'] = pd.Categorical(map_df['avatar'])

    # Co-occurrence matrix
    map_df = map_df.reset_index(drop=True)
    map_df = map_df[['object_id', 'avatar']]

    map_occ = pd.crosstab(map_df.avatar, map_df.object_id, dropna=False)
    mtx_map = map_occ.values
    mtx_labels = list(map_df['avatar'].values) # debug

    return mtx_map, mtx_labels


# Helper function: Save array to txt

# In[6]:


def write_array(arr, f):
    with open(f, 'w') as filehandle:  
        filehandle.writelines("%s\n" % e for e in arr)


# Make output directory
os.makedirs('outputs/activity_in', exist_ok = True)

# Save to file
for f in tqdm(map_files):
    out_file = f.replace('maplog', 'activity_in').replace('.tsv','.txt')
    label_file = out_file.replace('.txt', '_labels.txt')
    
    if os.path.exists(out_file):
        print('Outputs already exist: %s' % out_file)
        print('Skipping file')
    else:
        mtx_map, mtx_labels = map_crosstab(f)
        np.savetxt(out_file, mtx_map, '%i')
        write_array(mtx_labels, label_file)

