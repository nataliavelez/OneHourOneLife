
# coding: utf-8

# # Download public logs
# Natalia Vélez, November 2019

# In[28]:


from bs4 import BeautifulSoup
from tqdm import tqdm_notebook, tqdm
from getpass import getuser
from datetime import datetime
import os, csv, requests, urllib
import pandas as pd
import seaborn as sns


# Location of One Life logs:

# In[2]:


ohol_url = 'http://publicdata.onehouronelife.com/'
exclude_keywords = ['..', 'foodLog', 'curseLog'] # Directories not to download


# Make local dir to store data:

# In[3]:


data_dir = '../data/'
os.makedirs(data_dir, exist_ok=True)


# Helper function: Search through address recursively

# In[4]:


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

# In[5]:


ohol_paths = get_url_paths(ohol_url)
print('%i files found' % len(ohol_paths))


# Download data
# 
# NB: This chunk checks which files are present in the server, but missing from the data folder.

# In[6]:


data_download = pd.DataFrame({'in': ohol_paths})
data_download['out'] = data_download['in'].str.replace(ohol_url, data_dir)
data_download['exist'] = data_download['out'].map(os.path.exists)
data_download = data_download[~(data_download['exist'])]

print('Downloading %i/%i files' % (len(data_download), len(ohol_paths)))


# Save this download in the download log

# In[27]:


log_file = 'download_log.txt'

if not os.path.isfile(log_file):
    log_header = ['user', 'timestamp', 'files_on_server', 'files_on_local', 'files_downloaded']
    with open(log_file, 'wt') as file:
        tsv_writer = csv.writer(file, delimiter='\t')
        tsv_writer.writerow(log_header)

user = getuser()
timestamp = datetime.now().__str__()
server = len(ohol_paths)
downloaded = len(data_download)
local = server-downloaded

log_data = [user, timestamp, server, local, downloaded]
with open(log_file, 'at') as file:
        tsv_writer = csv.writer(file, delimiter='\t')
        tsv_writer.writerow(log_data)


# Run download

# In[30]:


data_iter = data_download.iterrows()
n_iter = data_download.shape[0]

for idx, row in tqdm(data_iter, total=n_iter):
    urllib.request.urlretrieve(row['in'], row['out'])

