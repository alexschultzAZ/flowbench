from datasets import load_from_disk
from transformers import AutoTokenizer, DataCollatorWithPadding, create_optimizer, TFAutoModelForSequenceClassification
import tensorflow as tf
import shutil
from zipfile import ZipFile
import os
from minio import Minio, error
import time

MINIO_ADDRESS = os.getenv('MINIO_ADDRESS')
minio_client = Minio(MINIO_ADDRESS, access_key="minioadmin", secret_key="minioadmin", secure=False)

def handle(event, context=None):

    tokenizerDownloadStart = time.time()
    tokenizer_name = 'tinybert_tokenizer'
    tokenizer_zip = load_from_minio('model', tokenizer_name+'.zip')
    tokenizerDownloadEnd = time.time()
    
    tokenizerLoadStart = time.time()
    tokenizer_dir = unzip(tokenizer_zip)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    tokenizerLoadEnd = time.time()

    modelDownloadStart = time.time()
    model_name = 'pretrained_tinybert'
    model_zip = load_from_minio('model', model_name+'.zip')
    modelDownloadEnd = time.time()

    modelLoadStart = time.time()
    model_dir = unzip(model_zip)
    id2label = {0: "NEGATIVE", 1: "POSITIVE"}
    label2id = {"NEGATIVE": 0, "POSITIVE": 1}
    model = TFAutoModelForSequenceClassification.from_pretrained(model_dir, num_labels=2, id2label=id2label, label2id=label2id)
    modelLoadEnd = time.time()
    
    datasetDownloadStart = time.time()
    dataset_name = 'imdb_dataset'
    dataset_zip = load_from_minio('model', dataset_name+'.zip')
    datasetDownloadEnd = time.time()
    
    datasetLoadStart = time.time()
    dataset_dir = unzip(dataset_zip)
    training_dataset, validation_dataset = create_train_val_dataset(dataset_dir, tokenizer, model)
    datasetLoadEnd = time.time()
    
    modelTrainStart = time.time()
    model = update_model(model, training_dataset, 1)
    modelTrainEnd = time.time()
    
    modelTestStart = time.time()
    loss, accuracy = test_model(model, validation_dataset)
    modelTestEnd = time.time()

    modelUploadStart = time.time()
    save_model(model, '/tmp/model/'+model_name)
    shutil.make_archive('/tmp/'+model_name, 'zip', '/tmp/model')   
    store_to_minio('model', model_name+'.zip', '/tmp/'+model_name+'.zip')
    modelUploadEnd = time.time()

    tflitemodelConvertStart = time.time()
    model.save('/tmp/tinybert_for_tflite')
    converter = tf.lite.TFLiteConverter.from_saved_model('/tmp/tinybert_for_tflite')
    tflite_model = converter.convert() 
    tflitemodelConvertEnd = time.time()

    tflitemodelUploadStart = time.time()
    with open("/tmp/tinybert_imdb.tflite", "wb") as f:
        f.write(tflite_model)
    store_to_minio('model', 'tinybert_imdb.tflite', '/tmp/tinybert_imdb.tflite')
    tflitemodelUploadEnd = time.time()

    result = {}    
    result['accuracy'] = accuracy
    result['loss'] = loss
    result['tokenizerDownloadTime'] = tokenizerDownloadEnd - tokenizerDownloadStart
    result['tokenizerLoadTime'] = tokenizerLoadEnd - tokenizerLoadStart
    result['datasetDownloadTime'] = datasetDownloadEnd - datasetDownloadStart
    result['datasetLoadTime'] = datasetLoadEnd - datasetLoadStart
    result['modelDownloadTime'] = modelDownloadEnd - modelDownloadStart
    result['modelLoadTime'] = modelLoadEnd - modelLoadStart
    result['modelTrainTime'] = modelTrainEnd - modelTrainStart
    result['modelTestTime'] = modelTestEnd - modelTestStart
    result['modelUploadTime'] = modelUploadEnd - modelUploadStart
    result['tflitemodelConvertTime'] = tflitemodelConvertEnd - tflitemodelConvertStart
    result['tflitemodelUploadTime'] = tflitemodelUploadEnd - tflitemodelUploadStart

    return result
    

def update_model(model, train_ds, epochs=10):

    num_epochs = 5
    batches_per_epoch = 2500
    total_train_steps = int(batches_per_epoch * num_epochs)
    optimizer, schedule = create_optimizer(init_lr=2e-5, num_warmup_steps=0, num_train_steps=total_train_steps)

    model.layers[0].trainable = True
    model.compile(optimizer=optimizer, metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])  # No loss argument!
    history = model.fit(x=train_ds,
                        epochs=epochs)
    
    return model


def create_train_val_dataset(dataset_folder_path, tokenizer, model):

    imdb = load_from_disk(dataset_folder_path)
    # imdb['test'] = imdb['test'].select(list(range(0, 1000)) + list(range(24000, 25000)))
    preprocess_function = lambda examples: tokenizer(examples["text"], truncation=True)
    tokenized_imdb = imdb.map(preprocess_function, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="tf")
    
    tf_train_set = model.prepare_tf_dataset(
        tokenized_imdb["train"],
        shuffle=True,
        batch_size=4,
        collate_fn=data_collator
    )

    tf_validation_set = model.prepare_tf_dataset(
        tokenized_imdb["test"],
        shuffle=False,
        batch_size=4,
        collate_fn=data_collator
    )
    
    return tf_train_set, tf_validation_set


def test_model(model, ds):

    loss, accuracy = model.evaluate(ds)
    return loss, accuracy


def save_model(model, save_model_path):
    model.save_pretrained(save_model_path)

def unzip(zip_file_path):
    with ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall('/tmp/')

    return '/tmp/' + os.path.basename(zip_file_path).split('.')[0] + '/'

def load_from_minio(bucket, file):
    # Get an object.
    try:
        new_file = "/tmp/" + file
        minio_client.fget_object(bucket, file, new_file)
        return new_file
    except error.InvalidResponseError as err:
        print(err)

def store_to_minio(bucket, object, file):
    try:
        minio_client.fput_object(bucket, object, file)
    except error.InvalidResponseError as err:
        print(err)
