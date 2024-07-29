import datetime
import time
import math
import socket



def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)

    print("Your Computer Name is:" + hostname)
    print("Your Computer IP Address is:" + IPAddr)
    # print("running fn")
    # time.sleep(1)
    # print("done")
    for x in range(0, 10000000):
        a = math.sqrt(64*64*64*64*64)
    # interval = 2
    # utilization = 90
    # start_time = time.time()
    # for i in range(0,int(interval)):
    #     print("About to do some arithmetic")
    #     while time.time()-start_time < utilization/100.0:
    #         a = math.sqrt(64*64*64*64*64)
    #     print(str(i) + ". About to sleep")
    #     time.sleep(1-utilization/100.0)
    #     start_time += 1
    print("did it")
    return "scalefn1 done at " + str(IPAddr)
