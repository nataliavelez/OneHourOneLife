#!/usr/bin/env python
# coding: utf-8

# # Detecting discoveries
# Natalia Vélez, July 2020

# In[ ]:


# %matplotlib inline
import matplotlib as mpl
mpl.use('Agg')

import os, re, glob, tqdm
import pandas as pd
import numpy as np
from os.path import join as opj

import scipy.stats
from gini import gini
from statsmodels.distributions.empirical_distribution import ECDF

import matplotlib.pyplot as plt
import seaborn as sns
# from tqdm import notebook

sns.set_style("white")
sns.set_context("talk")


# ## Prepare data

# Helper: Extract timestamp from filenames

# In[ ]:


def file_start(f):
    t0 = re.search('((?<=start-)|(?<=time-))[0-9]+', f).group(0)
    return int(t0)


# Family labels:

# In[ ]:


fam_file = '../2_demographics/outputs/family_playerID.tsv'
fam_df = pd.read_csv(fam_file, sep='\t', index_col=0)
#fam_df = fam_df.rename(columns={'playerID':'player_id'})
fam_df['fam_start'] = fam_df['family'].apply(file_start)
print('Labeling players by family:')
print(fam_df.head())


# Family fitness:

# In[ ]:


fit_file = '../2_demographics/outputs/family_fitness.tsv'
fit_df = pd.read_csv(fit_file, sep='\t', index_col=None)
print('Analyzing %i families' % fit_df.shape[0])
print(fit_df.head())


# Object depth:

# In[ ]:


depth_file = 'tech_tree/num_unique_ingredients.csv'
depth_df = pd.read_csv(depth_file)
depth_df = depth_df.rename(columns={'id': 'object_id', 'num_ingredients': 'depth'})
depth_df = depth_df[['object_id', 'depth']]
print('Repertoire depth:')
print(depth_df.head())


# Find map change files:

# In[ ]:


gsearch = lambda *args: glob.glob(opj(*args))
map_dir = 'outputs/maplog/'

map_files = gsearch(map_dir, '*.tsv')
map_files.sort()

print('Found %i map files' % len(map_files))
print(*map_files[:10], sep='\n')


# Find map seed changes:

# In[ ]:


seed_file = 'outputs/seed_changes.txt'
with open(seed_file, 'r') as handle:
    seed_data = handle.read().splitlines()

seed_changes = np.array([int(s) for s in seed_data])
seed_changes = np.sort(seed_changes)

print('%i world seeds' % len(seed_changes))
print(seed_changes)


# Find seed file corresponding to timestamp:

# In[ ]:


def find_seed(tstamp):
    
    lag = tstamp - seed_changes
    seeds = seed_changes[lag >= 0]
    if len(seeds):
        seed = seeds[-1]
    else: # Special: First log file
        seed = seed_changes[0]
            
    return seed


# Group mapchange files by world seed:

# In[ ]:


file_df = pd.DataFrame(map_files, columns=['file'])
file_df['tstamp'] = file_df.file.str.extract('(?<=start-)([0-9]+)')
file_df['tstamp'] = file_df['tstamp'].astype(np.int)
file_df['seed'] = file_df.tstamp.apply(find_seed)
file_df = file_df.sort_values('tstamp')
file_df['seed_start'] = file_df.groupby('seed')['tstamp'].transform('min')
print(file_df.head())


# ## Identify discoveries

# Helper function: Clean up individual map change files

# In[ ]:


def process_maplog(f):
    s_df = pd.read_csv(f, sep='\t', index_col=None)
    #s_df = s_df.rename(columns={'player_id': 'avatar'})
    
    # Fix timestamps to start of world seed
    t_log = file_start(f)
    s_df['t_epoch'] = s_df['t_elapsed'] + t_log

    # Player events only
    s_df = s_df[s_df['avatar'] > 0]

    # Parse object IDs, removing special identifiers
    s_df['object_id'] = s_df.object_id.str.replace('(^f|v[0-9]+|u[0-9]+)', '')
    s_df['object_id'] = s_df['object_id'].astype(np.int)

    # Only interactions with valid objects
    s_df = s_df[(s_df['object_id'] > 0) & (s_df['object_id'] < 5000)]
    s_df = s_df[s_df['object_id'] != 87] # Exclude fresh graves (player deaths)

    # Tag players by family    
    s_df = pd.merge(s_df, fam_df, on='avatar')
    s_df['t_fam'] = s_df['t_epoch'] - s_df['fam_start'] # t=0 at Eve birth

    return s_df


# Identify discoveries

# In[ ]:


def id_discoveries(maplog):

    # Prepare dataframe
    discoveries = maplog.copy()
    discoveries = discoveries[['seed', 't_epoch', 't_fam','family', 'object_id', 'x', 'y', 'avatar']]
    discoveries = discoveries.sort_values('t_fam')

    # Find the first time an object appears in family's repertoire
    discoveries = discoveries.groupby(['seed', 'family', 'object_id']).first()
    discoveries = discoveries.reset_index()
    discoveries = pd.merge(discoveries, depth_df)
    discoveries = discoveries.sort_values(['family', 't_fam'])

    return discoveries


# Change in repertoire size over time:

# In[ ]:


def discoveries_dynamic(discoveries):
    disc_count = discoveries.copy()
    disc_count = disc_count.sort_values(['family', 't_epoch'])
    disc_count['is_obj'] = (disc_count['object_id'] > 0)*1
    disc_count['count'] = disc_count.groupby('family')['is_obj'].cumsum()
    disc_count = disc_count[['seed', 'family', 'object_id', 't_epoch', 'count']]
    disc_count = disc_count.reset_index(drop=True)
    return disc_count


# Count # of discoveries per player:

# In[ ]:


def lorenz_inputs(discoveries):
    # Return a count of # discoveries for each family member
    n_discoveries = discoveries.groupby(['family','avatar'])['object_id']
    n_discoveries = n_discoveries.agg('count').reset_index()
    n_discoveries = n_discoveries.rename(columns={'object_id': 'n'})

    # Fill in missing family members (no discoveries)
    log_fams = np.unique(discoveries['family'])
    all_fam = fam_df.copy()
    all_fam = all_fam[['family', 'avatar']]
    all_fam = all_fam[all_fam['family'].isin(log_fams)].reset_index(drop=True)

    # Total number of discoveries
    n_discoveries_full = pd.merge(all_fam, n_discoveries, how='outer')
    n_discoveries_full['n'] = n_discoveries_full['n'].fillna(0).astype(int)
    
    # Family totals
    fam_totals = n_discoveries_full.groupby('family')['n'].agg(['sum', 'count']).reset_index()
    n_discoveries_full = pd.merge(n_discoveries_full, fam_totals, on='family', how='outer')
    n_discoveries_full = n_discoveries_full.sort_values(['family', 'n'], ascending=True)
    
    # Cumulative players and discoveries
    n_discoveries_full['cum_players'] = n_discoveries_full.groupby('family')['n'].cumcount()+1
    n_discoveries_full['cum_players'] = n_discoveries_full['cum_players']/n_discoveries_full['count']
    
    n_discoveries_full['cum_discoveries'] = n_discoveries_full.groupby('family')['n'].cumsum()
    n_discoveries_full['cum_discoveries'] = n_discoveries_full['cum_discoveries']/n_discoveries_full['sum']
    
    return n_discoveries_full


# Plot Lorenz curves (used to visualize innovation inequality):

# In[ ]:


# Plot Lorenz curve
def plot_lorenz(in_df, name, seed):
    highlight_col = '#ffad3b'
    fig, ax = plt.subplots(figsize=(6,6))
    
    # Insert point at origin 
    origin = pd.DataFrame({'family': [name],
                           'avatar': [0],
                           'n': [0],
                           'sum': [0],
                           'count': [0],
                           'cum_players': [0],
                           'cum_discoveries': [0]})
    
    df = pd.concat([origin, in_df])
    # Cumulative distribution
    sns.lineplot(data = df, x = 'cum_players', y = 'cum_discoveries', color = highlight_col, ax=ax)

    # Fill in area over Lorenz curve
    ax.fill_between(df['cum_players'], df['cum_discoveries'], df['cum_players'],
                   color = highlight_col)

    # Write Gini coefficient on plot
    g = gini(df['cum_discoveries'].values)
    ax.text(0.75, 0.05, 'G = %.2f' % g, 
            bbox = {'facecolor': '#ffffff', 'edgecolor': highlight_col})

    # Line of equality
    ax.plot([0, 1], [0, 1], transform=ax.transAxes, linestyle='-', color='black', linewidth = 1) 

    ## Customize
    ax.yaxis.tick_right() # Move axes to the right
    ax.tick_params(axis = "y", which = "both", right = False)

    ax.yaxis.set_label_position("right")
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.set(xlim = [0,1], ylim= [0,1], aspect = 1.0,
           xlabel='Cumulative share of characters\n(Fewest to most discoveries)',
           ylabel='Cumulative share of discoveries')

    #  Save to file
    plot_file = 'plots/discoveries/seed-%i_%s_lorenz.png' % (seed, name)
    plt.savefig(plot_file, bbox_inches = 'tight')
    plt.close()
        
    return g


# Plot distribution of # discoveries (useful to interpret Lorenz curve):

# In[ ]:


def plot_dist(df, name, seed):
    ax = sns.distplot(df['n'], kde=False)
    ax.set(xlabel='# discoveries')
    sns.despine()
    
    plot_file = 'plots/discoveries/seed-%i_%s_dist.png' % (seed, name)
    plt.savefig(plot_file, bbox_inches = 'tight')
    plt.close()


# Main loop:

# In[ ]:


discovery_list = []
rep_list = []
gini_list = []

for s in tqdm.tqdm(seed_changes):
    # Identify all logs with the same world seed
    seed_logs = file_df[file_df['seed'] == s].copy()
    seed_fs = seed_logs['file'].values

    if len(seed_fs):

        # Add all logs associated with the same world seed to dataframe
        seed_list = [process_maplog(f) for f in seed_fs]
        seed_df = pd.concat(seed_list).reset_index(drop=True)
        seed_df['seed'] = s

        # Identify discoveries by family
        # = first time a family member interacts with an object, by world seed
        seed_disc = id_discoveries(seed_df)
        
        # Change in repertoire size over time (used for survival regression)
        seed_disc_time = discoveries_dynamic(seed_disc)

        # Cumulative counts (used to plot Lorenz curve)
        seed_disc_cum = lorenz_inputs(seed_disc)
        seed_disc_cum['seed'] = s

        # Depth and breadth of repertoire
        seed_repertoire = seed_disc.groupby('family').agg({'object_id': 'count', 'depth': 'max'}).reset_index()
        seed_repertoire = seed_repertoire.rename(columns={'object_id': 'breadth'})

        # Innovation inequality
        for name,group in tqdm.tqdm(seed_disc_cum.groupby('family')):    

            g = plot_lorenz(group, name, s)
            plot_dist(group, name, s)
            gini_list.append((s, name, g))

        # Add to lists
        discovery_list.append(seed_disc_time)
        rep_list.append(seed_repertoire)


# Concat dataframes:

# In[ ]:


rep_df = pd.concat(rep_list)
rep_df['log_breadth'] = np.log10(rep_df['breadth'])
rep_df['log_depth'] = np.log10(rep_df['depth'])
rep_df.to_csv('outputs/family_repertoire.tsv', sep='\t', index=False)
#rep_df.head()


# In[ ]:


gini_df = pd.DataFrame(gini_list, columns = ['seed', 'family', 'gini'])
gini_df.to_csv('outputs/family_gini.tsv', sep='\t', index=False)
#gini_df.head()


# In[ ]:


discovery_df = pd.concat(discovery_list)
discovery_df.to_csv('outputs/family_discoveries.tsv', sep='\t', index=False)


# Plot innovation inequality:

# In[ ]:


# ax = sns.distplot(gini_df['gini'])
# ax.set(xlabel='Innovation inequality (G)', xlim=(0,1))
# sns.despine()


# Relationship between G and community size:

# In[ ]:


# size_df = pd.read_csv('../2_demographics/outputs/family_fitness.tsv', sep='\t', index_col=None)
# size_df = size_df[['family', 'sum']]
# size_df.head()


# In[ ]:


# g_size = pd.merge(gini_df, size_df, on='family', how='outer')
# g_size['log_sum'] = np.log10(g_size['sum'])
# g_size.head()


# In[ ]:





# In[ ]:


# fig = plt.figure(figsize=(6,6))
# ax = sns.regplot(x='gini', y='log_sum', data=g_size, 
#                  scatter_kws={'alpha': 0.05, 'color': '#A5C8E1'}, 
#                  line_kws = {'color': '#2276B4'},
#                  lowess=True)
# yticks =  np.arange(0,5)
# ax.set_yticks(yticks)
# yticklabels = [10**y for y in yticks]
# ax.set(xlabel = 'Innovation inequality (G)',
#        xlim = (0,1),
#        ylabel = '# raised to adulthood',
#        yticklabels=yticklabels)
# sns.despine()


# In[ ]:


# g = sns.jointplot(x='log_breadth',y='log_depth',data=rep_df, alpha=0.01)
# x0, x1 = g.ax_joint.get_xlim()
# y0, y1 = g.ax_joint.get_ylim()
# lims = [min(x0, y0), max(x1, y1)]
# g.ax_joint.plot(lims, lims, ':k')
# g.ax_joint.set(xlabel = 'log$_{10}$(breadth)', ylabel = 'log$_{10}$(depth)',
#                xlim = lims, ylim = lims)


# In[ ]:




