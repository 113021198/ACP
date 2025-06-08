import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os

import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import hstack, csr_matrix

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------------
# 1. Data Loading & Preprocessing
# ------------------------------------------------------------------------------
DATA_PATH = 'netflix_titles.csv'

df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=['listed_in', 'description', 'rating'])
df['genres_list'] = df['listed_in'].str.split(', ')

mlb = MultiLabelBinarizer()
genre_ohe = mlb.fit_transform(df['genres_list'])

tfidf = TfidfVectorizer(max_features=500)
desc_tfidf = tfidf.fit_transform(df['description'].fillna(''))

year_values = df['release_year'].values.reshape(-1, 1)

X_rec = hstack([csr_matrix(year_values), csr_matrix(genre_ohe), desc_tfidf])

nn_model = NearestNeighbors(n_neighbors=6, metric='cosine')
nn_model.fit(X_rec)

# ------------------------------------------------------------------------------
# 2. Helper Functions
# ------------------------------------------------------------------------------
def filter_movies(genres, rating, year_from, year_to):
    """
    Filter by multi-genre list, rating, and year range.
    """
    mask = pd.Series(True, index=df.index)

    if genres:
        mask &= df['genres_list'].apply(lambda lst: any(g in lst for g in genres))
    if rating:
        mask &= (df['rating'] == rating)
    if year_from is not None:
        mask &= (df['release_year'] >= year_from)
    if year_to is not None:
        mask &= (df['release_year'] <= year_to)

    return df[mask]


def find_exact_titles(partial_title):
    mask = df['title'].str.contains(partial_title, case=False, na=False)
    return df[mask]


def recommend_similar(title):
    matches = df.index[df['title'].str.lower() == title.lower()]
    if len(matches) == 0:
        return pd.DataFrame()
    idx = matches[0]
    distances, indices = nn_model.kneighbors(X_rec[idx], n_neighbors=6)
    rec_indices = indices.flatten()[1:]
    return df.iloc[rec_indices][['title', 'listed_in', 'release_year']].reset_index(drop=True)


def load_watchlist():
    if not os.path.exists('watchlist.json'):
        return []
    with open('watchlist.json', 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_watchlist(watchlist):
    with open('watchlist.json', 'w', encoding='utf-8') as f:
        json.dump(watchlist, f, indent=2)


# ------------------------------------------------------------------------------
# 3. Tkinter Application with Modern Styling
# ------------------------------------------------------------------------------
class MovieRecommenderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Movie Recommender – Modern UI")
        self.geometry("1000x700")
        self.configure(bg='#ECEFF1')
        self.resizable(True, True)

        # Apply ttk theme and styles
        style = ttk.Style(self)
        style.theme_use('clam')

        # Notebook/tab styles
        style.configure('TNotebook', background='#ECEFF1', borderwidth=0)
        style.configure('TNotebook.Tab',
                        background='#37474F',
                        foreground='white',
                        padding=(10, 5),
                        font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                  background=[('selected', '#1E88E5')],
                  foreground=[('selected', 'white')])

        # Frame styles
        style.configure('TFrame', background='#ECEFF1')
        style.configure('TLabelFrame', background='#ECEFF1', foreground='#37474F', font=('Segoe UI', 11, 'bold'))

        # Label styles
        style.configure('TLabel', background='#ECEFF1', foreground='#37474F', font=('Segoe UI', 10))

        # Button styles
        style.configure('Accent.TButton',
                        background='#1E88E5',
                        foreground='white',
                        font=('Segoe UI', 10, 'bold'),
                        padding=5)
        style.map('Accent.TButton',
                  background=[('active', '#1565C0')],
                  foreground=[('active', 'white')])

        # Widgets variables
        self.selected_genres = []
        self.selected_rating = tk.StringVar()
        self.year_from = tk.IntVar(value=1900)
        self.year_to = tk.IntVar(value=2025)
        self.title_search_var = tk.StringVar()

        self.watchlist = load_watchlist()

        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Browse by Filters
        tab_filter = ttk.Frame(notebook)
        notebook.add(tab_filter, text="Browse by Filters")
        self.build_filter_tab(tab_filter)

        # Tab 2: Title-based Recommendation
        tab_title = ttk.Frame(notebook)
        notebook.add(tab_title, text="Title-based Recommendation")
        self.build_title_tab(tab_title)

        # Tab 3: Watchlist
        tab_watchlist = ttk.Frame(notebook)
        notebook.add(tab_watchlist, text="Watchlist")
        self.build_watchlist_tab(tab_watchlist)

        # Tab 4: Stats
        tab_stats = ttk.Frame(notebook)
        notebook.add(tab_stats, text="Stats")
        self.build_stats_tab(tab_stats)

    # ---------------------- Filter Tab ----------------------
    def build_filter_tab(self, parent):
        for col in range(4):
            parent.columnconfigure(col, weight=[1, 2, 1, 2][col])
        parent.rowconfigure(5, weight=1)  # make listbox expand

        # Genres Label + Listbox (multi-select)
        ttk.Label(parent, text="Genres:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        genre_listbox = tk.Listbox(parent,
                                   selectmode='extended',
                                   bg='white',
                                   fg='#37474F',
                                   highlightbackground='#B0BEC5',
                                   selectbackground='#90CAF9',
                                   selectforeground='white',
                                   font=('Segoe UI', 10),
                                   bd=1,
                                   relief='solid')
        for g in sorted(mlb.classes_):
            genre_listbox.insert(tk.END, g)
        genre_listbox.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=5, pady=5)

        def on_genre_select(evt):
            selection = genre_listbox.curselection()
            self.selected_genres = [genre_listbox.get(i) for i in selection]

        genre_listbox.bind('<<ListboxSelect>>', on_genre_select)

        # Rating Label + Combobox
        ttk.Label(parent, text="Rating:").grid(row=0, column=2, sticky='e', padx=5, pady=5)
        all_ratings = sorted([r for r in df['rating'].unique() if isinstance(r, str) and "min" not in r.lower()])
        rating_combo = ttk.Combobox(parent,
                                    textvariable=self.selected_rating,
                                    values=all_ratings,
                                    state='readonly',
                                    font=('Segoe UI', 10))
        rating_combo.grid(row=0, column=3, sticky='ew', padx=5, pady=5)
        rating_combo.set(all_ratings[0])

        # Year From / To Spinboxes
        ttk.Label(parent, text="Year From:").grid(row=1, column=2, sticky='e', padx=5, pady=5)
        year_from_spin = tk.Spinbox(parent,
                                    from_=1900,
                                    to=2025,
                                    textvariable=self.year_from,
                                    width=8,
                                    font=('Segoe UI', 10),
                                    bg='white',
                                    bd=1,
                                    relief='solid')
        year_from_spin.grid(row=1, column=3, sticky='w', padx=5, pady=5)

        ttk.Label(parent, text="Year To:").grid(row=2, column=2, sticky='e', padx=5, pady=5)
        year_to_spin = tk.Spinbox(parent,
                                  from_=1900,
                                  to=2025,
                                  textvariable=self.year_to,
                                  width=8,
                                  font=('Segoe UI', 10),
                                  bg='white',
                                  bd=1,
                                  relief='solid')
        year_to_spin.grid(row=2, column=3, sticky='w', padx=5, pady=5)

        # Search Button
        search_btn = ttk.Button(parent,
                                text="Search",
                                style='Accent.TButton',
                                command=self.on_filter_search)
        search_btn.grid(row=3, column=0, columnspan=4, pady=10, sticky='ew')

        # Filtered Listbox
        self.filtered_listbox = tk.Listbox(parent,
                                           bg='white',
                                           fg='#37474F',
                                           highlightbackground='#B0BEC5',
                                           selectbackground='#90CAF9',
                                           selectforeground='white',
                                           font=('Segoe UI', 10),
                                           bd=1,
                                           relief='solid')
        self.filtered_listbox.grid(row=5, column=0, columnspan=3, rowspan=2,
                                   sticky='nsew', padx=5, pady=5)

        # Details Panel for Filtered Tab
        details_frame = ttk.LabelFrame(parent, text="Details")
        details_frame.grid(row=5, column=3, rowspan=2, sticky='nsew', padx=5, pady=5)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)

        self.details_text = scrolledtext.ScrolledText(details_frame,
                                                      wrap=tk.WORD,
                                                      state='disabled',
                                                      font=('Segoe UI', 10),
                                                      bg='white',
                                                      fg='#37474F',
                                                      bd=1,
                                                      relief='solid')
        self.details_text.grid(row=0, column=0, sticky='nsew')

        self.filtered_listbox.bind('<<ListboxSelect>>', self.show_filtered_details)

    def on_filter_search(self):
        genres = self.selected_genres
        rating = self.selected_rating.get()
        y_from = self.year_from.get()
        y_to = self.year_to.get()

        filtered = filter_movies(genres, rating, y_from, y_to)
        self.filtered_listbox.delete(0, tk.END)
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.config(state='disabled')

        if filtered.empty:
            messagebox.showinfo("No Results", "No movies match the selected filters.")
            return

        for idx, row in filtered.iterrows():
            self.filtered_listbox.insert(tk.END, f"{row['title']} ({row['release_year']})")

    def show_filtered_details(self, event):
        sel = self.filtered_listbox.curselection()
        if not sel:
            return
        title_with_year = self.filtered_listbox.get(sel[0])
        title = title_with_year.rsplit(" (", 1)[0]
        movie_row = df[df['title'] == title].iloc[0]

        details = (
            f"Title: {movie_row['title']}\n"
            f"Year: {movie_row['release_year']}\n"
            f"Genres: {movie_row['listed_in']}\n"
            f"Rating: {movie_row['rating']}\n"
            f"Director: {movie_row.get('director', 'N/A')}\n"
            f"Cast: {movie_row.get('cast', 'N/A')}\n"
            f"Country: {movie_row.get('country', 'N/A')}\n"
            f"Duration: {movie_row.get('duration', 'N/A')}\n\n"
            f"Description:\n{movie_row['description']}"
        )
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.config(state='disabled')

    # ------------------ Title-based Recommendation Tab ------------------
    def build_title_tab(self, parent):
        for col in range(3):
            parent.columnconfigure(col, weight=[1, 3, 1][col])
        parent.rowconfigure(1, weight=1)
        parent.rowconfigure(3, weight=1)

        ttk.Label(parent, text="Enter Title (partial or full):").grid(
            row=0, column=0, sticky='e', padx=5, pady=5)
        title_entry = ttk.Entry(parent,
                                textvariable=self.title_search_var,
                                font=('Segoe UI', 10))
        title_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        find_btn = ttk.Button(parent,
                              text="Find Titles",
                              style='Accent.TButton',
                              command=self.on_find_titles)
        find_btn.grid(row=0, column=2, sticky='w', padx=5, pady=5)

        self.match_listbox = tk.Listbox(parent,
                                        bg='white',
                                        fg='#37474F',
                                        highlightbackground='#B0BEC5',
                                        selectbackground='#90CAF9',
                                        selectforeground='white',
                                        font=('Segoe UI', 10),
                                        bd=1,
                                        relief='solid')
        self.match_listbox.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
        self.match_listbox.bind('<<ListboxSelect>>', self.show_match_details)

        rec_btn = ttk.Button(parent,
                             text="Recommend Similar",
                             style='Accent.TButton',
                             command=self.on_recommend)
        rec_btn.grid(row=2, column=0, columnspan=3, pady=10, sticky='ew')

        self.recommend_listbox = tk.Listbox(parent,
                                            bg='white',
                                            fg='#37474F',
                                            highlightbackground='#B0BEC5',
                                            selectbackground='#90CAF9',
                                            selectforeground='white',
                                            font=('Segoe UI', 10),
                                            bd=1,
                                            relief='solid')
        self.recommend_listbox.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
        self.recommend_listbox.bind('<<ListboxSelect>>', self.show_recommend_details)

        # Details panel for Title tab
        details_frame2 = ttk.LabelFrame(parent, text="Details")
        details_frame2.grid(row=1, column=3, rowspan=3, sticky='nsew', padx=5, pady=5)
        details_frame2.columnconfigure(0, weight=1)
        details_frame2.rowconfigure(0, weight=1)

        self.details_text2 = scrolledtext.ScrolledText(details_frame2,
                                                       wrap=tk.WORD,
                                                       state='disabled',
                                                       font=('Segoe UI', 10),
                                                       bg='white',
                                                       fg='#37474F',
                                                       bd=1,
                                                       relief='solid')
        self.details_text2.grid(row=0, column=0, sticky='nsew')

    def on_find_titles(self):
        partial = self.title_search_var.get().strip()
        if not partial:
            messagebox.showwarning("Input Required", "Please enter part of a title.")
            return

        matches = find_exact_titles(partial)
        self.match_listbox.delete(0, tk.END)
        self.recommend_listbox.delete(0, tk.END)
        self.details_text2.config(state='normal')
        self.details_text2.delete('1.0', tk.END)
        self.details_text2.config(state='disabled')

        if matches.empty:
            messagebox.showinfo("No Matches", f"No titles containing '{partial}'.")
            return

        for _, row in matches.iterrows():
            self.match_listbox.insert(tk.END, row['title'])

    def show_match_details(self, event):
        sel = self.match_listbox.curselection()
        if not sel:
            return
        title = self.match_listbox.get(sel[0])
        movie_row = df[df['title'] == title].iloc[0]

        details = (
            f"Title: {movie_row['title']}\n"
            f"Year: {movie_row['release_year']}\n"
            f"Genres: {movie_row['listed_in']}\n"
            f"Rating: {movie_row['rating']}\n"
            f"Director: {movie_row.get('director', 'N/A')}\n"
            f"Cast: {movie_row.get('cast', 'N/A')}\n"
            f"Country: {movie_row.get('country', 'N/A')}\n"
            f"Duration: {movie_row.get('duration', 'N/A')}\n\n"
            f"Description:\n{movie_row['description']}"
        )
        self.details_text2.config(state='normal')
        self.details_text2.delete('1.0', tk.END)
        self.details_text2.insert(tk.END, details)
        self.details_text2.config(state='disabled')

    def on_recommend(self):
        sel = self.match_listbox.curselection()
        if not sel:
            messagebox.showwarning("No Title Selected", "Please select a title first.")
            return

        selected_title = self.match_listbox.get(sel[0])
        recs = recommend_similar(selected_title)

        self.recommend_listbox.delete(0, tk.END)
        self.details_text2.config(state='normal')
        self.details_text2.delete('1.0', tk.END)
        self.details_text2.config(state='disabled')

        if recs.empty:
            messagebox.showinfo("No Recommendations", "Could not find similar movies.")
            return

        for _, row in recs.iterrows():
            self.recommend_listbox.insert(tk.END, f"{row['title']} ({row['release_year']})")

    def show_recommend_details(self, event):
        sel = self.recommend_listbox.curselection()
        if not sel:
            return
        title_with_year = self.recommend_listbox.get(sel[0])
        title = title_with_year.rsplit(" (", 1)[0]
        movie_row = df[df['title'] == title].iloc[0]

        details = (
            f"Title: {movie_row['title']}\n"
            f"Year: {movie_row['release_year']}\n"
            f"Genres: {movie_row['listed_in']}\n"
            f"Rating: {movie_row['rating']}\n"
            f"Director: {movie_row.get('director', 'N/A')}\n"
            f"Cast: {movie_row.get('cast', 'N/A')}\n"
            f"Country: {movie_row.get('country', 'N/A')}\n"
            f"Duration: {movie_row.get('duration', 'N/A')}\n\n"
            f"Description:\n{movie_row['description']}"
        )
        self.details_text2.config(state='normal')
        self.details_text2.delete('1.0', tk.END)
        self.details_text2.insert(tk.END, details)
        self.details_text2.config(state='disabled')

    # ---------------------- Watchlist Tab ----------------------
    def build_watchlist_tab(self, parent):
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # Watchlist Listbox
        self.watchlist_box = tk.Listbox(parent,
                                        bg='white',
                                        fg='#37474F',
                                        highlightbackground='#B0BEC5',
                                        selectbackground='#90CAF9',
                                        selectforeground='white',
                                        font=('Segoe UI', 10),
                                        bd=1,
                                        relief='solid')
        self.watchlist_box.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.update_watchlist_box()

        # Buttons Frame
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

        add_btn = ttk.Button(btn_frame, text="Add Selected to Watchlist", style='Accent.TButton',
                             command=self.add_to_watchlist)
        add_btn.pack(pady=10, fill='x')

        remove_btn = ttk.Button(btn_frame, text="Remove Selected", style='Accent.TButton',
                                command=self.remove_from_watchlist)
        remove_btn.pack(pady=10, fill='x')

        export_btn = ttk.Button(btn_frame, text="Export Watchlist to CSV", style='Accent.TButton',
                                command=self.export_watchlist)
        export_btn.pack(pady=10, fill='x')

    def update_watchlist_box(self):
        self.watchlist_box.delete(0, tk.END)
        for movie in self.watchlist:
            self.watchlist_box.insert(tk.END, movie)

    def add_to_watchlist(self):
        sel_filtered = self.filtered_listbox.curselection()
        sel_recommended = self.recommend_listbox.curselection()
        if sel_filtered:
            title_with_year = self.filtered_listbox.get(sel_filtered[0])
            title = title_with_year.rsplit(" (", 1)[0]
        elif sel_recommended:
            title_with_year = self.recommend_listbox.get(sel_recommended[0])
            title = title_with_year.rsplit(" (", 1)[0]
        else:
            messagebox.showwarning("No Selection", "Please select a movie from either the Filter or Recommendation list to add.")
            return

        if title in self.watchlist:
            messagebox.showinfo("Already in Watchlist", f"'{title}' is already in your watchlist.")
            return

        self.watchlist.append(title)
        save_watchlist(self.watchlist)
        self.update_watchlist_box()
        messagebox.showinfo("Added", f"'{title}' has been added to your watchlist.")

    def remove_from_watchlist(self):
        sel = self.watchlist_box.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a movie in your watchlist to remove.")
            return
        title = self.watchlist_box.get(sel[0])
        self.watchlist.remove(title)
        save_watchlist(self.watchlist)
        self.update_watchlist_box()
        messagebox.showinfo("Removed", f"'{title}' has been removed from your watchlist.")

    def export_watchlist(self):
        if not self.watchlist:
            messagebox.showinfo("Empty Watchlist", "Your watchlist is empty.")
            return
        export_df = df[df['title'].isin(self.watchlist)][
            ['title', 'release_year', 'listed_in', 'rating', 'director', 'cast', 'country', 'duration', 'description']
        ]
        export_df.to_csv('watchlist_export.csv', index=False)
        messagebox.showinfo("Exported", "Watchlist exported to 'watchlist_export.csv'.")

    # ---------------------- Stats Tab ----------------------
    def build_stats_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        stats_frame = ttk.Frame(parent)
        stats_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # Genre distribution (top 10)
        genre_counts = df['genres_list'].explode().value_counts().nlargest(10)
        axes[0].pie(genre_counts, labels=genre_counts.index, autopct='%1.1f%%', startangle=140)
        axes[0].set_title("Top 10 Genres", fontsize=10, fontname='Segoe UI')

        # Rating distribution
        rating_counts = df['rating'].value_counts().nlargest(10)
        axes[1].bar(rating_counts.index, rating_counts.values, color='#1E88E5')
        axes[1].set_title("Top 10 Ratings", fontsize=10, fontname='Segoe UI')
        axes[1].tick_params(axis='x', rotation=45, labelsize=8)

        # Release year histogram
        axes[2].hist(df['release_year'], bins=20, color='#1E88E5')
        axes[2].set_title("Release Year Distribution", fontsize=10, fontname='Segoe UI')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=stats_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)


# ------------------------------------------------------------------------------
# 4. Launch
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    app = MovieRecommenderApp()
    app.mainloop()
