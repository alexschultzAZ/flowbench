from minio import Minio
import os
import imutils
import cv2
from PIL import Image
from shutil import rmtree
from facenet_pytorch import MTCNN
from datetime import datetime
import time
import numpy as np
import requests

class Face():
    def __init__(self):
        
        self.device = 'cpu'
        self.mtcnn = MTCNN(keep_all=True, device='cpu')

    def store_to_minio(self, bucket, ret, record):
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
                self.invoke_next_function(bucket, ret, file)
                t2 = time.perf_counter()
                store_lat.append(str(t1 - t0))
                comm_lat.append(str(t2 - t1))
            record.append(store_lat)
            record.append(comm_lat)
            return
        except:
            print("Error in put object")


    def forward(self, req, original_filename):
        print(f"{req}")
        output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        t0 = time.perf_counter()
        img = cv2.imread(req, cv2.IMREAD_COLOR)
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        stage = str(os.getenv('PIPELINE_STAGE','3'))
        new_pic = output_dir + "/"+ original_filename +'-stage-' + stage + '-' + \
                datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")+ "-" + os.uname()[1] + ".jpg"

        #new_pic = output_dir + "/" + "stage-" + str(os.getenv('PIPELINE_STAGE')) + "-" + \
        #            datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + os.uname()[1] + ".jpg"
        face = self.mtcnn.extract(img, np.array([[0, 0, img.size[0], img.size[1]]]), save_path=new_pic)
        print(f"output_dir {output_dir}, new_pic = {new_pic}")
        return output_dir

        #t1 = time.perf_counter()
        #record = [[str(t1 - t0)]]
        #self.store_to_minio(os.environ["OUTPUTBUCKET"], output_dir, record)

        #os.remove(req)
        #rmtree(output_dir)



    def handler_small(self, newfile,original_filename):
        output_dir = self.forward(newfile, original_filename)
        print(f"output_dir {output_dir}")
        return output_dir

