import pandas as pd

def load_raw_data(path):
    """
    Load the CSV at `path`, drop invalid rows, and convert 'listed_in' to a
    list of genres. Returns a DataFrame with a new 'genres' column.
    """
    df = pd.read_csv(path)
    df = df.dropna(subset=['listed_in', 'type'])
    df['genres'] = df['listed_in'].apply(lambda x: [g.strip() for g in x.split(',')])
    return df
