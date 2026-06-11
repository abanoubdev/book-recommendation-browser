import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Set default styling for plots
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

def plot_rating_distribution(df):
    """Plots the distribution of average ratings with mean and median."""
    plt.figure(figsize=(10, 5))
    sns.histplot(data=df, x='avg_rating', kde=True, bins=30, color='#3498db')
    plt.title('Distribution of Average Ratings', pad=15)
    plt.xlabel('Average Rating (out of 5)')
    plt.ylabel('Count of Books')
    
    mean_val = df['avg_rating'].mean()
    median_val = df['avg_rating'].median()
    plt.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
    plt.axvline(median_val, color='green', linestyle='-', label=f'Median: {median_val:.2f}')
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_popularity_distribution(df):
    """Plots the distribution of ratings count using a log scale."""
    plt.figure(figsize=(10, 5))
    sns.histplot(data=df, x='ratings_count', kde=True, bins=30, color='#2ecc71', log_scale=True)
    plt.title('Distribution of Ratings Count (Log Scale)', pad=15)
    plt.xlabel('Ratings Count (Log Scale)')
    plt.ylabel('Count of Books')
    plt.tight_layout()
    plt.show()

def plot_popularity_vs_rating(df):
    """Plots a scatter plot of ratings count vs. average rating with a trendline."""
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='ratings_count', y='avg_rating', alpha=0.6, color='#9b59b6')
    plt.xscale('log')
    plt.title('Book Popularity (Ratings Count) vs. Average Rating', pad=15)
    plt.xlabel('Ratings Count (Log Scale)')
    plt.ylabel('Average Rating')
    
    sns.regplot(data=df, x='ratings_count', y='avg_rating', scatter=False, color='red', logx=True, label='Trendline')
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_page_count_distribution(df):
    """Plots a histogram of page counts and prints summary statistics."""
    plt.figure(figsize=(10, 5))
    sns.histplot(data=df, x='page_count', kde=True, bins=30, color='#e67e22')
    plt.title('Distribution of Page Counts', pad=15)
    plt.xlabel('Page Count')
    plt.ylabel('Count of Books')
    plt.tight_layout()
    plt.show()
    
    print("Page Count Summary Statistics:")
    print(df['page_count'].describe())

def plot_top_authors(df):
    """Plots bar charts of the top authors by book count and average rating."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # 1. Top authors by book count
    top_authors_count = df['author'].value_counts().head(10)
    sns.barplot(x=top_authors_count.values, y=top_authors_count.index, ax=axes[0], palette='Blues_r')
    axes[0].set_title('Top 10 Authors by Number of Books', pad=12)
    axes[0].set_xlabel('Number of Books')
    axes[0].set_ylabel('Author')
    
    # 2. Top authors by rating (minimum 3 books in dataset)
    author_stats = df.groupby('author').agg(
        avg_rating=('avg_rating', 'mean'),
        book_count=('title', 'count')
    ).reset_index()
    
    top_rated_authors = author_stats[author_stats['book_count'] >= 3].sort_values(by='avg_rating', ascending=False).head(10)
    sns.barplot(data=top_rated_authors, x='avg_rating', y='author', ax=axes[1], palette='Oranges_r')
    axes[1].set_title('Top 10 Highest Rated Authors (Min 3 Books)', pad=12)
    axes[1].set_xlabel('Average Rating')
    axes[1].set_ylabel('Author')
    axes[1].set_xlim(3.0, 5.0)
    
    plt.tight_layout()
    plt.show()
