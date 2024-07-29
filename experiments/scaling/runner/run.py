

import requests
from multiprocessing.dummy import Pool as ThreadPool

urls = ['http://10.1.238.115:8080/async-function/scalefn1'] * 120


# Make the Pool of workers
pool = ThreadPool(16)

# Open the URLs in their own threads
# and return the results
results = pool.map(requests.post, urls)

# Close the pool and wait for the work to finish
pool.close()
pool.join()
print("done")
