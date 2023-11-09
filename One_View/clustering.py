from sklearn.cluster import DBSCAN
from imutils import paths
import face_recognition
import numpy as np
import pickle
import cv2
import os

def load_and_encode_faces(input_dir, encodings_file):
    # grab the paths to the input images in dataset, then initialize data list
    print("[INFO] quantifying faces...")
    imagePaths = list(paths.list_images(input_dir))
    data = []

    for (i, imagePath) in enumerate(imagePaths):
        # load the input image and convert it from RGB (OpenCV ordering)
        # to dlib ordering (RGB)
        print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
        print(imagePath)

        image = cv2.imread(imagePath)
        if image is None:
            print(f"Error reading image: {imagePath}")
            continue  # Skip the current image and proceed to the next one

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input image
        boxes = face_recognition.face_locations(rgb, model='cnn')

        # compute the facial embedding for the face
        encodings = face_recognition.face_encodings(rgb, boxes)

        # build a dictionary of the image path, bounding box location,
        # and facial encodings for the current image
        d = [{"imagePath": imagePath, "loc": box, "encoding": enc} for (box, enc) in zip(boxes, encodings)]
        data.extend(d)

    # dump the facial encodings data to disk
    print("[INFO] serializing encodings...")
    with open(encodings_file, "wb") as f:
        pickle.dump(data, f)



def cluster_faces(encodings, output_dir):
    # load the serialized face encodings + bounding box locations from disk, then extract the set of encodings to so we can cluster on them
    print("[INFO] loading encodings...")
    data = pickle.loads(open(encodings, "rb").read())
    data = np.array(data)
    encodings = [d["encoding"] for d in data]

    # cluster the embeddings
    print("[INFO] clustering...")
    clt = DBSCAN(metric="euclidean", n_jobs=-1)
    clt.fit(encodings)
    # determine the total number of unique faces found in the dataset
    labelIDs = np.unique(clt.labels_)
    numUniqueFaces = len(np.where(labelIDs > -1)[0])
    print("[INFO] # unique faces: {}".format(numUniqueFaces))


    # loop over the unique face integers
    for labelID in labelIDs:
        # find all indexes into the `data` array that belong to the
        # current label ID, then randomly sample a maximum of 25 indexes
        # from the set
        print("[INFO] faces for face ID: {}".format(labelID))
        idxs = np.where(clt.labels_ == labelID)[0]
        idxs = np.random.choice(idxs, size=min(25, len(idxs)),
            replace=False)
        # initialize the list of faces to include in the montage
        cluster_dir = os.path.join(output_dir, f"Cluster_{labelID}")
        os.makedirs(cluster_dir, exist_ok=True)
    # loop over the sampled indexes
        for i in idxs:
            # load the input image and extract the face ROI
            image = cv2.imread(data[i]["imagePath"])
            image_output_path = os.path.join(cluster_dir, f"image_{i}.jpg")
            cv2.imwrite(image_output_path, image)
            (top, right, bottom, left) = data[i]["loc"]
            face = image[top:bottom, left:right]
            face = cv2.resize(face, (96, 96))
            face_output_path = os.path.join(cluster_dir, f"face_{labelID}.jpg")
            cv2.imwrite(face_output_path, face)
            
    print("[INFO] Images sorted into cluster directories.")
