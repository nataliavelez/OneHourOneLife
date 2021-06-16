#!/usr/bin/env python
# coding: utf-8

# # Detect generations

# Natalia Vélez, May 2021
# 
# This script goes through each family and assigns each avatar a generation number.

# In[1]:


import json
import numpy as np 
import pandas as pd
import networkx as nx
from tqdm import notebook

import sys
sys.path.append('..')
from utils import gsearch, str_extract, int_extract, load_json


# ## Load data

# Family registry:

# In[2]:


family_df = pd.read_csv('outputs/family_playerID.csv')
family_df = family_df.sort_values(by='avatar', ascending=True)
family_df.head(20)


# Lifelogs:

# In[3]:


life_df = pd.read_csv('outputs/all_lifelogs_compact.csv')
life_df = life_df[['avatar', 'parent', 'tBirth']]
life_df.head()


# Merged data:

# In[4]:


merge_df = life_df.merge(family_df, on='avatar')
merge_df = merge_df.sort_values(by=['family', 'tBirth']).reset_index(drop=True)
merge_df.head()


# Family graphs:

# In[5]:


graph_files = gsearch('outputs/families/*.json')
graph_files.sort()
print('Found %i files' % len(graph_files))
print(*graph_files[:10], sep='\n')


# Remove duplicate files:

# In[6]:


graph_path_df = pd.DataFrame({'path': graph_files})
graph_path_df['eve'] = graph_path_df.path.apply(lambda s: int_extract('(?<=eve-)[0-9]+', s))

print('Before removing duplicates: %i' % graph_path_df.shape[0])
graph_path_df = graph_path_df.drop_duplicates(subset='eve', keep='first')
print('After: %i' % graph_path_df.shape[0])

# DEBUG ONLY: Limit to first 100 families
# graph_path_df = graph_path_df.head(100)


# ## Search through generations iteratively

# In[7]:


gen_list = []

for idx, row in notebook.tqdm(graph_path_df.iterrows(), total=graph_path_df.shape[0]):
    # Family/eve names
    fam = row.path.replace('outputs/families/families_', '').replace('.json', '')
    eve = row.eve
    
    # Load graph
    G_data = load_json(row.path)
    G = nx.json_graph.node_link_graph(G_data)
    G = nx.relabel.relabel_nodes(G, {n:int(n) for n in G.nodes()}) # make sure nodes are integers
    
    # Compute generation #s for each avatar
    dist_dict = nx.single_source_shortest_path(G, eve)
    dist_list = [(fam, k, len(v)-1) for k,v in dist_dict.items()]
    dist_df = pd.DataFrame(dist_list, columns=['family', 'avatar', 'gen'])
    
    gen_list.append(dist_df)


# In[8]:


gen_df = pd.concat(gen_list)
gen_df.head()


# In[9]:


gen_df.to_csv('outputs/family_generations.csv', index=False)

