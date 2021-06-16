# Helper functions used throughout the analysis scripts
# Natalia Velez + Charley Wu, May 2021
import datetime, glob, re
from os.path import join as opj
from scipy.sparse import csr_matrix
import numpy as np

def gsearch(*args): return glob.glob(opj(*args))
def str_extract(pattern, s): return re.search(pattern,s).group(0)
def int_extract(pattern, s): return int(str_extract(pattern, s))
def to_date(t, fmt='%Y-%m-%d %H:%M:%S'): return datetime.datetime.fromtimestamp(t).strftime(fmt)
def load_json(path):
    with open(path, 'r') as handle:
        data = json.load(handle)
    return data

#Function to delete rows/columns
def delete_from_csr(mat, row_indices=[], col_indices=[]):
    """
    Remove the rows (denoted by ``row_indices``) and columns (denoted by ``col_indices``) from the CSR sparse matrix ``mat``.
    WARNING: Indices of altered axes are reset in the returned matrix
    """
    if not isinstance(mat, csr_matrix):
        raise ValueError("works only for CSR format -- use .tocsr() first")

    rows = []
    cols = []
    if row_indices:
        rows = list(row_indices)
    if col_indices:
        cols = list(col_indices)

    if len(rows) > 0 and len(cols) > 0:
        row_mask = np.ones(mat.shape[0], dtype=bool)
        row_mask[rows] = False
        col_mask = np.ones(mat.shape[1], dtype=bool)
        col_mask[cols] = False
        return mat[row_mask][:,col_mask]
    elif len(rows) > 0:
        mask = np.ones(mat.shape[0], dtype=bool)
        mask[rows] = False
        return mat[mask]
    elif len(cols) > 0:
        mask = np.ones(mat.shape[1], dtype=bool)
        mask[cols] = False
        return mat[:,mask]
    else:
        return mat

# Shuffle sparse matrices (CSR format)
def shuffle_csr(m):
    # Get original mtx dimensions
    m_shuffled = m.copy()
    n_row, n_col = m_shuffled.shape
    all_indices = np.arange(n_col)
    
    # Shuffle each row independently
    for row in range(n_row):
        # Get row indices
        row_idx = m_shuffled.indices[m_shuffled.indptr[row]:m_shuffled.indptr[row+1]]

        # Replace with shuffled indices
        shuffled_idx = np.random.choice(all_indices, size=len(row_idx), replace=True)
        m_shuffled.indices[m_shuffled.indptr[row]:m_shuffled.indptr[row+1]] = shuffled_idx

    return m_shuffled

#Human readable formating of memory size
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

