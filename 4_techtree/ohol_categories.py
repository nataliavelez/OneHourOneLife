#!/usr/bin/env python
# coding: utf-8

import os, sys, re, glob
from os.path import join as opj

# Directories
data_dir = glob.glob('../../OneLifeData*')
data_dir = data_dir[0]
cat_dir = opj(data_dir, 'categories')

# Helper: Read category files
def read_cat_file(cat_id):
    
    # cat_str = str(cat_id)

    ## Read object file
    cat_file = opj(cat_dir, '%i.txt' % cat_id)
    with open(cat_file, 'r') as file:
        raw_data = file.read().splitlines()
        
    return raw_data


def cat_children(category):
    cat_data = read_cat_file(category)

    obj_start = [i for i,c in enumerate(cat_data) if 'numObjects' in c]
    obj_start = obj_start[0]

    child = cat_data[obj_start+1:]
    child = [int(c.split()[0]) for c in child] #edge case: [1958 0.167000]

    return child
