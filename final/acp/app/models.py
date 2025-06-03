import os
import pandas as pd
import joblib

APP_ROOT = os.path.dirname(__file__)
DATA_PATH = os.path.join(APP_ROOT, '..', 'data', 'netflix_titles.csv')
SAVED_MODELS_PATH = os.path.join(APP_ROOT, 'saved_models')

def load_data():
    """
    Load the raw CSV, preprocess genres into lists, then use saved MultiLabelBinarizer
    to transform genres into a binary feature matrix. Also load LabelEncoder for 'type'.
    Returns:
      - movies_df: DataFrame indexed by title (columns include 'type', 'genres', etc.).
      - features: numpy array of shape (n_samples, n_genres), one-hot encoded genres.
      - label_encoder: fitted LabelEncoder for the 'type' column.
    """
    df = pd.read_csv(DATA_PATH)
    # Drop rows missing 'listed_in' or 'type'
    df = df.dropna(subset=['listed_in', 'type'])
    # Create a list of genres per movie
    df['genres'] = df['listed_in'].apply(lambda x: [g.strip() for g in x.split(',')])

    # Load the fitted MultiLabelBinarizer and LabelEncoder from saved_models
    mlb = joblib.load(os.path.join(SAVED_MODELS_PATH, 'mlb.pkl'))
    label_encoder = joblib.load(os.path.join(SAVED_MODELS_PATH, 'le.pkl'))

    # Transform genres into binary feature vectors
    genre_features = mlb.transform(df['genres'])

    # Index the DataFrame by title for quick lookups
    movies_df = df.set_index('title')
    return movies_df, genre_features, label_encoder

def load_models():
    """
    Load pretrained scikit-learn models from disk. 
    Returns:
      - knn_model: NearestNeighbors model for recommendations.
      - dt_model: DecisionTreeClassifier for 'type' prediction.
      - rf_model: RandomForestClassifier for 'type' prediction.
    """
    knn_model = joblib.load(os.path.join(SAVED_MODELS_PATH, 'knn_model.pkl'))
    dt_model = joblib.load(os.path.join(SAVED_MODELS_PATH, 'dt_model.pkl'))
    rf_model = joblib.load(os.path.join(SAVED_MODELS_PATH, 'rf_model.pkl'))
    return knn_model, dt_model, rf_model

def recommend_movies(title, movies_df, features, knn_model, n_neighbors=5):
    """
    Given a movie title, find its index in the DataFrame, then use KNN to find
    the nearest neighbors in genre space. Returns a list of recommended titles.
    """
    idx = movies_df.index.get_loc(title)
    distances, indices = knn_model.kneighbors([features[idx]], n_neighbors=n_neighbors+1)
    # Skip the first neighbor (itself)
    rec_indices = indices[0][1:]
    return movies_df.index[rec_indices].tolist()

def predict_type(title, movies_df, features, model, label_encoder):
    """
    Predict whether a given title is a 'Movie' or 'TV Show' using the supplied model.
    Returns the decoded label (string).
    """
    idx = movies_df.index.get_loc(title)
    feature_vector = [features[idx]]
    pred_numeric = model.predict(feature_vector)[0]
    return label_encoder.inverse_transform([pred_numeric])[0]
