import os
import time
from datetime import datetime
from minio import Minio
from minio.error import InvalidResponseError
import requests
import influxdb_client
import influxdb
from influxdb_client.client.write_api import SYNCHRONOUS

def store_to_minio(bucket, ret, max_upload, stagger_by, instats):
    files = sorted(os.listdir(ret))
    if len(files) == 0:
        return

    minioClient = Minio(os.environ["ENDPOINTOUTPUT"],
                        os.environ["ACCESSKEYOUTPUT"],
                        os.environ["SECRETKEYOUTPUT"],
                        secure=False)
    # Put an object.
    try:
        os.chdir(ret)
        for i,file in enumerate(files[:int(max_upload)],start=1):
            start_store = time.time()
            minioClient.fput_object(bucket, file, file)
            p = influxdb_client.Point("video-generation_each").field("data_upload_time", float(time.time()-start_store)*1000).tag("file_num", i).tag("stagger-by", stagger_by).tag("output_bucket",bucket).tag("device",os.getenv("OPENFAAS_URL")).tag("inputfile",file)
            instats.write_api.write(bucket=instats.bucket, org=instats.org, record=p)
            time.sleep(stagger_by)
            if os.getenv("NEXT_FUNCTION") and os.getenv("NEXT_GATEWAY"):
                start_invoke = time.time()
                comm_latencies = invoke_next_function(bucket, ret, [file])
                stop_invoke =  time.time()
                p = influxdb_client.Point("video-generation_each").field("output_upload_time", float(time.time()-start_store)*1000).tag("file_num", i).tag("stagger-by", stagger_by).tag("output_bucket",bucket).tag("device",os.getenv("OPENFAAS_URL")).tag("inputfile",file).tag("next_gateway",os.getenv("NEXT_GATEWAY")).tag("next_funtion",os.getenv("NEXT_FUNCTION")).tag("communication_time",comm_latencies)
                instats.write_api.write(bucket=instats.bucket, org=instats.org, record=p)
        return
    except InvalidResponseError as err:
        print(err)

def invoke_next_function(bucket, outdir, files):
    next_function = os.getenv('NEXT_FUNCTION')
    next_gateway = os.getenv('NEXT_GATEWAY')
    async_function = os.getenv('ASYNC')
    output_type = {'mp4' : 'video', 'mpeg' : 'video', \
                'jpeg' : 'image', 'jpg' : 'image', \
                'png' : 'image', 'zip' : 'application'}


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
        timestamps.append(float(t1 - t0))

    return timestamps

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



def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    if os.getenv("DATABASE"):
        instats = InfluxStats()
        #token = os.getenv("INFLUXDB_TOKEN")
        #org = os.getenv("ORG")
        #url = os.getenv("DATABASE_URL")
        #bucket = os.getenv("DATABASE")
        #client = influxdb_client.InfluxDBClient(
        #    url=url,
        #    token=token,
        #    org=org
        #)
        #print(f"Here is the details: token={token} \n org={org}, bucket={bucket}, url={url}")
        #write_api = client.write_api(write_options=SYNCHRONOUS)

    print("Starting video-generation ...")
    output_bucket = os.getenv("OUTPUTBUCKET")
    print(f"Sending videos to minio bucket {output_bucket} ... ")

    input_folder = os.getenv("INPUT_FOLDER")
    if os.listdir(input_folder):
        num_objs = len(os.listdir(input_folder))
        num_file_to_upload = int(os.getenv("NUM_FILES_TO_UPLOAD", num_objs))
        stagger_by = int(os.getenv("STAGGER_BY", 0))
        print(f"Preparing {num_file_to_upload} from local to Minio ...")
        if num_file_to_upload != 0:
            start_store = time.time()
            store_to_minio(output_bucket, input_folder, num_file_to_upload, stagger_by,instats)
            stop_store = time.time()
            if os.getenv("DATABASE"):
                p = influxdb_client.Point("video-generation").field("data_upload_time", float(stop_store-start_store)*1000).tag("store_num_files", num_file_to_upload).tag("stagger-by", stagger_by).tag("output_bucket",output_bucket).tag("device",os.getenv("OPENFAAS_URL"))
                instats.write_api.write(bucket=instats.bucket, org=instats.org, record=p)



    return req
