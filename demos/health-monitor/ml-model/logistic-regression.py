import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Import the heart disease dataset
dataset_url = "http://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
column_names = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg',
                'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'class']

# Read the dataset
dataset = pd.read_csv(dataset_url, names=column_names)

# Remove missing data indicated by "?"
df = dataset[~dataset.isin(['?'])]

# Drop rows with NaN values
df = df.dropna(axis=0)

# Convert data to numeric
df = df.apply(pd.to_numeric)

# Change 'class' column to binary
df["class"] = np.where(df["class"] > 0, 1, 0)

# Create X and y datasets
X = df.iloc[:, 0:13]
y = df.iloc[:, -1]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a logistic regression model
model = LogisticRegression()
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print('Classification Accuracy:', accuracy_score(y_test, y_pred) * 100, '%')

# Save the model to a file (you can change the filename as per your needs)
joblib.dump(model, 'logistic_regression_model.pkl')
