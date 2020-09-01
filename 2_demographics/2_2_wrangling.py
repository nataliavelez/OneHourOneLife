#!/usr/bin/env python
# coding: utf-8

# # Wrangling lifelog data (July 2019–May 2020)
# Natalia Vélez, last updated June 2020
# 
# In this notebook:
# 
# * Load, clean up lifelog data from the entire history of the game (updated!)
# * Split data by version
# * Split data by era (arc, rift, boundless world)
# * Prepare inputs for subsequent analyses (census, family trees, migration patterns)
# 
# In subsequent analyses, we will focus on data from the Boundless World era (November 2019–present)

import os, re, glob, datetime, tqdm
import pandas as pd
import numpy as np
from os.path import join as opj
from ast import literal_eval as make_tuple


# Helper functions:
gsearch = lambda *args: glob.glob(opj(*args))
str_extract = lambda pattern, s: re.search(pattern, s).group(0)

# DEBUG: Player missing from lifelogs
missing_id = 2279990
print('[DEBUG] Searching for: %i' % missing_id)

# ## Parse version history
# In future analyses, we'll want to split data by release; different releases of the game
#  will have different items, mechanics, etc. To do that, we'll parse the version history 
# here and get the start and end dates for each release.


ver_file = '../1_download/outputs/version_history.tsv'

# Load file
ver = pd.read_csv(ver_file, sep='\t')
print('Version history:')
print(ver.head())

# `find_version`: Helper function. Takes a filename as input, finds the corresponding release.

def find_version(file):
    file_date = date_extract(file)

    tmp_ver = ver.copy()
    tmp_ver['lag'] = file_date - tmp_ver['timestamp']
    tmp_ver = tmp_ver[tmp_ver['lag'] >= 0]

    file_ver = tmp_ver.loc[tmp_ver['lag'].idxmin()].release
    
    return file_ver


# `find_era`: Find era associated with release

def find_era(release):
    if release < 252:
        r = 'arc'
    elif (release >= 252) & (release < 280):
        r = 'rift'
    elif release >= 280:
        r = 'boundless'
        
    return r


# ## Clean up data

# We first need to filter files by date, to pick out files within the range we're interested in. 
# (This might be a roundabout way of doing it—suggestions welcome.)
# `date_extract`: Helper function. Takes a basename as a string (e.g., '2019_03March_23_Saturday.txt') 
# and returns an integer representation of the date (e.g., 20190323).

def date_extract(s):
    
    date_regex = '([0-9]{4})_([0-9]{2})[A-Za-z]+_([0-9]{2})'
    date_search = re.findall(date_regex, s)
    date_str = ''.join(date_search[0])
    date_dt = datetime.datetime.strptime(date_str, '%Y%m%d')
    date_tstamp = date_dt.timestamp()
    
    return date_tstamp


# List all files:

data_dir = '../data'
all_files = gsearch(data_dir, 'publicLifeLogData', 'lifeLog_bigserver2*', '2*y.txt')
all_files.sort()
print('Lifelog files:')
print(len(all_files))
print(*all_files[:10], sep='\n')


# Extract dates:
print('Extracting dates from filenames:')
all_dates = [date_extract(f) for f in all_files]
print(*all_dates[:10], sep='\n')


# (outdated) Filter files within range:
# data_files = file_df['file'].values
data_files = all_files
print('%i files found' % len(data_files))
print(*[os.path.basename(f) for f in data_files[-20:]], sep='\n')


# Load all files:
print('Loading files:')
data_list = []
empty_files = []
for f in tqdm.tqdm(data_files):
    tmp_server = str_extract('(?<=lifeLog_)[a-zA-Z0-9]+', f)
    tmp_ver = find_version(f)
    tmp_era = find_era(tmp_ver)

    tmp_d = pd.read_csv(f, sep =' ', header=None)
    tmp_d.insert(0, 'server', tmp_server)
    tmp_d.insert(1, 'release', tmp_ver)
    tmp_d.insert(2, 'era', tmp_era)
    data_list.append(tmp_d)


print('Check raw data:')
raw_data = pd.concat(data_list)
print(raw_data.tail())

# Deaths:
print('Raw death data:')
death_raw = raw_data[raw_data.iloc[:,3] == 'D'].copy().reset_index(drop=True)
print(death_raw.head())

# Births:
print('Raw birth data:')
birth_raw = raw_data[raw_data.iloc[:,3] == 'B'].copy().reset_index(drop=True)
print(birth_raw.head())

# ### Clean up data

shared_header = ['server', 'release', 'era',
                 'event', 'timestamp', 'avatar',
                 'hash', 'age', 'sex', 'location', 'parent',
                 'cause_of_death', 'pop', 'chain', 'killer']

trim_header = ['server', 'release', 'era',
               'event', 'timestamp', 'avatar',
               'hash', 'age', 'sex', 'location', 'parent',
               'cause_of_death', 'killer']

# #### Deaths
print('=== CLEANING UP DEATHS ===')
death_data = death_raw.copy()

# Insert missing columns
death_data.insert(10, 'parent', np.nan)
death_data.insert(13, 'chain', np.nan)
death_data.insert(14, 'killer', np.nan)

death_data.columns = shared_header
death_data = death_data.dropna(subset=['location'])

print('Raw death data:')
print(death_data.head())

print('DEBUG: Missing player in raw death data?')
print(death_data[death_data['avatar'] == missing_id])

# Clean up factor structure:

print('Trimmed death data:')
death_data = death_data[trim_header]
print(death_data.head())

# Clean up IDs,  locations, causes of death

# Locations
death_data['location'] = death_data['location'].apply(make_tuple)

# Check for murdered players
murderers = death_data['cause_of_death'].str.extract(r'(?<=killer_)([0-9]+)', expand=False)
death_data['cause_of_death'] = death_data['cause_of_death'].str.replace("killer_[0-9]+", "murdered")
death_data['killer'] = murderers

print(death_data['cause_of_death'].unique())
print(death_data['killer'].unique()[:10])

print('Cleaned-up death data:')
print(death_data.head())

print('DEBUG: Missing player in death data after clean-up?')
print(death_data[death_data['avatar'] == missing_id])

print('=== CLEANING UP BIRTHS ===')
birth_data = birth_raw.copy()

# Insert missing columns
birth_data.insert(7, 'age', np.nan)
birth_data.insert(11, 'cause_of_death', np.nan)
birth_data.insert(14, 'killer', np.nan)

birth_data.columns = shared_header
birth_data = birth_data.dropna(subset=['location'])

print('Raw birth data:')
birth_data.head()

print('DEBUG: Missing player in raw birth data?')
print(birth_data[birth_data['avatar'] == missing_id])

# Clean up factor structure:
print('Trimmed birth data:')
birth_data = birth_data[trim_header] 
print(birth_data.head())


# Clean up IDs, locations, parents:
# Fix messed-up tuples
birth_data['location'] = np.where(birth_data['location'].str.strip().str[-1] == ')',
                                  birth_data['location'],
                                  birth_data['location'] + ')')

# Then proceed
birth_data['location'] = birth_data['location'].apply(make_tuple)
birth_data['parent'] = np.where(birth_data['parent'] == 'noParent', 
                                -1,
                                birth_data['parent'].str.extract(r'(?<=parent=)([0-9]+)'))
birth_data['parent'] = birth_data['parent'].int

print('Cleaned-up birth data:')
print(birth_data.head())

print('DEBUG: Missing player in birth data after clean-up?')
print(birth_data[birth_data['avatar'] == missing_id])



# #### Save outputs
lifelog_data = pd.concat([death_data, birth_data])
lifelog_data = lifelog_data.sort_values(by=['server', 'timestamp'])
lifelog_data = lifelog_data.reset_index(drop=True)

print('Lifelog data:')
print(lifelog_data.head())

print('DEBUG: Missing player in lifelog data before split?')
print(lifelog_data[lifelog_data['avatar'] == missing_id])

# Split by eras and save:

eras = ['arc', 'rift', 'boundless']
all_servers = [str_extract('(?<=lifeLog_)[a-zA-Z0-9]+', f) for f in data_files]
servers = np.unique(all_servers)

for e in tqdm.tqdm(eras):
    era_data = lifelog_data[(lifelog_data['era'] == e) & (lifelog_data['server'] == 'bigserver2')]
    if not era_data.empty:
        era_data = era_data.reset_index(drop=True)
        era_fname = 'outputs/lifelogs_bigserver2_%s_data.tsv' % e
        era_data.to_csv(era_fname, sep='\t', index=True)

