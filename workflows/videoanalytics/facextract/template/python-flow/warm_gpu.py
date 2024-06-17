from facenet_pytorch import MTCNN, InceptionResnetV1
from datetime import datetime
from shutil import rmtree
import requests
import torch
import time, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from minio import Minio
import paho.mqtt.client as mqtt
from threading import Thread
from queue import Queue
from multiprocessing import Process, Queue as mpQueue
import socket

output_type = {'mp4' : 'video', 'mpeg' : 'video', \
                'jpeg' : 'image', 'jpg' : 'image', \
                'png' : 'image', 'zip' : 'application'}

def invoke_next_function(bucket, outdir, file):
    next_function = os.getenv('NEXT_FUNCTION')
    next_gateway = os.getenv('NEXT_GATEWAY')

    if next_function == '' or next_function is None:
        print("no next function, return")
        return

    if next_gateway == '' or next_gateway is None:
        print("no next gateway, return")
        return

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

def store_to_minio(bucket, ret, record):
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
        store_lat = []
        comm_lat = []
        for file in files:
            t0 = time.perf_counter()
            minioClient.fput_object(bucket, file, file)
            t1 = time.perf_counter()
            invoke_next_function(bucket, ret, file)
            t2 = time.perf_counter()
            store_lat.append(str(t1 - t0))
            comm_lat.append(str(t2 - t1))
        record.append(store_lat)
        record.append(comm_lat)
        return
    except ResponseError as err:
        print(err)

def on_connect(client, userdata, flags, rc):
    print("Connected to mqtt server with code: "+str(rc))
    client.subscribe('input')

def perf_record(perf_queue):
    stage = os.getenv("PIPELINE_STAGE")
    db = os.getenv("DATABASE")
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT")
    db_url = "http://" + db_host + ":" + db_port + "/write?db=" + db

    while True:
        record = perf_queue.get()

        binary = "writep1s" + str(stage) + " value=" + record[0][0]
        requests.post(url=db_url, data=binary)

        for store_lat in record[1]:
            binary = "miniostorep1s" + str(stage) + " value=" + store_lat
            requests.post(url=db_url, data=binary)

        for comm_lat in record[2]:
            binary = "commp1s" + str(stage) + " value=" + comm_lat
            requests.post(url=db_url, data=binary)

def forward(req):
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    global mtcnn, resnet, device, ids
    t0 = time.perf_counter()
    img = cv2.imread(req, cv2.IMREAD_COLOR)
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    new_pic = output_dir + "/" + "stage-" + str(os.getenv('PIPELINE_STAGE')) + "-" + \
                datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + os.uname()[1] + ".jpg"
    face = mtcnn.extract(img, np.array([[0, 0, img.size[0], img.size[1]]]), save_path=new_pic)
    t1 = time.perf_counter()
    record = [[str(t1 - t0)]]
    store_to_minio(os.environ["OUTPUTBUCKET"], output_dir, record)

    os.remove(req)
    rmtree(output_dir)
    
    global perf_queue
    perf_queue.put(record)

def handler(queue):
    while True:
        req = queue.get()
        forward(req)

def handler_small(newfile):
    forward(newfile)

def on_message(client, userdata, msg):
    global req_queue
    req_queue.put(msg.payload.decode("utf-8"))

#setup the producer-consumer pipes
req_queue = Queue(maxsize=0)
handler_proc = Thread(target=handler, args=((req_queue),))
handler_proc.daemon = True
handler_proc.start()

perf_queue = mpQueue(maxsize=0)
perf_proc = Process(target=perf_record, args=((perf_queue),))
perf_proc.daemon = True
perf_proc.start()

#load the models
device = ''
if torch.cuda.is_available() and os.environ["DEVICE"] != 'cpu':
    local_ip = socket.gethostbyname(os.environ["HOSTNAME"]).split('.')[-1]
    device_cnt = 0
    for f in os.listdir('/dev'):
        if f.startswith('nvidia') and f[6:].isdigit():
            device_cnt = device_cnt + 1
    device = 'cuda:' + str(int(local_ip) % device_cnt)
else:
    device = 'cpu'
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2', classify=True).eval().to(device)
ids = np.load('/tmp/vggface_labels_v2.npy')
ids = dict(enumerate(ids.flatten(), 0))

#setup mqtt client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(host='localhost')
client.loop_forever()

