import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

def fetch_feed(name, url, limit=10):
    print(f"\n=== Fetching {name} ===")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        print(f"✅ {len(data)} bytes downloaded")
    except Exception as e:
        print(f"❌ Error fetching {name}: {e}")
        return

    try:
        root = ET.fromstring(data)
        ns = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rss": "http://purl.org/rss/1.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        # RSS 1.0 items are usually direct children of rdf:RDF
        items = root.findall("rss:item", ns)
        if not items:
            # Fallback for any other structure
            items = root.findall(".//rss:item", ns)
        print(f"Found {len(items)} items")

        for i, item in enumerate(items[:limit], 1):
            title = item.findtext("rss:title", "", ns)
            link = item.findtext("rss:link", "", ns)
            desc = item.findtext("rss:description", "", ns)
            print(f"{i}. {title}\n   {link}\n   {desc[:100]}...\n")

    except Exception as e:
        print(f"❌ Error parsing XML for {name}: {e}")
        
# Test URLs
feeds = {
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Cell": "https://www.cell.com/cell/current.rss"
}

for journal, url in feeds.items():
    fetch_feed(journal, url)