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

    # Relevance filtering: remove non-programming/non-CS books
    import re
    
    positive_keywords = [
        'programming', 'programmer', 'program', 'code', 'coding', 'software', 'computer science', 
        'developer', 'develop', 'web dev', 'frontend', 'backend', 'algorithm', 'database', 
        'data structures', 'hacker', 'devops', 'refactoring', 'microservices', 'agile', 'scrum', 
        'git', 'github', 'docker', 'kubernetes', 'cloud computing', 'system design', 
        'software architecture', 'clean code', 'machine learning', 'artificial intelligence', 
        'neural network', 'data science', 'deep learning', 'design patterns', 'compilers', 
        'operating systems', 'networks', 'cryptography', 'web development', 'unix', 'linux', 
        'information technology', 'devsecops', 'object-oriented', 'oop', 'computer programming', 
        'lisp', 'python', 'javascript', 'java', 'c++', 'c#', 'rust', 'golang', 'typescript', 
        'kotlin', 'swift', 'scala', 'haskell'
    ]
    
    negative_keywords = [
        'comic', 'manga', 'graphic novel', 'cartoon', 'avatar', 'airbender', 'fiction', 'novel', 
        'fantasy', 'romance', 'thriller', 'mystery', 'poetry', 'self-help', 'habits', 'parenting', 
        'health', 'diet', 'recipe', 'cookbook', 'spiritual', 'religion', 'yoga', 'meditation', 
        'biography', 'autobiography', 'history', 'politics', 'economics', 'finance', 'investing', 
        'marketing', 'children\'s book', 'picture book', 'dressed book'
    ]
    
    strong_exclusions = [
        'avatar', 'airbender', 'legend of aang', 'legend of korra', 'archie #', 'archie comics', 
        'last airbender', 'dressed book'
    ]
    
    def is_relevant(row):
        title = str(row.get('title', '')).lower()
        raw_title = str(row.get('raw_title', '')).lower()
        genres = str(row.get('genres', '')).lower()
        description = str(row.get('description', '')).lower()
        
        # 1. Check strong exclusions in title
        for exc in strong_exclusions:
            if exc in title or exc in raw_title:
                return False
                
        # 2. Check if it's a comic/manga/cartoon (unless it has strong coding terms)
        is_comic = any(x in genres or x in title for x in ['comic', 'manga', 'graphic novel', 'cartoon', 'anime'])
        if is_comic:
            strong_programming_kw = ['programming', 'programmer', 'python', 'javascript', 'java', 'sql', 'database', 'code', 'coding', 'algorithms']
            if not any(kw in title or kw in genres for kw in strong_programming_kw):
                return False
                
        # 3. Calculate positive score
        pos_score = 0
        for kw in positive_keywords:
            if len(kw) <= 3:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, title) or re.search(pattern, raw_title):
                    pos_score += 3
                if re.search(pattern, genres):
                    pos_score += 2
                if re.search(pattern, description):
                    pos_score += 1
            else:
                if kw in title or kw in raw_title:
                    pos_score += 3
                if kw in genres:
                    pos_score += 2
                if kw in description:
                    pos_score += 1
                    
        # 4. Calculate negative score
        neg_score = 0
        for kw in negative_keywords:
            if kw in title or kw in raw_title or kw in genres or kw in description:
                neg_score += 2
                
        # 5. Threshold check
        return pos_score >= 3 and pos_score > neg_score

    pre_filter_len = len(df_combined)
    df_combined = df_combined[df_combined.apply(is_relevant, axis=1)]
    post_filter_len = len(df_combined)
    print(f"Relevance Filter: Kept {post_filter_len} out of {pre_filter_len} books (Removed {pre_filter_len - post_filter_len} irrelevant books).")


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
