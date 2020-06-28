"""Read transition files

The object.read_transition function takes in a path to a transition file,
reads it, and returns the transition data as a dictionary.

  Example:
  tpath = '../../OneLifeData7/transitions/659_556.txt'
  build_stanchion = object.read_transition(tpath)
"""

import os, sys, re
import ohol_object as obj

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
   
    # parse original actor/target from filename
    # remove LA/LT/L suffix
    originals = tid.split('_')
    if len(originals) > 2:
        suffix = originals[-1]
        originals = originals[:2]
    else: 
        suffix = ''
    
    lastActor = suffix == 'LA'
    lastTarget = suffix in ['L', 'LT']        
    
    with open(tpath, 'r') as file:
        raw_values = file.read()
    
    raw_values = raw_values.split(' ')
    raw_values = originals + raw_values
    tvals = [obj.parse_obj_values(v) for v in raw_values]
    tdata = dict(zip(tkeys, tvals))
    
    # Last use?
    tdata['lastUseActor'] = lastActor
    tdata['lastUseTarget'] = lastTarget
    
    # Add names
    tdata['origActorName'] = obj.obj_name(tdata['origActor'])
    tdata['origTargetName'] = obj.obj_name(tdata['origTarget'])
    tdata['newActorName'] = obj.obj_name(tdata['newActor'])
    tdata['newTargetName']  = obj.obj_name(tdata['newTarget'])
    
    return tdata

