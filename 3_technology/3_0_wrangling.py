#!/usr/bin/env python
# coding: utf-8

# # Map change: Data wrangling
# Natalia Vélez, June 2020

# In[3]:


import os, re, glob, datetime, tqdm, pymongo
from os.path import join as opj
import pandas as pd
import numpy as np
# from tqdm import notebook

# from calplot import calplot, yearplot


# Helper functions:
import sys
sys.path.append('..')
from utils import gsearch, str_extract, int_extract

# Connect to database
keyfile = '../6_database/credentials.key'
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
print(myclient)
ohol = myclient.ohol
map_col = ohol.maplogs
print(ohol.list_collection_names)

# Get timestamp from filename
def file_tstamp(f):
    tstamp = int_extract('[0-9]+(?=time)', f)
    date_dt = datetime.datetime.fromtimestamp(tstamp)
    date_str = date_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return date_str


# ## Find files

# In[5]:

map_dir = '../../data/publicMapChangeData/bigserver2.onehouronelife.com'
#scratch_dir = os.environ['SCRATCH']
#out_dir = opj(scratch_dir, 'OneHourOneLife', 'maplog')
out_dir = opj('outputs', 'maplog')
os.makedirs(out_dir, exist_ok=True)

# ### Old-style map change files
# Older map change data do not include player IDs---that is, we can know which items were interacted with, but not who interacted with what.

# In[6]:


old_map_files = gsearch(map_dir, '*seed_mapLog.txt')
old_map_files.sort()

print('Old-style map files:')
print(*old_map_files[:10], sep='\n')


# Timestamp of first and last old-style files:

# In[7]:


print('FIRST: %s' % file_tstamp(old_map_files[0]))
print('LAST: %s' % file_tstamp(old_map_files[-1]))


# ### New-style map change files
# More recent map change files include an extra column for player ID and do not include the mapseed in the filename.

# In[8]:


new_map_files = gsearch(map_dir, '*time_mapLog.txt')
new_map_files.sort()

print('New-style map files:')
print(*new_map_files[:10], sep='\n')


# Timestamp of first and most recently downloaded new-style mapchange files:

# In[9]:


print('FIRST: %s' % file_tstamp(new_map_files[0]))
print('LAST: %s' % file_tstamp(new_map_files[-1]))


# ### Mapseed timestamps?

# > The apocalypse is triggered by players and wipes out all player made items and **changes the world seed.** All players online in the world at that time stay in the world, still alive, just now naked and on new landscape, but still at the relative same coords as they were before apocalypse (for instance, if we are both at the same latitude but 1000 tiles apart on longitude when the apocalypse happens, in the new landscape we will still be on the same latitude and still 1000 tiles away on longitude). 
# 
# Source: [OHOL Forums](https://onehouronelife.com/forums/viewtopic.php?id=8997)
# 
# Can we tell when apocalypses happened by marking when a new mapseed file is created in the new-style mapchange logs?

# In[10]:


mapseed_files = gsearch(map_dir, '*mapSeed.txt')
mapseed_files.sort()

print(*mapseed_files[:5], sep='\n')


# Mapseed timestamps:

# In[11]:


mapseed_dates = [file_tstamp(f) for f in mapseed_files]
print('%i server resets found' % len(mapseed_dates))
print(*mapseed_dates, sep='\n')

mapseed_df = pd.DataFrame(mapseed_dates, columns=['date'])
mapseed_df['date'] = pd.to_datetime(mapseed_df['date'])
mapseed_df['seed_reset'] = 1
mapseed = pd.Series(mapseed_df['seed_reset'].values, index=mapseed_df['date'])

# fig,ax = calplot(mapseed, cmap='Reds', fillcolor='silver')
# fig.colorbar(ax[0].get_children()[1], ax=ax.ravel().tolist(), orientation = 'horizontal')


# ## Wrangle new-style map change data

# ### Clean up & concatenate map change files

# Load releases:

# In[12]:


ver_file = '../1_download/outputs/version_history.tsv'

# Load file
ver = pd.read_csv(ver_file, sep='\t')
ver.head()


# Helper function: Find closest-matching release

# In[13]:


def find_version(start_t):

    tmp_ver = ver.copy()
    tmp_ver['lag'] = start_t - tmp_ver['timestamp']
    tmp_ver = tmp_ver[tmp_ver['lag'] >= 0]

    file_ver = tmp_ver.loc[tmp_ver['lag'].idxmin()].release
    file_ver = int(file_ver)
    
    return file_ver


# Helper function: Read map change file and convert into a nice dataframe

# In[14]:


def make_map_df(f):

    # Read start time from first line
    with open(f) as handle:
        start_line = handle.readline()
    start_str = str_extract('\d+\.\d+', start_line)
    start_t = float(start_str)

    # Match start time to release
    log_release = find_version(start_t)
    
    # Out file
    out_file = 'maplog_release-%i_start-%i.tsv' % (log_release, start_t)
    out_path = opj(out_dir, out_file)

    # Convert to dataframe
    log_df = pd.read_table(f, sep=' ', skiprows=1, header=None, names=['t_elapsed', 'x', 'y', 'object_id', 'avatar'])
    log_df = log_df.dropna()
    return log_df, out_path


# Helper function: Find all unique items (used to define features in SVD)

# In[16]:


def find_unique(raw_map):

    # Trim invalid objects
    map_df = raw_map.copy()
    map_df = map_df[map_df.avatar > 0] # No player attached to event
    map_df = map_df[map_df.object_id != '0'] # Interact w/ empty square 
    
    # Clean up modifiers
    map_df['object_id'] = map_df.object_id.str.replace(r'^(f)|([u-v][0-9]+$)', '')
    
    # Convert to number
    map_df['object_id'] = map_df['object_id'].astype(np.int64)
    map_df['object_id'] = np.where(map_df['object_id'] > 5000, 9999, map_df['object_id'])

    # Unique items
    obj_list = map_df.object_id.tolist()
    unique_obj = np.unique(obj_list).tolist()
    unique_obj.sort()
    
    return unique_obj


# Read all mapchange files and convert to dataframe:

unique_object_list = []

for f in tqdm.tqdm(new_map_files):
    tmp_df, out_f = make_map_df(f)
    unique_object_list.append(find_unique(tmp_df))
    
    # Save to file
    tmp_df.to_csv(out_f, sep='\t', index=False)
    
    # Save to database
    tmp_list = tmp_df.to_dict('records')
    map_col.insert_many(tmp_list)

# ## Detect map seed changes
# Find seed files:
seed_files = gsearch(map_dir, '*mapSeed.txt')
seed_files.sort()
print(*seed_files, sep='\n')

# Read seed files:

seed_list = []
seed_file = 'outputs/seed_changes.txt'

for f in seed_files:
    tstamp = str_extract('[0-9]+(?=time)', f)
    seed_list.append(tstamp)

seed_list = '\n'.join(seed_list)

with open(seed_file, 'w') as out:
    out.writelines(seed_list)


# ## Get all unique objects

# Clean up list of unique objects:

# In[19]:


unique_objects_flat = sum(unique_object_list,[])
unique_objects_flat = np.array(unique_objects_flat)

unique_objects = np.unique(unique_objects_flat)
print('Found %i unique objects' % len(unique_objects))
print(*unique_objects[:50], sep='\t')


# In[ ]:


out_file = 'outputs/activity_features.txt'
with open(out_file, 'w') as handle:
    for obj in unique_objects:
        handle.write('%s\n' % obj)

