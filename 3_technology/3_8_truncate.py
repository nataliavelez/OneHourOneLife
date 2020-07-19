import numpy as np

r = 238 # Threshold

# Load SVD outputs
print('Loading original SVD outputs...')
U = np.loadtxt('outputs/svd/U.txt')
s = np.loadtxt('outputs/svd/s.txt')
Vh = np.loadtxt('outputs/svd/Vh.txt')

# Truncate
print('Left-side eigenvectors: %s' % U.shape)
U_hat = U[:,:r]
print('Truncated: %s\n' % U_hat.shape)
np.savetxt('outputs/svd/U_hat.txt', U_hat)

print('Singular values: %s' % s.shape)
s_hat = s[:r]
print('Truncated: %s\n' % s_hat.shape)
np.savetxt('outputs/svd/s_hat.txt', s_hat)

print('Right-side eigenvectors: %s' % Vh.shape)
Vh_hat = Vh[:r,:]
print('Truncated: %s' % Vh_hat.shape)
np.savetxt('outputs/svd/Vh_hat.txt', Vh_hat)
