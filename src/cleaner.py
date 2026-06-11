import os
import pandas as pd

def clean_data():
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    scraped_path = os.path.join(BASE_DIR, "data", "scraped_books.csv")
    api_path = os.path.join(BASE_DIR, "data", "api_books.csv")
    cleaned_output_path = os.path.join(BASE_DIR, "data", "cleaned_books.csv")

    df_scraped = pd.read_csv(scraped_path)
    df_api = pd.read_csv(api_path)

    expected_cols = [
        'title', 'raw_title', 'author', 'avg_rating', 'ratings_count', 
        'cover_url', 'details_url', 'page_count', 'genres', 'description', 'source'
    ]
    
    df_scraped = df_scraped.reindex(columns=expected_cols)
    df_api = df_api.reindex(columns=expected_cols)

    df_combined = pd.concat([df_scraped, df_api], ignore_index=True)

    df_combined['norm_title'] = df_combined['title'].astype(str).str.lower().str.strip()
    df_combined['norm_author'] = df_combined['author'].astype(str).str.lower().str.strip()

    before_len = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=['norm_title', 'norm_author'], keep='first')
    after_len = len(df_combined)

    df_combined = df_combined.drop(columns=['norm_title', 'norm_author'])

    df_combined['avg_rating'] = pd.to_numeric(df_combined['avg_rating'], errors='coerce').fillna(0.0).round(2)
    df_combined['ratings_count'] = pd.to_numeric(df_combined['ratings_count'], errors='coerce').fillna(0).astype(int)
    
    median_pages = df_combined[df_combined['page_count'] > 0]['page_count'].median()
    if pd.isna(median_pages) or median_pages <= 0:
        median_pages = 250  
    df_combined['page_count'] = pd.to_numeric(df_combined['page_count'], errors='coerce').fillna(0).astype(int)
    df_combined.loc[df_combined['page_count'] <= 0, 'page_count'] = int(median_pages)

    df_combined['description'] = df_combined['description'].fillna('').astype(str).str.strip()
    df_combined.loc[df_combined['description'] == '', 'description'] = "No description available."

    df_combined['genres'] = df_combined['genres'].fillna('').astype(str).str.strip()
    df_combined.loc[df_combined['genres'] == '', 'genres'] = "General"

    df_combined['cover_url'] = df_combined['cover_url'].fillna('').astype(str).str.strip()
    placeholder_cover = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?q=80&w=300&auto=format&fit=crop"
    df_combined.loc[df_combined['cover_url'] == '', 'cover_url'] = placeholder_cover
    df_combined.loc[df_combined['cover_url'].str.contains('nophoto', case=False, na=False), 'cover_url'] = placeholder_cover

    df_combined = df_combined.sort_values(by='avg_rating', ascending=False)
    os.makedirs(os.path.dirname(cleaned_output_path), exist_ok=True)
    df_combined.to_csv(cleaned_output_path, index=False)
    print(f"Data Cleaned Successfully")
