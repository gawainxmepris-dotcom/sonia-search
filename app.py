from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    query = request.args.get("q", "")
    return redirect(f"https://www.google.com/search?q={query}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

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

        print(f"[CRAWL] {url}")
        text, links = fetch_page(url)
        if text:
            docs[url] = text
            print(f"[OK] {url} indexée")
        else:
            print(f"[SKIP] {url}")

        for link in links:
            if link not in visited and same_domain(base, link):
                to_visit.append(link)

    return docs

def build_index():
    global documents, inverted_index
    print("[SONIA] CRAWLER EN ARRIÈRE‑PLAN…")

    documents = crawl(START_URLS, MAX_PAGES)

    inverted_index = defaultdict(set)
    for url, text in documents.items():
        for token in set(tokenize(text)):
            inverted_index[token].add(url)

    print("[SONIA] INDEX CONSTRUIT ✔")

def delayed_crawler():
    time.sleep(2)  # <<< IMPORTANT : laisse Flask démarrer
    build_index()

# ================================
# TOKENIZE + SEARCH
# ================================

def tokenize(text):
    return re.findall(r"\w+", text.lower())

def search(query):
    tokens = tokenize(query)
    if not tokens:
        return []
    result_sets = [inverted_index.get(t, set()) for t in tokens]
    if not result_sets:
        return []
    return sorted(set.intersection(*result_sets))

# ================================
# FLASK APP
# ================================

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Moteur de recherche SONIA</title>

  <style>
    body {
      margin: 0;
      background-color: #FFFFFF; /* fond blanc pur */
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
      width: 400px; /* ajuste si besoin */
      margin-bottom: 30px;
      background-color: #FFFFFF; /* garantit aucune teinte */
      filter: none; /* supprime toute ombre */
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
      box-shadow: none; /* aucune ombre */
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

    <!-- Chemin exact vers ton logo -->
    <img src="/static/sonia.png" alt="Logo SONIA" class="logo">

    <!-- Redirection Google -->
    <form action="https://www.google.com/search" method="GET" class="search-bar">
      <input type="text" name="q" placeholder="Rechercher...">
      <button type="submit">Recherche</button>
    </form>

  </div>
<script>
  const input = document.querySelector("input[name='q']");
  const suggestionBox = document.createElement("div");

  suggestionBox.style.position = "absolute";
  suggestionBox.style.background = "#fff";
  suggestionBox.style.width = "60%";
  suggestionBox.style.maxWidth = "600px";
  suggestionBox.style.border = "1px solid #ddd";
  suggestionBox.style.borderTop = "none";
  suggestionBox.style.zIndex = "1000";
  suggestionBox.style.display = "none";

  document.querySelector(".search-container").appendChild(suggestionBox);

  input.addEventListener("input", async () => {
    const query = input.value.trim();
    if (query.length < 2) {
      suggestionBox.style.display = "none";
      return;
    }

    const url = `https://suggestqueries.google.com/complete/search?client=firefox&q=${encodeURIComponent(query)}`;
    const response = await fetch(url);
    const data = await response.json();

    const suggestions = data[1];

    suggestionBox.innerHTML = "";
    suggestions.forEach(s => {
      const item = document.createElement("div");
      item.style.padding = "10px";
      item.style.cursor = "pointer";
      item.style.borderBottom = "1px solid #eee";
      item.textContent = s;

      item.onclick = () => {
        input.value = s;
        suggestionBox.style.display = "none";
      };

      suggestionBox.appendChild(item);
    });

    suggestionBox.style.display = "block";
  });

  document.addEventListener("click", () => {
    suggestionBox.style.display = "none";
  });
</script>
</body>
</html>


"""

@app.route("/", methods=["GET"])
def home():
    q = request.args.get("q", "").strip()
    results = search(q) if q else None
    return render_template_string(HTML, q=q, results=results)

# ================================
# LANCEMENT SERVEUR
# ================================

if __name__ == "__main__":
    print("[SONIA] Serveur lancé sur http://127.0.0.1:8000")

    # Lancer le crawler APRÈS le démarrage
    threading.Thread(target=delayed_crawler, daemon=True).start()

    app.run(debug=False, port=8000)
