#!/usr/bin/env python
# coding: utf-8

'''Read technological tree

This module contains several useful functions to retrieve information from the tech tree:

```
import ohol_tech as tech
tech.tech_tree # Tech tree in dictionary form
depths,recipe = tech.get_recipe([obj]) # Returns 

```
'''


import pymongo, textwrap, pydot
import numpy as np
import pandas as pd
from IPython.core.display import Image, display, HTML
from itertools import groupby
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
from utils import int_extract
from networkx.drawing.nx_pydot import graphviz_layout

from pathlib import Path
from utils import opj


# In[12]:


## Connect to database
def connect():
     #Connection string
    key_dir = (Path(__file__).parent / "6_database/").resolve()
    keyfile = opj(key_dir, 'credentials.key')
#     keyfile = '6_database/credentials.key'
    creds = open(keyfile, "r").read().splitlines()
    myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 
    ohol = myclient.ohol
    
    return ohol

## Load tech tree
def load_tech_tree():
    
    ohol = connect()
    tech_df = pd.DataFrame(list(ohol.tech_tree.find()))
    tech_df = tech_df[['id', 'depth', 'recipe']]
    tech_df = tech_df.set_index('id')

    tech_tree = tech_df.to_dict('index')
    return tech_tree
tech_tree = load_tech_tree()

## Load objects from database
def load_objects():
    
    ohol = connect()
    obj_df = pd.DataFrame(list(ohol.objects.find()))
    obj_df = obj_df[['id', 'name']]

    return obj_df
objects = load_objects()

## Load transitions
def load_transitions():
    
    ohol = connect()
    trans_df = pd.DataFrame(list(ohol.expanded_transitions.find()))
    trans_df = trans_df[['origActor', 'origTarget', 'newActor', 'newTarget']]
    
    return trans_df

transitions = load_transitions()

## Object depth
def depth(obj):
    return tech_tree[obj]['depth']


# In[13]:


def obj_name(obj):
    
    if obj < 1:
        return 'empty'
    else:
        return objects[objects.id == obj].name.values[0]


# In[14]:


## Get recipe
def search_recipe(obj, recipeList=None):
    '''
    Returns full recipe by searching recursively through the tech tree
    '''
    # If recipe is empty, start a new list
    if recipeList is None:
        recipeList = []
    
    # Search recursively through object parents
    prev_step = tech_tree[obj]['recipe']
    if prev_step is not None:
        recipeList.append(prev_step)
        parents = [prev_step['origActor'], prev_step['origTarget']]
        for p in parents:
            search_recipe(p, recipeList)
    return recipeList

def get_recipe(obj):
    '''
    Cleans up the outputs of `search_recipe` by removing duplicate transitions
    and sorting transitions from simplest to most complex
    '''
    # Remove duplicate steps
    raw_recipe = search_recipe(obj)
    trimmed_recipe = list(map(dict, set(tuple(sorted(d.items())) for d in raw_recipe)))
    
    # Order transitions from simplest to most complex
    depths = [max(depth(e['newActor']), depth(e['newTarget'])) for e in trimmed_recipe] 
    ordered_recipe = list(zip(depths, trimmed_recipe))
    ordered_recipe.sort(key=lambda l:l[0])
    
    # Returns two lists: depths, recipe steps
    if len(ordered_recipe):
        depths,steps = list(zip(*ordered_recipe)) 
    else:
        depths = []
        steps = []
    
    return depths, steps


# In[15]:


def get_ingredients(obj_recipe):
    ingredients = [(step['origActor'], step['origTarget']) for step in obj_recipe]
    ingredients_unwrapped = [i for step in ingredients for i in step if i > 1]
    return set(ingredients_unwrapped)


# In[16]:


## Render single transition in HTML
def embed(s): return display(HTML(s))
    
def display_transition(recipe_step):
    '''
    Displays transitions in pretty, HTML-formatted text
    '''
    # Get item names
    names = {k:obj_name(v) for k,v in recipe_step.items()}
    
    # Generate HTML tags
    tag = '<mark style="background-color: %s;">%s</mark>'
    actor_color = '#91d8f2'
    target_color = '#ffbf6b'
    out = '(%s,%s) &#x2192; (%s,%s)' % (tag % (actor_color, names['origActor']),
                                        tag % (target_color, names['origTarget']),
                                        tag % (actor_color, names['newActor']),
                                        tag % (target_color, names['newTarget']))
    
    embed(out)

def display_recipe(obj):
    '''
    Render all transitions into a recipe
    '''
    
    depths,recipe = get_recipe(obj)
    recipe_tuple = list(zip(depths,recipe))
    
    for depth,group in groupby(recipe_tuple, key=lambda l:l[0]):
        embed('<h2>Step %i</h2>' % depth)
        for step in group:
            display_transition(step[1])
            
def node_name(obj, w=15):
    '''
    Takes an object and returns sensible node names (text-wrapped string)
    '''
    name = obj_name(obj)
    name_wrapped = textwrap.wrap(name,width=w)
    return '\n'.join(name_wrapped)
 
def display_pydot(pdot):
    '''
    Display graphs inline
    '''
    plt = Image(pdot.create_png())
    display(plt)


# In[25]:


def tree_graph(obj):
    ## Build graph 
    # Get recipe and object depths
    depths,recipe = get_recipe(obj)
    ingredients = list(get_ingredients(recipe))
    nodes = ingredients + [obj]
    max_depth = max(depths)

    # Sort recipe from the end product down
    recipe_df = pd.DataFrame(recipe)
    recipe_df['depth'] = depths
    recipe_df = recipe_df.sort_values('depth').reset_index(drop=True)

    # Helper functions: Identify next transition down
    def is_product(p): return (recipe_df.newActor == p) | (recipe_df.newTarget == p)
    def is_ingredient(p): return (recipe_df.origActor == p) | (recipe_df.origTarget == p)

    # Create nodes
    G = pydot.Dot(graph_type='digraph', rankdir='LR', strict = True)
    ranked_groups = [[] for _ in range(max_depth+1)]
    for i in nodes:
        if i == obj:
            rank = max_depth+1
        else:
            # Find earliest step that ingredient is involved in
            involved_in = recipe_df[is_ingredient(i)]
            rank = np.min(involved_in.depth)

        node_i = pydot.Node(node_name(i), shape='box', width=2, height=1, fontname='Helvetica Neue')
        G.add_node(node_i)
        ranked_groups[rank-1].append((i, node_i))

    # Rank nodes    
    for group in ranked_groups:
        S = pydot.Subgraph(rank='same')
        for node_i in group:
            S.add_node(node_i[1])
        G.add_subgraph(S)

    # Create edges
    products = [str(obj)]
    expanded = []

    for _, row in recipe_df.iterrows():
        # Identify parents and product of each step
        parents = [row['origActor'], row['origTarget']]
        parents = [p for p in parents if p > 0]

        products = [row['newActor'], row['newTarget']]
        products = [p for p in products if (p in nodes) & (p not in parents)]

        for p_i in parents:
            for p_j in products:
                edge_ij = pydot.Edge(node_name(p_i), node_name(p_j))
                G.add_edge(edge_ij)

    return G


# In[26]:


def tree_proximity(obj1, obj2):
    sets = []

    for obj in (obj1, obj2):
        _,recipe = get_recipe(obj)
        ingredients = get_ingredients(recipe)
        sets.append(list(ingredients) + [obj])

    n1 = len(sets[0])
    n2 = len(sets[1])

    unique1 = np.setdiff1d(sets[0], sets[1])
    unique2 = np.setdiff1d(sets[1], sets[0])

    p1given2 = (n1 - len(unique1))/n1
    p2given1 = (n2 - len(unique2))/n2

    proximity = min(p1given2, p2given1)
    return proximity

