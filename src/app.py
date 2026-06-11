import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from model import (
    get_recommendations, 
    get_cluster_recommendations, 
    build_and_train_model, 
    CLUSTERED_DATA_PATH,
    MODEL_FILEPATH
)

st.set_page_config(
    page_title="Good Reads Book Recommender",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
    color: #f5f6fa;
}

.book-card {
    background: rgba(24, 24, 24, 0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex;
    flex-direction: column;
    height: auto;
    min-height: 580px;
}

.book-card:hover {
    transform: translateY(-8px);
    border-color: rgba(155, 89, 182, 0.5);
    box-shadow: 0 15px 35px 0 rgba(155, 89, 182, 0.2);
    background: rgba(255, 255, 255, 0.05);
}

.image-container {
    width: 100%;
    height: 320px;
    overflow: hidden;
    border-radius: 10px;
    margin-bottom: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #1a1a1a;
    flex-shrink: 0;
}

.book-cover {
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;
    transition: transform 0.3s ease;
}

.genre-container {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 10px;
}

.genre-badge {
    background: rgba(52, 152, 219, 0.12);
    color: #3498db;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid rgba(52, 152, 219, 0.25);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 120px;
}

.rating-badge {
    background: rgba(241, 196, 15, 0.15);
    color: #f1c40f;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(241, 196, 15, 0.3);
}

.book-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 4px;
    color: #ffffff;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 2.6em;
    flex-shrink: 0;
}

.book-author {
    font-size: 0.82rem;
    font-weight: 500;
    color: #bdc3c7;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.book-meta {
    font-size: 0.78rem;
    color: #a4b0be;
    margin-top: auto;
    line-height: 1.5;
}

div.stButton > button {
    background-color: #9b59b6;
    color: white;
    border-radius: 8px;
    border: none;
    transition: all 0.2s ease;
}
div.stButton > button:hover {
    background-color: #8e44ad;
    box-shadow: 0 4px 15px rgba(155, 89, 182, 0.4);
}
</style>
""", unsafe_allow_html=True)

BANNER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_header_banner.png")
DATA_PATH = CLUSTERED_DATA_PATH

if os.path.exists(BANNER_PATH):
    st.image(BANNER_PATH, use_container_width=True)
else:
    st.title("Ironhack Book Recommender")
    st.subheader("Smart Programming Book Recommendations")

if not os.path.exists(CLUSTERED_DATA_PATH) or not os.path.exists(MODEL_FILEPATH):
    with st.spinner("Building and training recommender model..."):
        build_and_train_model()

st.sidebar.markdown("## ⚙️ Filters & Settings")
st.sidebar.markdown("Adjust parameters to find your perfect books.")

min_rating = st.sidebar.slider(
    "⭐ Minimum Rating",
    min_value=0.0,
    max_value=5.0,
    value=3.5,
    step=0.1
)

max_pages = st.sidebar.slider(
    "📄 Maximum Page Count",
    min_value=50,
    max_value=1500,
    value=800,
    step=50
)

num_recommendations = st.sidebar.slider(
    "🎯 Number of Books to Show",
    min_value=1,
    max_value=10,
    value=6
)

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    return pd.read_csv(DATA_PATH)

df = load_data()

if df is None:
    st.error("🚨 Clustered books dataset not found. Please train your model by running `python3 src/model.py` first!")
    st.stop()

def apply_filters(rec_list):
    filtered = []
    for book, score in rec_list:
        if book['avg_rating'] < min_rating:
            continue
        if book['page_count'] > max_pages:
            continue
        filtered.append((book, score))
    return filtered

def display_book_grid(books_list):
    if not books_list:
        st.info("No books match your criteria. Try adjusting the filters on the sidebar!")
        return

    for i in range(0, len(books_list), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(books_list):
                book, score = books_list[i + j]
                col = cols[j]
                
                title = book['title']
                author = book['author']
                cover_url = book['cover_url']
                
                if pd.isna(cover_url) or not cover_url or "nophoto" in str(cover_url):
                    cover_url = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?q=80&w=300&auto=format&fit=crop"
                
                rating = book['avg_rating']
                reviews = book['ratings_count']
                pages = book['page_count']
                genres = book['genres']
                description = book['description']
                
                genre_pills = ""
                if pd.notna(genres) and genres:
                    for g in str(genres).split(',')[:3]:
                        genre_pills += f'<span class="genre-badge" title="{g.strip()}">{g.strip()}</span>'

                with col:
                    card_html = f"""
                    <div class="book-card">
                        <div class="image-container">
                            <img src="{cover_url}" class="book-cover" style="width: 100% !important; height: 100% !important; object-fit: contain !important;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1543002588-bfa74002ed7e?q=80&w=300&auto=format&fit=crop';"/>
                        </div>
                        <div class="book-title" title="{title}">{title}</div>
                        <div class="book-author">by {author}</div>
                        <div style="margin-bottom: 8px;">
                            <span class="rating-badge">⭐ {rating:.2f}</span>
                        </div>
                        <div class="genre-container">
                            {genre_pills}
                        </div>
                        <div class="book-meta">
                            📄 <b>Pages:</b> {int(pages)} <br>
                            👥 <b>Reviews:</b> {int(reviews):,}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

# tab1, tab2 = st.tabs(["Beginner Learning Paths", "Similar Book Finder"])
tab2 = st.text("Similar Book Finder")
st.markdown("### Find Similar Books")
book_options = df['title'].unique()

selected_book = st.selectbox(
    "Select a book you like:",
    options=book_options,
    index=None,
    placeholder="Type to search for a book..."
)

if selected_book:
    raw_recs = get_recommendations(selected_book, num_recommendations=25)
    filtered_recs = apply_filters(raw_recs)[:num_recommendations]

    st.markdown(f"#### 📚 If you liked **{selected_book}**, check these out:")
    display_book_grid(filtered_recs)

# with tab1:
#     st.markdown("### Pick a Coding Track to Start Programming")

#     path_options = {
#         "Software Engineering & Clean Architecture": 0,
#         "Web Development (HTML, CSS, Frontend)": 1,
#         "Python & Systems Programming": 2,
#         "JavaScript & Modern Scripting": 4,
#         "Computer Science Foundations & Algorithms": 6,
#         "Java & JVM Enterprise Development": 8,
#         "Object-Oriented Design & OOP Patterns": 9
#     }

#     selected_path = st.selectbox("Select your starting track:", list(path_options.keys()))
#     cluster_id = path_options[selected_path]

#     raw_recs = get_cluster_recommendations(cluster_id, num_recommendations=25)
#     filtered_recs = apply_filters(raw_recs)[:num_recommendations]

#     st.markdown(f"#### Top Recommendations for **{selected_path}**")
#     display_book_grid(filtered_recs)

# with tab2:
#     st.markdown("### Find Similar Books")
#     book_options = df['title'].unique()

#     selected_book = st.selectbox(
#         "Select a book you like:",
#         options=book_options,
#         index=None,
#         placeholder="Type to search for a book..."
#     )

#     if selected_book:
#         raw_recs = get_recommendations(selected_book, num_recommendations=25)
#         filtered_recs = apply_filters(raw_recs)[:num_recommendations]

#         st.markdown(f"#### 📚 If you liked **{selected_book}**, check these out:")
#         display_book_grid(filtered_recs)
