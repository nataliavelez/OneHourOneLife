#!/usr/bin/env python
# coding: utf-8

# # Lineages
# Natalia Vélez, July 2020
# 
# The goal of this notebook is to construct family graphs (directed graph from parent —> child) out of the lifelog data. These family trees will be used in several other analyses.

# In[1]:


# %matplotlib inline

import os, re, glob, json, tqdm, pymongo
import pandas as pd
import numpy as np

import networkx as nx
# import matplotlib.pyplot as plt
# import seaborn as sns
from networkx.drawing.nx_agraph import graphviz_layout

from os.path import join as opj
# from tqdm import notebook
from ast import literal_eval as make_tuple

# sns.set_context('talk')
# sns.set_style('white')

# # Connect to database
# keyfile = '../6_database/credentials.key'
# creds = open(keyfile, "r").read().splitlines()
# myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
# print(myclient)
# ohol = myclient.ohol
# life_col = ohol.lifelogs
# print(ohol.list_collection_names)

# Helper function
def gsearch(*args): return glob.glob(opj(*args)) # Search for fukes
def clean_tuple(s):
    try:
        t = make_tuple(s)
    except ValueError:
        t = ()
    return t


# Get data:
# era_files = glob.glob('outputs/lifelogs*_data.tsv')
# era_list = []

# for f in era_files:
#     era_data = pd.read_csv(f, sep='\t', index_col=0)
#     era_list.append(era_data)
    
# era_df = pd.concat(era_list)
# era_df = era_df.drop(columns=['server', 'release', 'era'])
era_df = pd.read_csv('outputs/lifelogs_bigserver2_data.csv')
era_df = era_df.drop(columns=['server', 'release', 'era'])

# era_df.head()


# Find players' parents and time/location of birth:

idx_vars = ['player', 'avatar']
births = era_df[era_df['event'] == 'B'].copy()
births = births[idx_vars + ['timestamp', 'parent', 'location', 'sex']]
births = births.rename({'location': 'birth', 'timestamp': 'tBirth'}, axis='columns')
# births.head()


# Find time and circumstances of death:

# In[4]:


deaths =  era_df[era_df['event'] == 'D'].copy()
deaths = deaths[idx_vars + ['timestamp', 'location', 'age', 'cause_of_death']]
deaths = deaths.rename({'location': 'death', 'timestamp': 'tDeath'}, axis='columns')

# deaths.head()


# ## Merge births and deaths

# **DEBUG:** Unique avatar IDs in births and deaths

# In[5]:


# Get unique avatars in each DF
unique_births = np.unique(births['avatar'])
unique_deaths = np.unique(deaths['avatar'])

# How many total unique avatars?
unique_avatars = np.concatenate((unique_births, unique_deaths))
unique_avatars = np.unique(unique_avatars)

# Which avatars are in deaths but not births, and vice versa?
not_in_deaths = np.setdiff1d(unique_births, unique_deaths)
not_in_births = np.setdiff1d(unique_deaths, unique_births)

print('%i unique avatars' % len(unique_avatars))
print('%i in both' % len(np.intersect1d(unique_births, unique_deaths)))
print('%i not in deaths: %s...' % (len(not_in_deaths), not_in_deaths[:5],))
print('%i not in births: %s...' % (len(not_in_births), not_in_births[:5],))


# Merge & clean up:

# In[6]:


print('Births: %s' % (births.shape,))
print('Deaths: %s' % (deaths.shape,))

life_df = pd.merge(births, deaths, on=idx_vars, how='outer')
print('Merged dataframe: %s' % (life_df.shape,))

# Turn birth/death locations to tuples
print('Birth/death locations...')
life_df['birth'] = life_df['birth'].apply(clean_tuple).apply(np.array)
life_df['death'] = life_df['death'].apply(clean_tuple).apply(np.array)

# Split coordinates
print('Splitting into x/y coords...')
life_df[['birthX', 'birthY']] = pd.DataFrame(life_df['birth'].tolist(),
                                              index=life_df.index)   
life_df[['deathX', 'deathY']] = pd.DataFrame(life_df['death'].tolist(),
                                              index=life_df.index)

# Parse player IDs
print('Parsing player IDs...')
life_df['avatar'] = life_df['avatar'].astype(np.int)

# Parse parent IDs
print('Parsing parents...')
#life_df['parent'] = life_df['parent'].str.extract('(noParent|(?<=parent=)[0-9]+)')
life_df['parent'] = life_df['parent'].str.replace('noParent', '-1')
life_df['parent'] = life_df['parent'].astype(np.int)

# Order from most recent
print('Cleaning up...')
life_df = life_df.sort_values('tBirth', ascending=False)
life_df = life_df.reset_index(drop=True)


# In[7]:


print(life_df.shape)
# life_df.tail()


# ## Parse names

# Helper function: Remove from data...
# 
# * Roman numerals (including some nonsense ones at high-gen numbers)
# * Kin labels? (e.g., SHINA1580640)

# In[8]:


def is_roman(s):
    # Checks if string is a "valid" Roman numeral
    # Note this includes some *cough*idiosyncratic*cough* numerals in the OHOL dataset:
    # e.g., CLXLIII => True (but actually nonsense)
    roman_regex  = 'M{0,4}(CM|CD|D?C{0,3})(LXL|XC|XL|L?X{0,3})(IX|IV|V?I{0,3})'
    roman_match = re.match(roman_regex, s)
    
    str_length = len(s)
    match_length = roman_match.span()[1]
    
    return str_length == match_length

def is_kin(s, idx):
    kin_regex = '[A-Z]{0,}[0-9]+'
    kin_match = re.search(kin_regex, s)
    return bool(kin_match) & (idx > 0)

def is_valid(s, idx):
    
    not_roman = not is_roman(s)
    not_kin = not is_kin(s, idx)
    
    return not_roman & not_kin


# Find name files:

# In[9]:


data_dir = '../../data'
name_files = glob.glob(opj(data_dir, 'publicLifeLogData', 'lifeLog_bigserver2*', '*names.txt'))
name_files.sort()
print('Name files:')
print(*[os.path.basename(f) for f in name_files[:5]], sep='\n')
print('...')


# Iterate over name files and extract names:

# In[10]:


name_list = []
re.compile("^([A-Z][0-9]+)+$")

for f in tqdm.tqdm(name_files):
    with open(f, 'r') as handle:
        data_str = handle.read().splitlines()

    data = []
    for s in data_str:
        row_data = s.split() # Split lines
        row_data = [si for idx, si in enumerate(row_data) if is_valid(si, idx)]
        
        if len(row_data) > 3:
            row_data.remove('EVE')
            print('Corrected: %s' % row_data)

        while len(row_data) < 3: 
            row_data.append('')

        name_list.append(row_data)


# Assemble into dataframe:

# In[11]:


name_df = pd.DataFrame(name_list, columns=['avatar', 'first', 'last'])
name_df['avatar'] = name_df['avatar'].astype(np.int)
# name_df.head()


# Merge with `life_df`:

# In[12]:

print('<<< DEBUG: Before merge:')
print(life_df.shape)
life_df = pd.merge(life_df, name_df, on='avatar', how='left')
print('After merge:')
print(life_df.shape)
print('>>>')
# life_df.head()


# Save `life_df` to file:

# In[13]:


print('Saving merged lifelogs...')
life_df.to_csv('outputs/all_lifelogs_compact.csv', index=False)

# print('Uploading lifelogs to database...')
# life_list = life_df.copy()
# life_list = life_list.drop(columns=['birth','death'])
# life_list = life_df.to_dict('records')
# life_col.insert_many(life_list)

# ## Sanity check: How many lineages can we expect?

# Spot eves:

# In[14]:


eves = life_df[life_df['parent'] < 0].reset_index()
eves.to_csv('outputs/lineage_input_eves.csv', index=False)
print(eves['avatar'][:10])


# How many eves?
n_eves = eves.shape[0]
n_births = len(life_df)
eve_rate = n_eves/n_births
print('%i Eves out of %i births (%0.2f%%)' % (n_eves, n_births, eve_rate*100))


# Eve spawn rate over time (TO-DO: MOVE TO LATER SCRIPT)

# In[16]:


# eve_rate = life_df.copy()
# eve_rate['is_eve'] = eve_rate['parent'] < 0
# eve_rate['date'] = pd.to_datetime(eve_rate['tBirth'],unit='s')
# eve_rate['month'] = eve_rate['date'].dt.to_period('M')

# eve_rate = eve_rate.groupby('month')['is_eve'].agg(['count', 'sum']).reset_index()
# eve_rate = eve_rate.rename(columns={'count': 'n_births', 'sum': 'n_eves'})
# eve_rate['eve_rate'] = eve_rate['n_eves']/eve_rate['n_births']

# fig,ax=plt.subplots(figsize=(8,4))
# ax.plot_date(eve_rate['month'], eve_rate['eve_rate'], '-o')
# ax.set(ylabel='Eve spawn rate')
# plt.xticks(rotation=45)
# sns.despine()


# ## Parent-child pairs

# Helper: Search recursively through lifelogs, starting with Eve

# In[23]:


# All parent-child links
parent_df = life_df[['avatar', 'parent']].copy()
parent_df.to_csv('outputs/lineage_input_parents.csv', index=False)
# parent_df.head()


# In[18]:


def search_fam(player):
    descendants = parent_df.loc[parent_df['parent'] == player, 'avatar'].values
    
    for d in descendants:
        descendants = np.append(descendants, search_fam(d))
        
    return descendants


# Helper: Write data to JSON file

# In[19]:


def write_json(data, f):
    with open(f, 'w') as outfile:
        json.dump(data, outfile)


# All parent-child pairs:

# Main loop: Build graphs from parent-child pairs:

# In[22]:


os.makedirs('outputs/families', exist_ok=True)

families_list = []

for _, family in tqdm.tqdm(eves.iterrows(), total=n_eves):

    eve = family['avatar']
    fam_name = family['last']
    fam_start = family['tBirth']

    fam_nodes = list(search_fam(eve))
    fam_df = parent_df[parent_df['avatar'].isin(fam_nodes)]
    fam = nx.from_pandas_edgelist(fam_df, 'parent', 'avatar', None, nx.DiGraph())    
    fam.add_node(str(eve))

    all_members = fam_nodes + [eve]
    
    print(fam_name) # DEBUG
    if isinstance(fam_name, float):
        fam_name = '(missing)'
    elif len(fam_name) == 0:
        fam_name = '(blank)'

    fam_id = 'time-%i_eve-%i_name-%s' % (fam_start, eve, fam_name)

    # Add family to list
    families_list.extend([(relative, fam_id) for relative in all_members])

    # Save family data
    out_file = 'outputs/families/families_%s.json' % fam_id
    fam_data = nx.json_graph.node_link_data(fam)
    write_json(fam_data, out_file)


# ### Tag lifelogs by family
# This will be used for several subsequent analyses (e.g., migration, comparing different success measures)

# In[ ]:


families_df = pd.DataFrame(families_list, columns=['avatar', 'family'])
families_df.to_csv('outputs/family_playerID.csv', index=False)

