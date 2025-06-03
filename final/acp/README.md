# Movie Recommendation App

A modular Flask application that provides movie recommendations based on Netflix‐style metadata.  
Implements machine learning (KNN, Decision Tree, Random Forest) using scikit‐learn and features a Tailwind CSS–styled UI.

---

## Project Structure


- **`app/`**: Flask application package  
  - **`__init__.py`**: Creates and configures the Flask app.  
  - **`main.py`**: Entrypoint for local development.  
  - **`routes.py`**: Defines the index route and handles form submissions.  
  - **`models.py`**: Loads dataset, feature matrix, encoders, and pretrained models. Exposes functions:  
    - `recommend_movies(...)` – returns KNN‐based recommendations.  
    - `predict_type(...)` – uses Decision Tree or Random Forest to predict if a title is “Movie” or “TV Show.”  
  - **`data_processing.py`**: Utility to load and preprocess raw CSV for model training.  
  - **`saved_models/`**: Holds pickled `(knn_model.pkl, dt_model.pkl, rf_model.pkl, mlb.pkl, le.pkl)`.  
  - **`templates/index.html`**: Tailwind CSS–styled front‐end.

- **`data/netflix_titles.csv`**: Source dataset (Netflix metadata).

- **`ml/train_models.py`**: Script to preprocess data, train KNN + classifiers, and dump them under `app/saved_models/`.

- **`requirements.txt`**: Python dependencies.

---

## Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/yourusername/movie-recommender.git
   cd movie-recommender
