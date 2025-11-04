"""
Fetch RSS feeds (Nature, Science, Cell)
and upload each to Dropbox /Apps/rss_uploader/ folder.
No external libraries needed.
"""

import os, json, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime

# === Dropbox token from GitHub Secret ===
token = os.environ["DROPBOX_TOKEN"]

# === RSS feed sources ===
feeds = {
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Cell": "https://www.cell.com/cell/current.rss",
}

timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")

def fetch_feed(name, url, limit=10):
    """Fetch and parse RSS feed, return formatted text."""
    print(f"Fetching {name}...")
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = resp.read()
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
        print(f"⚠️ Error fetching {name}: {e}")
        return None

def upload_to_dropbox(content: str, dropbox_path: str):
    """Upload text directly to Dropbox App folder."""
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {token}",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "overwrite",
            "mute": False
        }),
        "Content-Type": "application/octet-stream",
    }
    req = urllib.request.Request(url, data=content.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        print(f"✅ Uploaded to {result['path_display']}")

# === Run ===
for journal, url in feeds.items():
    text = fetch_feed(journal, url)
    if not text:
        continue
    dropbox_filename = f"/{journal}_{timestamp}.txt"
    upload_to_dropbox(text, dropbox_filename)

print("🎉 All feeds uploaded to Dropbox /Apps/rss_uploader/")