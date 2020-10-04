import numpy as np

r = 238 # Threshold

print('Loading U')
U = np.loadtxt('outputs/svd/U.txt')
print(U.shape)
U_hat = U[:,:r]
print(U_hat.shape)
np.savetxt('outputs/svd/U_hat.txt', U_hat)
del U

print('Loading s')
s = np.loadtxt('outputs/svd/s.txt')
print(s.shape)
s_hat = s[:r]
print(s_hat.shape)
np.savetxt('outputs/svd/s_hat.txt', s_hat)
del s

print('Loading Vh')
Vh = np.loadtxt('outputs/svd/Vh.txt')
print(Vh.shape)
Vh_hat = Vh[:r,:]
print(Vh_hat.shape)
np.savetxt('outputs/svd/Vh_hat.txt', Vh_hat)
del Vh
