from flask import Blueprint, render_template, request
from .models import load_data, load_models, recommend_movies, predict_type

main = Blueprint('main', __name__)

# Load the dataset, feature matrix, and label encoder once at startup
movies_df, features, label_encoder = load_data()
knn_model, dt_model, rf_model = load_models()

@main.route('/', methods=['GET', 'POST'])
def index():
    """
    Home route: displays a form to input a movie title.  
    On POST, if the title exists, compute KNN-based recommendations 
    and type predictions via Decision Tree and Random Forest.
    """
    context = {}
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if title in movies_df.index:
            # KNN recommendations
            recommendations = recommend_movies(title, movies_df, features, knn_model)
            # Predict type ('Movie' vs 'TV Show') using both classifiers
            type_dt = predict_type(title, movies_df, features, dt_model, label_encoder)
            type_rf = predict_type(title, movies_df, features, rf_model, label_encoder)
            context.update({
                'title': title,
                'recommendations': recommendations,
                'type_dt': type_dt,
                'type_rf': type_rf
            })
        else:
            context['error'] = 'Movie not found in database. Please check your spelling or try another title.'
    return render_template('index.html', **context)
