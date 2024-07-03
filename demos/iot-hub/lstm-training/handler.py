import os
from minio import Minio, S3Error
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import pandas as pd
import io

def train_lstm_model(minio_client, bucket_name):
    obj = minio_client.get_object(bucket_name, 'sensor_data.csv')
    df = pd.read_csv(io.BytesIO(obj.read()))

    # For simplicity, we'll focus on temperature prediction
    data = df['temperature'].values.reshape(-1, 1)
    split = int(len(data) * 0.8)
    train_data = data[:split]
    test_data = data[split:]

    def create_dataset(data, time_step=1):
        X, Y = [], []
        for i in range(len(data) - time_step - 1):
            a = data[i:(i + time_step), 0]
            X.append(a)
            Y.append(data[i + time_step, 0])
        return np.array(X), np.array(Y)

    time_step = 10
    X_train, y_train = create_dataset(train_data, time_step)
    X_test, y_test = create_dataset(test_data, time_step)

    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=20, batch_size=64, verbose=1)

    model.save('lstm_model.h5')
    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

    try:
        minio_client.fput_object(bucket_name, 'lstm_model.h5', 'lstm_model.h5')
        print("LSTM model saved to MinIO bucket successfully.")
    except S3Error as e:
        print("Error occurred while uploading LSTM model to MinIO:", e)


MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET')
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)
# Ensure bucket exists
if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
    minio_client.make_bucket(MINIO_BUCKET_NAME)

# Train LSTM model and save to MinIO
train_lstm_model(minio_client, MINIO_BUCKET_NAME)
"""
export MINIO_ENDPOINT='172.17.0.4:9000' \
export MINIO_ACCESS_KEY='minioadmin' \
export MINIO_SECRET_KEY='minioadmin' \
export MINIO_BUCKET='lstm-sensor-data'

"""