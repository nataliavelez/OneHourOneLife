"""Read object files

The object.read_obj function takes in an object ID, searches for the
corresponding object file in the OneLifeData7 repository, and returns 
the object data as a dictionary.

  Example:
  stone_dict = object.read_obj(33)
"""

import os, sys, re

# Helper: Read object files
def read_obj_file(obj_id):
    
    obj_str = str(obj_id)

    ## Read object file
    obj_file = '../../OneLifeData7/objects/%s.txt' % obj_str
    with open(obj_file, 'r') as file:
        raw_data = file.read().splitlines()
        
    return raw_data

# Helper: Clean up data from original object file
def clean_obj_data(raw_data):
    data = raw_data[:]
    data[1] = 'name=%s' % data[1]

    # Clean up comments in name field, if any
    data[1] = re.sub(r'#(?=.+$)', ' -', data[1])
    data[1] = re.sub(r',', ' &', data[1])

    # Split timestretch into a new field
    data_str = '\n'.join(data)
    data_str = data_str.replace('#timeStretch', '\ntimeStretch')

    # Split comma-separated fields into new lines
    data_str = re.sub(r',(?=[A-Za-z]+\=)', '\n', data_str)

    # Remove comments
    data_str = re.sub(r'#.+(?=\n)', '', data_str)

    # Split datastring into a list again
    data = data_str.split('\n')
    
    return data

# Helper: Parse values
def parse_obj_values(v0):
    v_list = v0.split(',') # Split lists
    parsed_v = []
    
    for vi in v_list: # Parse numbers
        try: # Try to convert things to numerics
            
            if '.' in vi: # parse floats
                parsed_v.append(float(vi))
            else: # parse ints
                parsed_v.append(int(vi))
                
        except ValueError: # leave strings be
            parsed_v.append(vi)
            
    # Flatten singletons
    if len(parsed_v) == 1:
        parsed_v = parsed_v[0]
    
    return parsed_v


# Main function: Takes in an object ID (e.g., 3044) and returns object properties as a dictionary
def read_obj(obj_id):
    
    raw_data = read_obj_file(obj_id) # From object file
    data = clean_obj_data(raw_data) # Cleaned up 
    
    # Split list of strings into key-value pairs
    data_tuples = [s.split('=') for s in data]
    
    # Parse values
    data_keys, data_values_raw = zip(*data_tuples)
    data_values = [parse_obj_values(v) for v in data_values_raw]
    data_dict = {k:v for k,v in zip(data_keys, data_values)}
    
    return data_dict

# Specifically returns name
def obj_name(obj_id):
    if obj_id < 1:
        name = 'Empty'
    else:
        obj_dict = read_obj(obj_id)
        name = obj_dict['name']
        
    return name