#!/usr/bin/env python
# coding: utf-8

# # Average proximity to kin vs. non-kin
# Natalia Velez, May 2021

import numpy as np
import pandas as pd
import pymongo
from os.path import join as opj
from scipy.spatial import distance
from tqdm import notebook

# Connect to database:
keyfile = '../6_database/credentials.key'
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
db = myclient.ohol

print(db)
print(db.list_collection_names())

# Load lifelogs:
life_query = db.lifelogs.find({},{'_id': 0, 'player_y': 0})
life_data = pd.DataFrame(list(life_query))
life_data = life_data.rename(columns={'player_x': 'player'}) # clean up data frame

# This method finds everyone that was alive at a given point and their locations of birth.
# Note: in the future, we can combine data from the maplogs to get each contemporary's last known location, rather than their birth location. (Individuals might drift substantially over a lifetime.)
def living_pop(t):
    return life_data[(life_data['tBirth'] <= t) & (life_data['tDeath'] > t)]


# Average distance to kin and non-kin:
def get_avg_distance(row):
    # get time of avatar's birth
    avatar = row.avatar
    avatar_birth = row.tBirth
    avatar_fam = row.family


    # find all of the avatar's contemporaries
    contemporaries = living_pop(avatar_birth)
    contemporaries = contemporaries[contemporaries.avatar != avatar] # exclude self

    if contemporaries.empty:
        # skip if there are no contemporaries
        avg_distance = pd.DataFrame(columns=['kin', 'distance', 'avatar'])
    else:
        # compute distance to kin and non-kin
        contemporaries['kin'] = np.where(contemporaries['family'] == avatar_fam, 'Kin', 'Non-kin')
        contemporaries['distance'] = contemporaries.apply(lambda c: distance.euclidean((row.birthX, row.birthY),
                                                                                       (c.birthX, c.birthY)), axis=1)

        # average distance
        avg_distance = contemporaries.groupby('kin')['distance'].agg('mean').reset_index()
        avg_distance['avatar'] = avatar

    return avg_distance

# Iterate over rows:
dist_list = []
for idx,row in notebook.tqdm(life_data.iterrows(), total = life_data.shape[0]):
    d = get_avg_distance(row)
    dist_list.append(d)

# Use log distance:
dist_df = pd.concat(dist_list)
dist_df['distance'] = dist_df['distance'] + 1
dist_df['log_distance'] = np.log10(dist_df['distance'])

# Save to file
dist_df.to_csv('outputs/average_distance.csv', index=False)
