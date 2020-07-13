"""Read transition files

The object.read_transition function takes in a path to a transition file,
reads it, and returns the transition data as a dictionary.

  Example:
  tpath = '../../OneLifeData7/transitions/659_556.txt'
  build_stanchion = object.read_transition(tpath)
"""

import os, sys, re
import ohol_objects as obj

# Parse decay time
def decay_time(t0):
    if t0 < 0:
        t = -t0 * 60 * 60 # hours are in the negative
    else:
        t = t0 # everything else is positive 
    
    return t

# Check if is tool
def is_tool(tdata):
    
    tool_kw = re.search('broken|just murdered|empty|needle|bottle|bowl', tdata['newActorName'], re.IGNORECASE)
    matches_tool = tool_kw is not None
   
    is_obj = tdata['origActor'] > 0
    is_persistent = matches_tool | (tdata['origActor'] == tdata['newActor'])
    
    return is_obj & is_persistent

# MAIN FUNCTION: Returns dict of transition data
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
    
    # Extra properties (from OneTech repo)
    tool_bool = is_tool(tdata)
    tdata['autoDecaySeconds'] = decay_time(tdata['autoDecaySeconds'])
    tdata['isTool'] = tool_bool
    
    return tdata

# Parse read_transition, returning only objects
def read_objs(tpath):
    
    tdata = read_transition(tpath)
    objs = [(tdata['origActor'], tdata['origTarget']), (tdata['newActor'],  tdata['newTarget'])]
    
    return objs