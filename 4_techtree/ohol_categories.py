#!/usr/bin/env python
# coding: utf-8

import os, sys, re, glob
from os.path import join as opj

# Directories
data_dir = glob.glob('../../OneLifeData*')
data_dir = data_dir[0]
cat_dir = opj(data_dir, 'categories')

cat_files = glob.glob(opj(cat_dir, '*.txt'))
cat_files.sort()

cat_nums = [int(re.search('[0-9]+(?=.txt)', c).group(0)) for c in cat_files]

# Helper: Read category files
def read_cat_file(cat_id):
    
    # cat_str = str(cat_id)

    ## Read object file
    cat_file = opj(cat_dir, '%i.txt' % cat_id)
    with open(cat_file, 'r') as file:
        raw_data = file.read().splitlines()
        
    return raw_data

# Check if object ID describes a category
def is_cat(obj_id):
    
    obj_path = opj(cat_dir, '%s.txt' % obj_id)
    return os.path.exists(obj_path)

# Search for object ID within all category files (might be very slow)
def find_cat(obj_id):
    
    cat_matches = []
    
    # If object ID matches category, return itself
    if is_cat(obj_id):
        cat_matches = [obj_id]
        
    # Otherwise, search for category among cat children
    else: 
        cat_matches = []
        for c in cat_nums:
            children = read_cat(c)
            if obj_id in children:
                cat_matches.append(c)

    return cat_matches

# Main fun: Read objects contained within category
def read_cat(category):
    cat_data = read_cat_file(category)

    obj_start = [i for i,c in enumerate(cat_data) if 'numObjects' in c]
    obj_start = obj_start[0]

    child = cat_data[obj_start+1:]
    child = [int(c) for c in child]

    return child
