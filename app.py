from flask import Flask, render_template, request, redirect, render_template_string
import os, threading, time, re, requests
from collections import defaultdict, deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ================================
# FLASK APP
# ================================

app = Flask(__name__)

# ================================
# CONFIG
# ================================

START_URLS = ["https://www.mangakakalot.gg/"]
MAX_PAGES = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

documents = {}
inverted_index = defaultdict(set)

# ================================
# FETCH + LINKS
# ================================

def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=3)
        if resp.status_code == 403:
            return "", []
        resp.raise_for_status()
    except:
        return "", []

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
    return text, links

def same_domain(base_url, other_url):
    try:
        return urlparse(base_url).netloc == urlparse(other_url).netloc
    except:
        return False

# ================================
# CRAWLER + INDEX
# ================================

def crawl(start_urls, max_pages):
    visited = set()
    to_visit = deque(start_urls)
    docs = {}

    base = start_urls[0]

    while to_visit and len(docs) < max_pages:
        url = to_visit.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not same_domain(base, url):
            continue

        text, links = fetch_page(url)
        if text:
            docs[url] = text

        for link in links:
            if link not in visited and same_domain(base, link):
                to_visit.append(link)

    return docs

def build_index():
    global documents, inverted_index
    documents = crawl(START_URLS, MAX_PAGES)

    inverted_index = defaultdict(set)
    for url, text in documents.items():
        for token in set(tokenize(text)):
            inverted_index[token].add(url)

def delayed_crawler():
    time.sleep(2)
    build_index()

# ================================
# TOKENIZE + SEARCH
# ================================

def tokenize(text):
    return re.findall(r"\w+", text.lower())

def search_engine(query):
    tokens = tokenize(query)
    if not tokens:
        return []
    result_sets = [inverted_index.get(t, set()) for t in tokens]
    if not result_sets:
        return []
    return sorted(set.intersection(*result_sets))

# ================================
# HTML
# ================================

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Moteur de recherche SONIA</title>

  <style>
    body {
      margin: 0;
      background-color: #FFFFFF;
      font-family: Arial, sans-serif;
    }

    .search-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      background-color: #FFFFFF;
    }

    .logo {
      width: 400px;
      margin-bottom: 30px;
      background-color: #FFFFFF;
      filter: none;
    }

    .search-bar {
      display: flex;
      align-items: center;
      width: 60%;
      max-width: 600px;
      background-color: #FFFFFF;
      border: 1px solid #DDD;
      border-radius: 30px;
      padding: 10px 20px;
      box-shadow: none;
    }

    .search-bar input {
      flex: 1;
      border: none;
      outline: none;
      font-size: 16px;
      background-color: #FFFFFF;
    }

    .search-bar button {
      background-color: #6C63FF;
      color: #FFFFFF;
      border: none;
      border-radius: 20px;
      padding: 8px 16px;
      cursor: pointer;
      font-weight: bold;
      transition: background-color 0.3s ease;
    }

    .search-bar button:hover {
      background-color: #5848E5;
    }
  </style>
</head>

<body>
  <div class="search-container">

    <img src="/static/sonia.png" alt="Logo SONIA" class="logo">

    <form action="/search" method="GET" class="search-bar">
      <input type="text" name="q" placeholder="Rechercher...">
      <button type="submit">Recherche</button>
    </form>

  </div>
</body>
</html>
"""

# ================================
# ROUTES
# ================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# ================================
# LANCEMENT SERVEUR
# ================================

if __name__ == "__main__":
    threading.Thread(target=delayed_crawler, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

