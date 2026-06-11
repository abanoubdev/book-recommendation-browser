import os
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DATA_PATH = os.path.join(BASE_DIR, "data", "cleaned_books.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_FILEPATH = os.path.join(MODEL_DIR, "recommender_models.pkl")
CLUSTERED_DATA_PATH = os.path.join(BASE_DIR, "data", "clustered_books.csv")

def build_and_train_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(CLEANED_DATA_PATH):
        raise FileNotFoundError(f"Cleaned books dataset not found: {CLEANED_DATA_PATH}")

    df = pd.read_csv(CLEANED_DATA_PATH)

    combined_text = df['genres'].fillna('') + " " + df['genres'].fillna('') + " " + df['description'].fillna('')
    df['combined_text'] = combined_text

    tfidf = TfidfVectorizer(stop_words='english', max_features=1500)
    tfidf_matrix = tfidf.fit_transform(df['combined_text'])

    n_pca_components = min(15, tfidf_matrix.shape[0], tfidf_matrix.shape[1])
    pca = PCA(n_components=n_pca_components, random_state=42)
    tfidf_dense = tfidf_matrix.toarray()
    pca_features = pca.fit_transform(tfidf_dense)

    scaler = StandardScaler()
    numerical_features = df[['avg_rating', 'page_count']].values
    scaled_numerical = scaler.fit_transform(numerical_features)

    weighted_numerical = scaled_numerical * 0.5
    combined_features = np.hstack((pca_features, weighted_numerical))

    num_clusters = 10
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(combined_features)

    df.to_csv(CLUSTERED_DATA_PATH, index=False)

    similarity_matrix = cosine_similarity(combined_features)
    
    models = {
        'tfidf': tfidf,
        'pca': pca,
        'scaler': scaler,
        'kmeans': kmeans,
        'similarity_matrix': similarity_matrix
    }

    with open(MODEL_FILEPATH, 'wb') as f:
        pickle.dump(models, f)

def get_recommendations(book_title, num_recommendations=5):
    if not os.path.exists(CLUSTERED_DATA_PATH) or not os.path.exists(MODEL_FILEPATH):
        return []

    df = pd.read_csv(CLUSTERED_DATA_PATH)
    with open(MODEL_FILEPATH, 'rb') as f:
        models = pickle.load(f)
        
    similarity_matrix = models['similarity_matrix']

    match_indices = df[df['title'].str.lower().str.strip() == book_title.lower().strip()].index
    
    if len(match_indices) == 0:
        match_indices = df[df['title'].str.lower().str.contains(book_title.lower(), na=False)].index
        if len(match_indices) == 0:
            return []
            
    book_idx = match_indices[0]
    book_cluster = df.loc[book_idx, 'cluster']
    
    sim_scores = list(enumerate(similarity_matrix[book_idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    recommendations = []
    for idx, score in sim_scores:
        if idx == book_idx:
            continue
            
        row = df.iloc[idx]
        if row['cluster'] == book_cluster:
            recommendations.append((row, score))
            
        if len(recommendations) >= num_recommendations:
            break
            
    if len(recommendations) < num_recommendations:
        for idx, score in sim_scores:
            if idx == book_idx:
                continue
            row = df.iloc[idx]
            if idx not in [r[0].name for r in recommendations]:
                recommendations.append((row, score))
            if len(recommendations) >= num_recommendations:
                break
                
    return recommendations[:num_recommendations]

def get_cluster_recommendations(cluster_id, num_recommendations=5):
    if not os.path.exists(CLUSTERED_DATA_PATH):
        return []
        
    df = pd.read_csv(CLUSTERED_DATA_PATH)
    cluster_df = df[df['cluster'] == int(cluster_id)].copy()
    
    if cluster_df.empty:
        return []
        
    cluster_df['score'] = cluster_df['avg_rating'] * 10 + np.log1p(cluster_df['ratings_count'])
    cluster_df = cluster_df.sort_values(by='score', ascending=False)
    
    recommendations = []
    for _, row in cluster_df.head(num_recommendations).iterrows():
        recommendations.append((row, 1.0))
        
    return recommendations
