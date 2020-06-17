"""Read transition files

The object.read_transition function takes in a path to a transition file,
reads it, and returns the transition data as a dictionary.

  Example:
  tpath = '../../OneLifeData7/transitions/659_556.txt'
  build_stanchion = object.read_transition(tpath)
"""

import os, sys, re
import ohol_object

def read_transition(tpath):
    
    tkeys = [
        'origActor',
        'origTarget',
        'newActor',
        'newTarget',
        'autoDecaySeconds',
        'actorMinUseFraction',
        'targetMinUseFraction',
        'reverseUseActor',
        'reverseUseTarget',
        'move',
        'desiredMoveDist',
        'noUseActor',
        'noUseTarget'
    ]
    
    tfile = os.path.basename(tpath)
    tid = tfile.replace('.txt', '')
    originals = tid.split('_')
    
    with open(tpath, 'r') as file:
        raw_values = file.read()
    
    raw_values = raw_values.split(' ')
    raw_values = originals + raw_values
    tvals = [ohol_object.parse_obj_values(v) for v in raw_values]
    tdata = dict(zip(tkeys, tvals))
    
    return tdata

