import os
import pandas as pd
import joblib
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.neighbors import NearestNeighbors
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from app.data_processing import load_raw_data

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'netflix_titles.csv')
SAVED_MODELS_PATH = os.path.join(BASE_DIR, 'app', 'saved_models')

os.makedirs(SAVED_MODELS_PATH, exist_ok=True)

def main():
    # 1. Load and preprocess raw data
    df = load_raw_data(DATA_PATH)

    # 2. Extract 'genres' column as lists
    genres_list = df['genres']

    # 3. Fit MultiLabelBinarizer on genres
    mlb = MultiLabelBinarizer()
    genre_features = mlb.fit_transform(genres_list)

    # 4. Encode 'type' column (Movie vs TV Show)
    le = LabelEncoder()
    type_labels = le.fit_transform(df['type'])  # Movie→0, TV Show→1

    # 5. Train KNN (for recommendations)
    knn_model = NearestNeighbors(n_neighbors=6, algorithm='auto')
    knn_model.fit(genre_features)
    joblib.dump(knn_model, os.path.join(SAVED_MODELS_PATH, 'knn_model.pkl'))

    # 6. Train Decision Tree (to predict 'type')
    dt_model = DecisionTreeClassifier(random_state=42)
    dt_model.fit(genre_features, type_labels)
    joblib.dump(dt_model, os.path.join(SAVED_MODELS_PATH, 'dt_model.pkl'))

    # 7. Train Random Forest (to predict 'type')
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(genre_features, type_labels)
    joblib.dump(rf_model, os.path.join(SAVED_MODELS_PATH, 'rf_model.pkl'))

    # 8. Save the fitted encoders for later use
    joblib.dump(mlb, os.path.join(SAVED_MODELS_PATH, 'mlb.pkl'))
    joblib.dump(le, os.path.join(SAVED_MODELS_PATH, 'le.pkl'))

    print("Models and encoders have been trained and saved to `app/saved_models/`.")

if __name__ == '__main__':
    main()
