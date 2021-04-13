#!/usr/bin/env python
# coding: utf-8

import os, sys, re, glob
from os.path import join as opj
from utils import int_extract
from pathlib import Path

# Directories
data_dir = (Path(__file__).parent / "../OneLifeData7").resolve()
cat_dir = opj(data_dir, 'categories')

# Helper: Read category files
def read_cat_file(cat_id):
    
    # cat_str = str(cat_id)

    ## Read object file
    cat_file = opj(cat_dir, '%i.txt' % cat_id)
    with open(cat_file, 'r') as file:
        raw_data = file.read().splitlines()
        
    return raw_data


def get_children(category):
    cat_data = read_cat_file(category)

    obj_start = [i for i,c in enumerate(cat_data) if 'numObjects' in c]
    obj_start = obj_start[0]

    child = cat_data[obj_start+1:]
    child = [int(c.split()[0]) for c in child] #edge case: [1958 0.167000]

    return child

def read_cat(category):
    
    raw_data = read_cat_file(category)
    
    # Parent ID
    parent = [i for i in raw_data if 'parentID' in i]
    parent = int_extract('(?<=parentID=)[0-9]+', parent[0])
    
    # Special properties
    pattern = any('pattern' in i for i in raw_data)
    probabilistic = any('probSet' in i for i in raw_data)
    n = [i for i in raw_data if 'numObjects' in i]
    n = int_extract('(?<=numObjects=)[0-9]+', n[0])
    
    # Children
    child_pattern = re.compile('^[0-9].+')
    children_raw = [i for i in raw_data if child_pattern.match(i)]
    
    if probabilistic:
        children,probs = zip(*[c.split() for c in children_raw])
        children = [int(c) for c in children]
        probs = [float(p) for p in probs]
    else:
        children = [int(c) for c in children_raw]
        probs = None
    
    # Put into dictionary
    cat_data = {'parentID': parent,
                'numObjects': n,
                'probabilistic': probabilistic, 
                'pattern': pattern,
                'children': children,
                'probs': probs}
    
    return cat_data
