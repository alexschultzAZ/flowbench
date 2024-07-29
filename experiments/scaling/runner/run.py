# import os
# import subprocess
# import time
# import requests
# from threading import Thread

# # for x in range(0, 10):
# #     print("running " + str(x))
# #     os.system('curl http://10.1.238.115:8080/function/scalefn1')
# #     time.sleep(0.1)

# response = requests.post('http://10.1.238.115:8080/function/scalefn1')


# # # start all programs
# # processes = [subprocess.Popen(program) for program in ['curl http://10.1.238.115:8080/function/scalefn1', 'curl http://10.1.238.115:8080/function/scalefn1']]
# # # wait
# # for process in processes:
# #     process.wait()



# from threading import Thread

# threads = [Thread(target=requests.post, args=('http://10.1.238.115:8080/function/scalefn1',)]
# for t in threads: t.start()
# for t in threads: t.join()


# print("done")

# import requests
# from multiprocessing.dummy import Pool as ThreadPool

# urls = ['http://10.1.238.115:8080/async-function/scalefn1'] * 120


# # Make the Pool of workers
# pool = ThreadPool(16)

# # Open the URLs in their own threads
# # and return the results
# results = pool.map(requests.post, urls)

# # Close the pool and wait for the work to finish
# pool.close()
# pool.join()
# print("done")

import os

for x in range(0, 10):
    print("curling " + str(x))
    os.system('curl http://10.1.238.115:8080/async-function/scalefn1    --data "Hi"   --header "X-Callback-Url: http://192.168.1.99:8888"')

print("done")

#1524
##1746