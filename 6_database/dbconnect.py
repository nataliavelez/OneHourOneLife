import pymongo
import os
import fnmatch

#find *.key containing username and password on separate lines(untracked using .gitignore)
for file_name in os.listdir():
    if fnmatch.fnmatch(file_name,'*.key'):
        keyfile = file_name

#Connection string
creds = open(keyfile, "r").read().splitlines()
myclient = pymongo.MongoClient('134.76.24.75', username=creds[0], password=creds[1], authSource='ohol') 