import time
import urllib.parse
import csv
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

SEARCH_URL = "https://openlibrary.org/search.json"
WORKS_URL = "https://openlibrary.org/works/"

HEADERS = {
    'User-Agent': 'SoftwareDevBookRecommender/1.0 (academic bootcamp project; contact: student@bootcamp.edu)'
}

def fetch_work_description(work_key):
    work_id = work_key.replace('/works/', '')
    url = f"{WORKS_URL}{work_id}.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code == 200:
            data = response.json()
            description = data.get('description', '')
            if isinstance(description, dict):
                description = description.get('value', '')
            return description.strip()
    except Exception as e:
        pass
    return ""

def fetch_books_by_subject(subject, limit=100):
    books = []
    params = {
        'q': f'subject:{subject}',
        'fields': 'key,title,author_name,number_of_pages_median,ratings_average,ratings_count,subject,cover_i',
        'limit': limit
    }
    
    url = f"{SEARCH_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"Error status code: {response.status_code}")
            return []
            
        data = response.json()
        docs = data.get('docs', [])
        
        for doc in docs:
            title = doc.get('title', '')
            if not title:
                continue
                
            authors = doc.get('author_name', [])
            author = authors[0] if authors else "Unknown Author"
            
            subjects = doc.get('subject', [])
            genres = ", ".join(subjects[:5]) if subjects else ""
            
            avg_rating = doc.get('ratings_average', 0.0)
            ratings_count = doc.get('ratings_count', 0)
            page_count = doc.get('number_of_pages_median', 0)
            cover_i = doc.get('cover_i', '')
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg" if cover_i else ""
            
            work_key = doc.get('key', '')
            
            books.append({
                'title': title,
                'raw_title': title,
                'author': author,
                'avg_rating': float(avg_rating) if avg_rating else 0.0,
                'ratings_count': int(ratings_count) if ratings_count else 0,
                'cover_url': cover_url,
                'details_url': f"https://openlibrary.org{work_key}" if work_key else "",
                'page_count': int(page_count) if page_count else 0,
                'genres': genres,
                'work_key': work_key,
                'source': 'open_library_api'
            })
            
    except Exception as e:
        print(f"Request error: {e}")
        
    print(f"Subject '{subject}' fetched {len(books)} books.")
    return books

def fetch_descriptions_parallel(books, max_workers=10):

    print(f"Starting parallel fetching of descriptions for {len(books)} books using {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_book = {}
        for book in books:
            work_key = book.get('work_key', '')
            if work_key:
                future = executor.submit(fetch_work_description, work_key)
                future_to_book[future] = book
            else:
                book['description'] = ""
                
        for i, future in enumerate(as_completed(future_to_book)):
            book = future_to_book[future]
            try:
                desc = future.result()
                book['description'] = desc
            except Exception as e:
                book['description'] = ""
                
            if (i + 1) % 50 == 0:
                print(f"Fetched {i + 1}/{len(future_to_book)} descriptions...")

def fetch_api_books(filepath):
    subjects = [
        "software-development",
        "programming",
        "computer-science",
        "software-engineering",
        "javascript",
        "python",
        "java",
        "web-development",
        "algorithms",
        "databases",
        "design-patterns"
    ]
    
    all_books = []
    seen_titles = set()
    
    books_per_subject = 80
    
    for subject in subjects:
        books = fetch_books_by_subject(subject, limit=books_per_subject)
        for b in books:
            title_lower = b['title'].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                all_books.append(b)
        
        print(f"Cumulative total unique books: {len(all_books)}")
        if len(all_books) >= 500:
            break
            
    all_books = all_books[:500]
    
    fetch_descriptions_parallel(all_books, max_workers=10)
            
    for book in all_books:
        if 'work_key' in book:
            del book['work_key']
            
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if all_books:
        keys = all_books[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_books)
        print(f"Saved {len(all_books)} API books to {filepath}")
    else:
        print("No books to save.")

def enrich_scraped_books(scraped_filepath, enriched_filepath):
    if not os.path.exists(scraped_filepath):
        print(f"Scraped file not found: {scraped_filepath}")
        return
        
    enriched_books = []
    
    with open(scraped_filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        scraped_list = list(reader)
        
    print(f"Enriching {len(scraped_list)} scraped books from Open Library...")
    
    def resolve_book_details(book):
        title = book['title']
        author = book['author']
        q = f'title:"{title}" author:"{author}"'
        params = {
            'q': q,
            'fields': 'key,number_of_pages_median,subject,cover_i',
            'limit': 1
        }
        
        url = f"{SEARCH_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                docs = data.get('docs', [])
                if docs:
                    doc = docs[0]
                    subjects = doc.get('subject', [])
                    book['genres'] = ", ".join(subjects[:5]) if subjects else ""
                    book['page_count'] = int(doc.get('number_of_pages_median', 0))
                    
                    cover_i = doc.get('cover_i', '')
                    if cover_i and (not book.get('cover_url') or 'nophoto' in book.get('cover_url', '')):
                        book['cover_url'] = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
                        
                    book['work_key'] = doc.get('key', '')
                    return
        except Exception as e:
            pass
            book['genres'] = ""
            book['page_count'] = 0
            book['work_key'] = ""

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(resolve_book_details, book) for book in scraped_list]
        for i, future in enumerate(as_completed(futures)):
            if (i + 1) % 50 == 0:
                print(f"Resolved details for {i + 1}/{len(scraped_list)} books...")

    fetch_descriptions_parallel(scraped_list, max_workers=10)

    for book in scraped_list:
        if 'work_key' in book:
            del book['work_key']
            
    os.makedirs(os.path.dirname(enriched_filepath), exist_ok=True)
    if scraped_list:
        keys = scraped_list[0].keys()
        with open(enriched_filepath, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(scraped_list)
        print(f"Saved enriched scraped books to {enriched_filepath}")