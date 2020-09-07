#!/usr/bin/env python
# coding: utf-8

# In[56]:


## Identify lineages
# Natalia Velez, September 2015
# This script identifies family lineages and saves each family to a graph

import pandas as pd
import numpy as np
import networkx as nx
import json, tqdm

## Load inputs
print('Loading inputs:')
parent_df = pd.read_csv('outputs/lineage_input_parents.csv')
eves = pd.read_csv('outputs/lineage_input_eves.csv')
n_eves = eves.shape[0]
print('%i eves detected' % n_eves)

## Helper functions
def search_fam(player):
    descendants = parent_df.loc[parent_df['parent'] == player, 'avatar'].values
    
    for d in descendants:
        descendants = np.append(descendants, search_fam(d))
        
    return descendants

def write_json(data, f):
    with open(f, 'w') as outfile:
        json.dump(data, outfile)
    
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

    if not len(fam_name):
        fam_name = 'nameless'

    fam_id = 'time-%i_eve-%i_name-%s' % (fam_start, eve, fam_name)

    # Add family to list
    families_list.extend([(relative, fam_id) for relative in all_members])

    # Save family data
    out_file = 'outputs/families/families_%s.json' % fam_id
    fam_data = nx.json_graph.node_link_data(fam)
    write_json(fam_data, out_file)

# Save avatar-family pairs
print('Saving avatar-family pairs:')
families_df = pd.DataFrame(families_list, columns=['avatar', 'family'])
families_df.to_csv('outputs/family_playerID.tsv', sep='\t')

