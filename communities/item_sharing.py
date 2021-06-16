#!/usr/bin/env python
# coding: utf-8

# # Detect instances of item sharing
# Written by Grace Deng, edited by Natalia Velez
# May 2021

import json, pymongo, os
import pandas as pd
import numpy as np
import networkx as nx
from tqdm import notebook

import sys
sys.path.append('..')
from utils import int_extract, gsearch


# Connect to database:
keyfile = '../6_database/credentials.key'
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
db = myclient.ohol

print(db)
print(db.list_collection_names())


# ## Load data
# Note: To save on calls to the database, we're loading a local copy of the data
map_files = gsearch('../3_technology/outputs/maplog/*.tsv')
map_files.sort()

print('Found %i map files' % len(map_files))
print(*map_files[:10], sep='\n')

# Helper functions: Get unique avatars who accessed a location
def unique_avatars(d):
    avatars = [v['avatar'] for k,v in d.items()]
    avatars = [a for a in avatars if a > 0]
    return len(np.unique(avatars))


# Main loop: This loop builds a directed graph. In order to draw an edge between players, two conditions must be met:
# 
# * Both avatars must have interacted with the same spot consecutively.
# * Both avatars must be different from another, and they must be actual avatars. (This excludes decay transitions, where avatar = -1)
# * The spot must be occupied before the second avatar interacts with it. (This excludes transitions where a spot was previously empty, and is then filled by a new avatar.)
# 
# Each edge contains two attributes:
# 
# * `weight`: Number of directed interactions from previous avatar to current avatar. Increments by 1 with each interaction.
# * `shared`: List of object IDs shared between players
invalid_items = ['0', '87', '752', '1920', '3053'] # exclude fresh bones and empty squares
G = nx.DiGraph()
last_known = pd.DataFrame(columns=['x','y','t','object_id','avatar'])

for f in notebook.tqdm(map_files):
    map_data = pd.read_csv(f, sep='\t')

    # Shift simultaneous events by .001 seconds (smaller than the current time resolution)
    map_data['t'] = np.where(map_data.duplicated(subset=['x','y','t']), map_data['t']+.001, map_data['t'])
    map_data = map_data.drop_duplicates(subset=['x','y','t'],keep='last')
    map_data['avatar'] = map_data['avatar'].astype(np.int)

    t_elapsed = map_data.agg({'t': ['min', 'max']}).diff().dropna()
    print('===========')
    print('Loaded data from: %s' % f)
    print('Analyzing %i minutes of gameplay' % (t_elapsed.values[0][0]/60))
    print('%i duplicate events' % (np.sum(map_data.duplicated(subset=['x','y','t']))))

    # Make a nested dictionary
    # `(x,y):{t:{'object_id': obj, 'avatar': avatar}}`
    map_dict = map_data.groupby(['x','y']).apply(lambda row: row.set_index('t').to_dict('index')).to_dict()
    print('Original length: %i' % len(map_dict))

    # Filter out cases with no interactions
    # a. Location is only accessed once
    # b. Only one valid avatar (not -1) changes the map state
    map_dict = {k:v for k,v in map_dict.items() if (len(v) > 1) & (unique_avatars(v) > 1)}
    print('%i map locations found' % len(map_dict))

    # Clean up data
    map_df = [pd.DataFrame.from_dict(v, orient='index') for k,v in map_dict.items()]
    map_df = pd.concat(map_df).reset_index().rename(columns={'index':'t'})
    
    # Add last-known states from previous map file
    map_df = pd.concat([last_known, map_df])
    print('Adding last-known state of %i locations' % last_known.shape[0])
    print('Final length: %i' % map_df.shape[0])

    # Add to graph
    for loc,loc_data in map_df.groupby(['x','y']):
        # Initial values
        prev_avatar = -1
        prev_obj = 0

        # Iterate over rows
        for idx,row in loc_data.iterrows():

            # Get current item and avatar
            curr_avatar = row.avatar
            curr_obj = row.object_id

            # Check if it's a valid transition
            different_avatars = prev_avatar != curr_avatar
            non_decay = -1 not in (prev_avatar, curr_avatar)
            valid_avatars = different_avatars & non_decay
            occupied_spot = prev_obj not in invalid_items

            # Add transition
            if  valid_avatars & occupied_spot:
                # Update the weight of existing connections
                if G.has_edge(prev_avatar, curr_avatar): 
                    G[prev_avatar][curr_avatar]['weight'] += 1
                    G[prev_avatar][curr_avatar]['shared'].append(prev_obj)
                    G[prev_avatar][curr_avatar]['t'].append(row.t)
                # Initialize new ones
                else:
                    G.add_edge(prev_avatar, curr_avatar, weight=1, shared=[prev_obj], t=[row.t])

            # Set up next iteration
            prev_avatar = curr_avatar
            prev_obj = curr_obj
    
    last_known = map_df.drop_duplicates(subset=['x','y'], keep='last')
    print('Passing data from %i locations to next iteration' % last_known.shape[0])


# Save graph to file:
G_data = nx.readwrite.json_graph.node_link_data(G)
with open('outputs/item_interactions_graph.json', 'w') as outfile:
    json.dump(G_data, outfile)


# Upload linkage information to database:
link_col = db.item_interactions
link_col.insert_many(G_data['links'])

