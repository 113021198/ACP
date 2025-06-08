Wirandito Sarwono - 113021198
Dimas Ahmad Fahreza - 113021199
Radian Try Darmawan - 113021220

# Our Final Project

# Movie Recommender

A Python-based movie recommendation application with a modern Tkinter GUI that helps users discover Netflix content through filtering and content-based recommendations.

## Features

- **Multi-Filter Search**: Filter movies by genres, ratings, and release year ranges
- **Content-Based Recommendations**: Find similar movies using machine learning (cosine similarity)
- **Title Search**: Search for movies by partial or full title matches
- **Personal Watchlist**: Save, manage, and export your movie watchlist
- **Data Visualization**: Interactive charts showing genre distribution, ratings, and release year trends
- **Persistent Storage**: Watchlist data saved in JSON format across sessions

## Requirements

```
pandas
scikit-learn
matplotlib
scipy
tkinter (included with Python)
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/113021198/ACP/tree/main/final
cd final
```

2. Install required packages:
```bash
pip install pandas scikit-learn matplotlib scipy
```

3. Ensure you have the Netflix dataset file `netflix_titles.csv` in the same directory

## Usage

Run the application:
```bash
python movie_recommendation.py
```

### Interface Tabs

1. **Browse by Filters**: Select multiple genres, ratings, and year ranges to find movies
2. **Title-based Recommendation**: Search for a movie and get similar recommendations
3. **Watchlist**: Manage your saved movies and export to CSV
4. **Stats**: View dataset statistics with interactive charts

## Technical Details

- **Recommendation Engine**: Uses TF-IDF vectorization on movie descriptions combined with genre encoding and release year data
- **Machine Learning**: Implements k-nearest neighbors with cosine distance for similarity matching
- **GUI Framework**: Modern Tkinter interface with ttk styling and embedded Matplotlib charts
- **Data Processing**: Pandas DataFrames with MultiLabelBinarizer for genre handling

## Dataset

The application expects a Netflix titles CSV file with columns including:
- title, release_year, listed_in (genres), description, rating, director, cast, country, duration

## Project Team

**Group 4 - Advanced Computer Programming**
- Radian Try Darmawan (113021220)
- Dimas Ahmad Fahreza (113021199)  
- Wirandito Sarwono (113021198)

**Instructor**: DINH-TRUNG VU  
**Institution**: Asia University  
**Date**: 2025-06

## License

This project was developed as part of an academic course at Asia University.
