from minio import Minio
import os
import imutils
import cv2
from PIL import Image
from shutil import rmtree
from facenet_pytorch import MTCNN, InceptionResnetV1
from datetime import datetime
import time
import numpy as np
import requests
import torch

class Face():
    def __init__(self):
        
        acceleration = os.getenv('ACCELERATION', 'cpu').lower()  # Default to 'cpu' if the variable is not defined

        # Check if GPU is available and ACCELERATION is set to 'gpu'
        print(f"Acceleration env is {acceleration}")
        print(f"Torch.cuda.is_available() = {torch.cuda.is_available()}")
        if acceleration == 'gpu' and torch.cuda.is_available():
            device = 'cuda'
        else:
            device = 'cpu'

        # Print device being used
        print(f"Using device: {device}")
        #self.mtcnn = MTCNN(keep_all=True, device='cpu')
        self.mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

    
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
        output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        t0 = time.perf_counter()
        img = cv2.imread(req, cv2.IMREAD_COLOR)
        boxes, _ = self.mtcnn.detect(img)

        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        #new_pic = output_dir + "/" + "stage-" + str(os.getenv('PIPELINE_STAGE')) + "-" + \
        #            datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + os.uname()[1] + ".jpg"
        stage = str(os.getenv('PIPELINE_STAGE','3'))
        new_file = output_dir + "/"+ original_filename +'-stage-' + stage + '-' + \
                    datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + os.uname()[1]
        # face = self.mtcnn.extract(img, np.array([[0, 0, img.size[0], img.size[1]]]), save_path=new_pic)
        face, prob = self.mtcnn(img, return_prob=True, save_path=None)
        # saved_data = torch.load('/app/tmp/data.pt')  # loading data.pt file
        saved_data = torch.load('/app/tmp/data.pt')  # loading data.pt file

        if face != None:
            emb = self.resnet(face.unsqueeze(0)).detach()  # detech is to make required gradient false
            embedding_list = saved_data[0]  # getting embedding data
            name_list = saved_data[1]  # getting list of names
            dist_list = []  # list of matched distances, minimum distance is used to identify the person
            for idx, emb_db in enumerate(embedding_list):
                dist = torch.dist(emb, emb_db).item()
                dist_list.append(dist)
            idx_min = dist_list.index(min(dist_list))
            # Save the result name in a file
            with open(new_file+".txt", 'w+') as f:
                f.write(name_list[idx_min])
            return output_dir, name_list[idx_min]
        else:
            print(f"No face is detected")
            return None, None
        #t1 = time.perf_counter()
        #record = [[str(t1 - t0)]]
        #self.store_to_minio(os.environ["OUTPUTBUCKET"], output_dir, record)

        #os.remove(req)
        #rmtree(output_dir)



    def handler_small(self, newfile, original_filename):
        output_dir, name = self.forward(newfile, original_filename)
        return output_dir, name

