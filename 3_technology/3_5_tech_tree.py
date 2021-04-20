#!/usr/bin/env python
# coding: utf-8

# # Build tech tree
# Grace Deng, August 2020 <br />
# Updated by Natalia Velez, April 2021

# In[ ]:


# %matplotlib inline

import os, re, glob, json
from os.path import join as opj
import numpy as np
import pandas as pd
import json
import pymongo
from tqdm import notebook

# # Debug: Estimate time needed to run job
# import time
# import matplotlib.pyplot as plt
# import seaborn as sns

# sns.set_style('white')
# sns.set_context('talk')

# Debug: Embed html-formatted text
# (Used to do QA on transitions)
from IPython.core.display import display, HTML
def embed(s): return display(HTML(s))


# ## Load game data from database

# Connect:

# In[ ]:


keyfile = '../6_database/credentials.key'

#Connection string
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
print(myclient)

ohol = myclient.ohol
print(ohol)


# Objects:

# In[ ]:


objects = list(ohol.objects.find())
objects = pd.DataFrame(objects)

def obj_name(obj):
    return objects[objects.id == obj].name.values[0]

print('Loading %i objects' % objects.shape[0])
objects.head()


# Transitions:

# In[ ]:


transitions = list(ohol.expanded_transitions.find())
transitions = pd.DataFrame(transitions)

print('Loading %i transitions' % transitions.shape[0])
transitions.head()


# Helper functions: Querying object, transition data

# In[ ]:


### Read from object data
def obj_name(i):
    if i in [0, -1]:
        return 'empty'
    else:
        return objects[objects.id == i].name.values[0]

### Read from transition data
def paths_from(i):
    '''
    Get all uses for object i
    '''
    return (transitions['origActor'] == i) | (transitions['origActor'] == i)

def paths_to(i):
    '''
    Get all paths that produce object i
    (When we build the tech tree, we're going to make the shortest of these paths
    the official 'recipe' for i and use it to calculate the depth of i) 
    '''
    is_product = (transitions['newActor'] == i) | (transitions['newTarget'] == i)
    is_ingredient = paths_from(i)    
    
    return is_product & (~is_ingredient)

def combinations(obj1, obj2):
    '''
    Gets all transitions involving obj1 and obj2, regardless of their relative positions
    '''
    obj1_actor = (transitions['origActor'] == obj1) & (transitions['origTarget'] == obj2)
    obj2_actor = (transitions['origActor'] == obj2) & (transitions['origTarget'] == obj1)   
    
    return obj1_actor | obj2_actor

### Display outputs nicely
trans_cols = ['origActor', 'origTarget', 'newActor', 'newTarget']
def record_transition(row):
    '''
    Converts row in transition df into a mongo-friendly dictionary
    '''
    return row[trans_cols].to_dict()
    

def display_transition(row):
    '''
    Displays transitions in pretty, HTML-formatted text
    '''
    # Get item names
    names = row[trans_cols].apply(obj_name)
    
    # Generate HTML tags
    tag = '<mark style="background-color: %s;">%s</mark>'
    actor_color = '#91d8f2'
    target_color = '#ffbf6b'
    out = '(%s,%s) &#x2192; (%s,%s)' % (tag % (actor_color, names['origActor']),
                                        tag % (target_color, names['origTarget']),
                                        tag % (actor_color, names['newActor']),
                                        tag % (target_color, names['newTarget']))
    
    embed(out)


# Helper functions in action:

# In[ ]:


print(obj_name(72))

print('=== USES ===')
for _, row in transitions[paths_from(72)].iterrows():
    display_transition(row)

print('=== HOW TO GET ===')
for _, row in transitions[paths_to(72)].iterrows():
    display_transition(row)


# ## Search through Tech tree

# Initialize Tech tree dictionary:

# In[ ]:


tech_dict = {o:None for o in objects.id.values}


# Start with natural objects:

# In[ ]:


nat_objs = objects[objects.mapChance > 0].id.values.tolist()
#nat_objs = [32, 33, 63, 153, 50] # DEBUG: Constrained set of natural objects
print('== Starting from %i natural items ==' % len(nat_objs))
print(*['%s (%i)' %(obj_name(o), o) for o in nat_objs], sep='\n')


# Search iteratively through Tech tree
# 
# (Note: This is pretty inefficient, as we repeatedly test the same combinations - fix before scaling up?)

# In[ ]:


# Initialize values
known_objs = [-2, -1, 0] + nat_objs
tech_tree = {o: {'depth': 0, 'recipe': None} for o in known_objs}
counter = 1
n_new = len(known_objs)
combos = [(o_i, o_j) 
          for i,o_i in enumerate(known_objs)
          for j,o_j in enumerate(known_objs[i:])]

# DEBUG: Time each iteration through tech tree
# iter_timer = []

while n_new > 0:
# while counter < 7: # DEBUG: Limit search
    print('=== ITERATION %i ===' % counter)
#     start = time.time()
    
    # Search for viable combinations
    product_list = [transitions[combinations(o_i, o_j)] for o_i, o_j in combos]
    product_df = pd.concat(product_list)
    
    # Which combinations yield new products?
    new_objs = []
    for _, row in product_df.iterrows():
        for e in ['newActor', 'newTarget']:
            product = row[e]
            
            # New products are added to the tech tree
            if product not in tech_tree.keys():
                print('%s (%i)' % (obj_name(product), product))
                new_objs.append(product)
                tech_tree[product] = {}
                tech_tree[product]['recipe'] = record_transition(row)
                
                # Calculate parents' depth
                parents = row[['origActor', 'origTarget']].tolist()
                parents_depth = max([tech_tree[p]['depth'] for p in parents])
                
                # Don't add difficulty for decay transitions
                if min(parents) < 0:
                    tech_tree[product]['depth'] = parents_depth
                else:
                    tech_tree[product]['depth'] = parents_depth + 1 
                
    # Prepare for next iteration
    counter += 1
    n_new = len(new_objs)
    
    # Update combinations in search space    
    if n_new > 0:
        combo_old = [(o_i, o_j) for o_i in known_objs for o_j in new_objs]
        combo_new = [(o_i, o_j) for i,o_i in enumerate(new_objs) for j,o_j in enumerate(new_objs[i:])]
        combos = combo_old + combo_new
        known_objs += new_objs
    else:
        print('(None found)')
    
#     iter_timer.append(time.time()-start)


# Debug: Plot the time it takes to do each iteration through the Tech tree

# In[ ]:


# plt.plot(iter_timer)
# plt.xlabel('Iteration #')
# plt.ylabel('Time per iteration (secs)')


# ## Save to database

# Finally, we're going to format the Tech tree to upload it to the database!

# In[ ]:


tech_df = pd.DataFrame.from_dict(tech_tree, orient='index')
tech_df = tech_df.rename_axis('id').reset_index()

tech_df.tail()


# Debug: Are any craftable items missing from the tech tree? 

# In[ ]:


all_objects = objects[~objects.name.str.contains('@')].id.values
found_objects = tech_df.id.values

missing_objects = np.setdiff1d(all_objects, found_objects)

print('%i objects not in Tech tree' % len(missing_objects))
print(*[(o, obj_name(o)) for o in missing_objects], sep='\n')
#print('...')


# Upload to database:

# In[ ]:


tech_list = tech_df.to_dict('records')
print('%i items in tech tree' % len(tech_list))
print(*tech_list[-10:], sep='\n')

