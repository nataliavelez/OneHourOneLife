# Helper functions used throughout the analysis scripts
# Natalia Vélez, April 2021
import datetime, glob, re
from os.path import join as opj

def gsearch(*args): return glob.glob(opj(*args))
def str_extract(pattern, s): return re.search(pattern,s).group(0)
def int_extract(pattern, s): return int(str_extract(pattern, s))
def to_date(t, fmt='%Y-%m-%d %H:%M:%S'): return datetime.datetime.fromtimestamp(t).strftime(fmt)
