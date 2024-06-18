from datetime import datetime
import face_recognition
import pickle
import cv2
import os

def handle(req):
    output_dir = "/tmp/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stage = os.getenv('PIPELINE_STAGE')
    known_faces = os.getenv("ENCODINGS")

    print("[INFO] loading encodings...")
    data = pickle.loads(open(known_faces, "rb").read())

    image = cv2.imread(req)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    boxes = [(0, image.shape[1], image.shape[0], 0)]
    box = boxes[0]
    encodings = face_recognition.face_encodings(rgb, boxes)
    encoding = encodings[0]

    print("[INFO] recognizing faces...")
    matches = face_recognition.compare_faces(data["encodings"], encoding)
    name = "Unknown"

    if True in matches:
        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
        counts = {}

        for i in matchedIdxs:
            name = data["names"][i]
            counts[name] = counts.get(name, 0) + 1

        name = max(counts, key=counts.get)

    cv2.rectangle(image, (box[3], box[0]), (box[1], box[2]), (0, 255, 0), 2)
    y = box[0] - 15 if box[0] - 15 > 15 else box[0] + 15
    cv2.putText(image, name, (box[3], y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    new_pic = output_dir + "/" + "stage-" + str(stage) + "-" + \
                        datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + \
                        "-" + os.uname()[1] + ".jpg"
    cv2.imwrite(new_pic, image)

    if len(os.listdir(output_dir)) == 0:
        os.rmdir(output_dir)
        return ""

    return output_dir
