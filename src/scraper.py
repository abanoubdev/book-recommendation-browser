import time
import random
import re
import csv
import os
import requests
from bs4 import BeautifulSoup

def scrape_goodreads_lists(list_urls, target_limit=500):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.goodreads.com/'
    }
    
    books = []
    seen_books = set()
    
    for list_url in list_urls:
        if len(books) >= target_limit:
            break
            
        print(f"scraping list with {list_url}")
        
        try:
            response = requests.get(list_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch {list_url}. Status code: {response.status_code}")
                time.sleep(random.uniform(5, 10))
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            book_elements = soup.select('tr[itemscope][itemtype="http://schema.org/Book"]')
            
            if not book_elements:
                print(f"No book elements found on {list_url}. Moving to next list.")
                continue
                
            print(f"Found {len(book_elements)} books on {list_url}")
            
            for element in book_elements:
                try:
                    title_elem = element.select_one('a.bookTitle')
                    title = title_elem.text.strip() if title_elem else ""
                    href = title_elem['href'] if title_elem and 'href' in title_elem.attrs else ""
                    details_url = f"https://www.goodreads.com{href}" if href else ""
                    
                    clean_title = re.sub(r'\s*\([^)]*\)', '', title).strip()
                    
                    author_elem = element.select_one('a.authorName')
                    author = author_elem.text.strip() if author_elem else ""
                    
                    book_key = (clean_title.lower(), author.lower())
                    if book_key in seen_books:
                        continue
                        
                    img_elem = element.select_one('img.bookCover, img[src*="books/"]')
                    cover_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                    
                    rating_elem = element.select_one('span.minirating')
                    avg_rating = 0.0
                    ratings_count = 0
                    
                    if rating_elem:
                        rating_text = rating_elem.text.strip()
                        match_rating = re.search(r'(\d+\.\d+)\s*avg rating', rating_text)
                        match_count = re.search(r'([\d,]+)\s*rating', rating_text)
                        
                        if match_rating:
                            avg_rating = float(match_rating.group(1))
                        if match_count:
                            ratings_count = int(match_count.group(1).replace(',', ''))
                    
                    seen_books.add(book_key)
                    
                    books.append({
                        'title': clean_title,
                        'raw_title': title,
                        'author': author,
                        'avg_rating': avg_rating,
                        'ratings_count': ratings_count,
                        'cover_url': cover_url,
                        'details_url': details_url,
                        'source': 'goodreads_scraped'
                    })
                except Exception as e:
                    continue
                
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Request error on {list_url}: {e}")
            time.sleep(5)
            continue
            
    print(f"Total unique books fetched: {len(books)}")
    return books[:target_limit]

def save_books_to_csv(books, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    keys = books[0].keys() if books else ['title', 'raw_title', 'author', 'avg_rating', 'ratings_count', 'cover_url', 'details_url', 'source']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(books)
    print(f"Saved {len(books)} books to {filepath}")
