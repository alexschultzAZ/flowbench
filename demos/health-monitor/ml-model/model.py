import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import classification_report, accuracy_score

# Import the heart disease dataset
dataset_url = "http://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
column_names = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'class']

# Read the dataset
dataset = pd.read_csv(dataset_url, names=column_names)

# Remove rows with missing data
dataset = dataset.replace('?', np.nan)
dataset = dataset.dropna()

# Convert data to numeric
dataset = dataset.apply(pd.to_numeric)

# Convert 'class' column to binary
dataset['class'] = np.where(dataset['class'] > 0, 1, 0)

# Split the data into features and target
X = dataset.iloc[:, :-1]
y = dataset.iloc[:, -1]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)

# Define the CNN model
model = Sequential()
model.add(Dense(10, input_dim=13, kernel_initializer='normal', activation='relu'))
model.add(Dense(8, kernel_initializer='normal', activation='relu'))
model.add(Dense(4, kernel_initializer='normal', activation='relu'))
model.add(Dense(1, activation='sigmoid'))

# Compile the model
model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.001), metrics=['accuracy'])

# Define the checkpoint callback
checkpoint = ModelCheckpoint('CNN_Model.keras', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
callbacks_list = [checkpoint]

# Train the model
model.fit(X_train, y_train, epochs=60, batch_size=8, verbose=1, validation_data=(X_test, y_test), callbacks=callbacks_list)

# Print the classification report
y_pred = np.round(model.predict(X_test))
print(classification_report(y_test, y_pred))
print('Classification Accuracy: {} %'.format(accuracy_score(y_test, y_pred) * 100))
