# Copyright (c) Alex Ellis 2017. All rights reserved.
# Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import os
import sys
import time
import shutil
import requests
from minio import Minio
from function import handler
from minio.error import InvalidResponseError
from datetime import datetime
#from influxdb import InfluxDBClient
import influxdb_client
import influxdb
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxStats:
    def __init__(self):
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("ORG")
        self.url = os.getenv("DATABASE_URL")
        self.bucket = os.getenv("DATABASE")
        self.client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )
        print(f"Here is the details: token={self.token} \n org={self.org}, bucket={self.bucket}, url={self.url}")
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)


output_type = {'mp4' : 'video', 'mpeg' : 'video', \
                'jpeg' : 'image', 'jpg' : 'image', \
                'png' : 'image', 'zip' : 'application'}

def invoke_next_function(bucket, outdir, files):
    next_function = os.getenv('NEXT_FUNCTION')
    next_gateway = os.getenv('NEXT_GATEWAY')
    async_function = os.getenv('ASYNC')

    timestamps = []
    if next_function == '' or next_function is None:
        print("no next function, return")
        return timestamps

    if next_gateway == '' or next_gateway is None:
        print("no next gateway, return")
        return timestamps

    if async_function == '' or async_function is None:
        async_function = '1'

    if len(files) == 0:
        return timestamps

    for file in files:
        t0 = time.time()
        url = 'http://' + next_gateway + '/async-function/' + next_function
        ext = file.split('.')[-1]
        cat = output_type[ext]

        # print("send %s using %s" % (file, os.environ["OUTPUTMODE"]))
        if os.environ["OUTPUTMODE"] == 'http':
            with open(outdir + '/' + file, 'rb') as f:
                data = f.read()
            ret = requests.post(url, data=data, \
                            headers={'Content-Type': cat + '/' + ext, \
                                        'Referer': file})
        else:
            data = bucket + ' ' + file
            ret = requests.post(url, data=data);
        # print(ret.status_code, ret.reason) # print(ret.text)
        t1 = time.time()
        timestamps.append(float(t1 - t0)*1000)

    return timestamps

def store_to_minio(bucket, ret):
    files = os.listdir(ret)
    if len(files) == 0:
        return

    minioClient = Minio(os.environ["ENDPOINTOUTPUT"],
                        os.environ["ACCESSKEYOUTPUT"],
                        os.environ["SECRETKEYOUTPUT"],
                        secure=False)
    # Put an object.
    try:
        os.chdir(ret)
        for file in files:
            minioClient.fput_object(bucket, file, file)
        return
    except InvalidResponseError as err:
        print(err)


def load_from_objectstore(bucket, file):
    url = os.environ["NEXT_GATEWAY"]
    openfaas_url = os.environ["OPENFAAS_URL"]
    
    # Get an object.
    try:
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        url = 'http://' + url + '/getobject'
        #data = openfaas_url + ' ' + bucket + ' ' + curr_round + files
        # jsoninput = '{"url": "' + openfaas_url + '", "filePath": "' + bucket + " " + file + '"}'
        jsoninput = '{"url": "' + openfaas_url + "/" + bucket + "/" + file + '", "filePath": "'+ "/tmp" + '"}'
        #jsoninput = bucket + " " + file 
        #print(data)
        ret = requests.post(url, data=jsoninput);
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        with open(new_file, "wb") as f:
            f.write(ret.content)
        #minioClient.fget_object(bucket, file, new_file)
        return new_file
    except InvalidResponseError as err:
        print(err)

def load_from_minio(bucket, file):
    minioClient = Minio(os.environ["ENDPOINTINPUT"],
                        os.environ["ACCESSKEYINPUT"],
                        os.environ["SECRETKEYINPUT"],
                        secure=False)
    # Get an object.
    try:
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        minioClient.fget_object(bucket, file, new_file)
        return new_file
    except InvalidResponseError as err:
        print(err)

def get_stdin():
    buf = ""
    while(True):
        line = sys.stdin.readline()
        buf += line
        if line == "":
            break
    return buf

if __name__ == "__main__":
    request_start_ts = str(round(time.time() * 1000000000))
    compute_start = 0
    compute_end = 0
    store_start = 0
    store_end = 0
    load_start = 0
    load_end = 0

    files = []
    bucket = ''
    file = ''
    outdir = ''
    if os.getenv("DATABASE"):
        instats = InfluxStats()

    if os.environ["INPUTMODE"] == 'http':
        file = os.getenv("Http_Referer")
        new_file = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + file
        f = open(new_file, "wb+")
        f.write(sys.stdin.buffer.read())
        f.close()

        compute_start = time.time()
        outdir = handler.handle(new_file,file.split(".")[0])
        compute_end = time.time()
    else:
        st = get_stdin()
        bucket = st.split(' ')[0]
        file = st.split(' ')[1].rstrip("\n")

        load_start = time.time()
        #new_file = load_from_objectstore(bucket, file)
        new_file = load_from_minio(bucket, file)
        load_end = time.time()

        compute_start = time.time()
        outdir = handler.handle(new_file,file.split(".")[0])
        compute_end = time.time()

    if outdir != None and outdir != '':
        files = os.listdir(outdir)
        if os.environ["OUTPUTMODE"] == 'obj':
            bucket = os.environ["OUTPUTBUCKET"]
            store_start = time.time()
            store_to_minio(bucket, outdir)
            store_end = time.time()

    if os.getenv("NEXT_FUNCTION"):
        comm_latencies = invoke_next_function(bucket, outdir, files)

    # connect to influxdb and log latency numbers
    if os.getenv("DATABASE") is not None:
        stage = os.getenv("PIPELINE_STAGE")
        p = influxdb_client.Point("video-splitting").field("data_download_time", float(load_end-load_start)*1000).tag("original_filename", file.split(".")[0]).tag("compute_time", float(compute_end-compute_start)*1000).tag("output_upload_time_folder",float(store_end-store_start)*1000).tag("device",os.getenv("OPENFAAS_URL")).tag("communication_time",comm_latencies)
        instats.write_api.write(bucket=instats.bucket, org=instats.org, record=p)

    os.remove(new_file)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)