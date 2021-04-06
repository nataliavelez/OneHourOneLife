
# coding: utf-8

# # Identify family interactions based on if they shared the same objects
get_ipython().magic('matplotlib inline')

import os, re, glob, datetime, json
from os.path import join as opj
import pandas as pd
import numpy as np
import scipy.stats
from tqdm import tqdm
from datetime import datetime

from tqdm.notebook import tqdm
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from networkx.drawing.nx_agraph import graphviz_layout
import community as community_louvain


# ## load data
baseDir = '../data/publicMapChangeData/bigserver2.onehouronelife.com/'

#useful functions
str_extract = lambda pattern, s: re.search(pattern, s).group(0)
int_extract = lambda pattern, s: int(str_extract(pattern, s))


#read files
files_tot = []
for ts in glob.glob(baseDir + '*'):
    files_tot.append(ts)

file_names = []
for f in files_tot:
    fn = f.split('/')[-1]
    file_names.append(fn)
file_names.sort(key=lambda f: int_extract('[0-9]+(?=)', f))


# create a dictionary for mapSeed -- mapLog
map_seeds = [int_extract('[0-9]+(?=)', fn) for fn in file_names if 'mapSeed' in fn]
print("Looking at mapSeeds: ", map_seeds)


file_dict = {}
for fn in file_names:
    timestamp = int_extract('[0-9]+(?=)', fn)
    if timestamp in map_seeds:
        map_start = timestamp
        file_dict[map_start] = [timestamp]
    else:
        file_dict[map_start].append(timestamp)




# ### test: only look at the first slice
subset = file_dict[list(file_dict.keys())[0]]
print("Now parseing mapChange data: ", subset)

start = pd.read_csv(baseDir + str(subset[0]) + 'time_mapLog.txt')
time0 = float(start.columns[0].split(": ")[1])


col = ['time','locX','locY','obj','playerID']
data = pd.DataFrame(columns = col)
for i in subset:
    mydf = pd.read_csv(baseDir + str(i) + 'time_mapLog.txt')
    start_time = float(mydf.columns[0].split(": ")[1])
    mydf[['time','locX','locY','obj','playerID']] = mydf[mydf.columns[0]].str.split(" ", expand=True)
    mydf = mydf.dropna()
    mydf['time'] = mydf['time'].astype(float) + start_time - time0
    mydf['playerID'] = mydf['playerID'].astype(int)
    mydf = mydf[col]
    data = data.append(mydf, ignore_index = True)

duration = max(data.time) - min(data.time)
print("map durating: ", duration)



# ### load family data and write a find_family function
fam= pd.read_csv('../2_demographics/outputs/family_playerID.tsv', sep = '\t', index_col = 0)


def find_fam(playerId):

    family = fam.loc[fam['playerID'] == playerId,'family'].tolist()
    if len(family):
        fam_name = family[0].split('-')[-1]
    else:
        fam_name = fam_name = "UnKnown"

    return fam_name

# check if every player has a last name (No!) and find the number of players in a family
fam_player_dict = {}
player_fam_dict = {}
for i in data['playerID'].unique():
    if (i != -1) and (i != 0):
        family = fam.query('playerID == @i')['family'].values
        if len(family):
            family_name = family[0].split('-')[-1]
            player_fam_dict[i] = family_name
            if family_name in fam_player_dict.keys():
                fam_player_dict[family_name] = fam_player_dict[family_name]+1
            else:
                fam_player_dict[family_name] = 1


# ## record connection in a dataframe
# Sort by location and time
parsed = data.sort_values(by = ['locX','locY','time']).copy()
# tag previous player and object at this location
parsed['same_loc'] = parsed.locY.eq(parsed.locY.shift())
parsed['all_prev_obj'] = parsed.obj.shift()
parsed['prev_obj'] = parsed[parsed['same_loc']==True]['all_prev_obj']
parsed['all_prev_playerID'] = parsed.playerID.shift()
parsed['prev_playerID'] = parsed[parsed['same_loc']==True]['all_prev_playerID']
parsed = parsed[['time','locX','locY','obj','playerID','prev_obj','prev_playerID']]

# take data where an object at a location was changed by a different player
parsednew = parsed.loc[(parsed.prev_obj != "0") & (parsed.playerID != parsed.prev_playerID)
                       & (parsed.prev_playerID != -1) & (parsed.playerID != -1)].dropna()
parsednew = parsednew.sort_values(by = ['time'])
##(parsed.obj != parsed.prev_obj) Don't need the object to change? Some targets won't change




# ## Louvain
G = nx.from_pandas_edgelist(parsednew, 'playerID', 'prev_playerID')
partition = community_louvain.best_partition(G)
# plt.figure(figsize=(50,50))
# pos = nx.spring_layout(G)
# nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=100, node_color=list(partition.values()))
# nx.draw_networkx_edges(G, pos, alpha=0.5)
# plt.savefig('louvain.png', dpi = 100)


# Tag community to each player
def find_community(player):
    try:
        return partition[player]
    except KeyError:
        return np.nan

data_louvain = data.loc[data.playerID != -1].copy()
data_louvain['community'] = data_louvain['playerID'].apply(find_community)
data_louvain['objID'] = data_louvain['obj'].apply(lambda x: int_extract('[0-9]+', x))
data_louvain = data_louvain.dropna()


print("Summarizing innovations in communities")
community_innovations = pd.DataFrame()
for i in data_louvain.community.unique():
    comm_subset = data_louvain.loc[data_louvain.community == i]
    comm_innovs = comm_subset.groupby(['objID'])['playerID'].apply(lambda x: x.tolist()[0]).to_frame().reset_index()
    comm_innovs_sum = comm_innovs.groupby(['playerID'])['objID'].count().to_frame().reset_index()
    comm_innovs_sum['community'] = i
    community_innovations = community_innovations.append(comm_innovs_sum)
community_innovations = community_innovations.reset_index()



avatars = parsednew.playerID.unique()
same_family = []
same_comm = []
for i in avatars:
    others = parsednew.loc[parsednew.playerID==i]['prev_playerID'].tolist()
    for j in others:
        try:
            same_family.append(player_fam_dict[i] == player_fam_dict[j])
        except KeyError: ##family name not defined
            same_family.append(np.nan)
        same_comm.append(partition[i] == partition[j])



###### can get rid of this once we tag every player with a family
with_fam_list = []
for i in range(len(same_family)):
    if (same_family[i] is True) or (same_family[i] is False):
        with_fam_list.append(i)


#tag families and communities
mydf = pd.DataFrame()
mydf['same_fam'] = same_family
mydf['same_comm'] = same_comm

mydf = mydf.dropna()
mydf['agreement'] = mydf.same_fam.eq(mydf.same_comm)


### summary statistics

# What's the egree of correlation?
p_agree = len(mydf.loc[mydf.agreement==True])/len(mydf)
print("Degree of correspondence between families and communities: ", p_agree)


# How many families are there?
num_family = len(fam_player_dict.keys())



# How many partitions are there?
num_partition = max(partition.values())


# create a player-family-community df
playerdf = pd.DataFrame()
playerdf['playerID'] = avatars
playerdf['family'] =playerdf['playerID'].map(find_fam)
playerdf['partition'] =playerdf['playerID'].map(lambda x: partition[x])


# How many unique families are in each community?
comm_fam = playerdf.groupby('partition')['family'].apply(lambda x: len(set(x))).to_frame().reset_index()

# How many communities are families spread out into?
fam_comm = playerdf.groupby('family')['partition'].apply(lambda x: len(set(x))).to_frame().reset_index()





# ## plot interactions by family
#
# # count the number of interactions between players (defined as two players interacted with the same object)
# grouped = parsednew.groupby(['playerID','prev_playerID'])['time'].count().to_frame().reset_index()
# grouped_with_fam = grouped.copy()
# grouped_with_fam['player_fam'] = grouped_with_fam['playerID'].map(find_fam)
# grouped_with_fam['prev_player_fam'] = grouped_with_fam['prev_playerID'].map(find_fam)
#
# fam_df = grouped_with_fam.groupby(['player_fam','prev_player_fam'])['time'].count().to_frame().reset_index()
# fam_df = fam_df.query('(player_fam != prev_player_fam) and (player_fam != "UnKnown") and (prev_player_fam != "UnKnown")')
# fam_df.sort_values(by = 'time', ascending = False)
#
# # turn df to graph representation
# G2 = nx.from_pandas_edgelist(fam_df, 'prev_player_fam','player_fam', None, nx.DiGraph())
#
# # set node size proportional to family size
# ns = [200*np.sqrt(fam_player_dict[i]) for i in G2.nodes]
#
# # set edge width proportional to number of interactions
# s = sum(fam_df['time'].tolist())
# ew = []
# for (u,v) in G2.edges:
#     times = fam_df.loc[(fam_df.prev_player_fam == u) & (fam_df.player_fam == v)]['time'].values[0]
#     weight = 20*np.sqrt(times/s)
#     ew = np.append(ew, weight)
#
# # draw graph
# plt.figure(figsize=(15,15))
# pos = nx.spring_layout(G2, k=0.8, iterations=20) ##make nodes further apart
# nx.draw(G2, pos=pos, with_labels= True, node_color='skyblue', width=ew, node_shape='s', node_size=ns, font_size=10)
#
# plt.savefig('plots/fam_directed.png',dpi = 100)
