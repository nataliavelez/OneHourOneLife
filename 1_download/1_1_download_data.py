#!/usr/bin/env python
# coding: utf-8

# # Download public logs
# Natalia Vélez, November 2019

# In[11]:


from bs4 import BeautifulSoup
from datetime import datetime
import os, csv, requests, urllib, tqdm
import pandas as pd


# Location of One Life logs:

# In[12]:


ohol_url = 'http://publicdata.onehouronelife.com/'
exclude_keywords = ['..', 'foodLogs', 'curseLog'] # Directories not to download
server = 'bigserver2' # server to download from 


# Make local dir to store data:

# In[13]:


data_dir = '../../data/'
os.makedirs(data_dir, exist_ok=True)


# Helper function: Search through address recursively

# In[14]:


def get_url_paths(url, parent=''):
    response = requests.get(url)
    if response.ok:
        response_text = response.text
    else:
        return response.raise_for_status()
    soup = BeautifulSoup(response_text, 'html.parser')
    
    paths = []
    for node in soup.find_all('a'):
        node_href = node.get('href')        
        # Conditions for recursive search
        node_isdir = node_href.endswith('/')
        node_keep = not any(kwd in node_href for kwd in exclude_keywords)
        
        if ((node_isdir) & (node_keep)):
            print('crawl —> %s' % parent+node_href)
            
            # Add folder to local data
            local_dir = data_dir + parent + node_href
            if not os.path.isdir(local_dir):
                print('New local dir: %s' % local_dir)
                os.makedirs(local_dir)
            
            # Recursive search
            paths += get_url_paths(url + node_href, parent+node_href)
            
        elif not node_isdir:
            paths.append(url + node.get('href'))
            
    return paths


# Find OHOL files:

# In[15]:


ohol_all_paths = get_url_paths(ohol_url)
print('%i files found' % len(ohol_all_paths))

# Keep only paths in server
ohol_paths = [f for f in ohol_all_paths if server in f]
print('%i files in server %s' % (len(ohol_paths), server))


# Download data
# 
# NB: This chunk checks which files are present in the server, but missing from the data folder.

# In[16]:


data_download = pd.DataFrame({'in': ohol_paths})
data_download['out'] = data_download['in'].str.replace(ohol_url, data_dir)
data_download['exist'] = data_download['out'].map(os.path.exists)
data_download = data_download[~(data_download['exist'])]

print('Downloading %i/%i files' % (len(data_download), len(ohol_paths)))


# Save this download in the download log

# In[7]:


log_file = 'download_log.txt'

if not os.path.isfile(log_file):
    log_header = ['user', 'timestamp', 'files_on_server', 'files_on_local', 'files_downloaded']
    with open(log_file, 'wt') as file:
        tsv_writer = csv.writer(file, delimiter='\t')
        tsv_writer.writerow(log_header)

user = 'nvelez'
timestamp = datetime.now().__str__()
server = len(ohol_paths)
downloaded = len(data_download)
local = server-downloaded

log_data = [user, timestamp, server, local, downloaded]
with open(log_file, 'at') as file:
        tsv_writer = csv.writer(file, delimiter='\t')
        tsv_writer.writerow(log_data)


# Run download

# In[8]:


data_iter = data_download.iterrows()
n_iter = data_download.shape[0]

for idx, row in tqdm.tqdm(data_iter, total=n_iter):
    print('Writing to: %s' % row['out'])
    urllib.request.urlretrieve(row['in'], row['out'])

