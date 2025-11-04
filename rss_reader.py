"""
Fetch RSS feeds from major journals (Nature, Science, Cell)
and save them to separate timestamped text files.
No external dependencies required.
"""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# RSS feeds
feeds = {
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Cell": "https://www.cell.com/cell/current.rss"
}

# Timestamp for filenames
timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")

# Function to fetch and parse RSS
def fetch_feed(name, url, limit=10):
    print(f"Fetching {name}...")
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read()
    except Exception as e:
        print(f"⚠️ Error fetching {name}: {e}")
        return None

    try:
        root = ET.fromstring(data)
        items = root.findall(".//item")
        lines = [f"# {name} RSS Feed — {datetime.utcnow()} UTC\n"]
        for i, item in enumerate(items[:limit], 1):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            lines.append(f"\n{i}. **{title}**\n{link}\n{desc}\n")
        return "\n".join(lines)
    except Exception as e:
        print(f"⚠️ Error parsing {name}: {e}")
        return None

# Fetch each journal
for journal, url in feeds.items():
    text = fetch_feed(journal, url)
    if not text:
        continue
    filename = f"{journal}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Saved {filename}")

print("🎉 All feeds processed.")