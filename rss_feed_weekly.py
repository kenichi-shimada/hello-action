import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import html, re

def is_research_article(journal, link):
    """Keep only likely research/review articles."""
    if "nature.com" in link:
        return "/s" in link  # /s##### pattern
    elif "science.org" in link:
        return "10.1126/science." in link
    elif "cell.com" in link:
        return "/cell/fulltext/S" in link
    return False

def clean_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def parse_date(date_str):
    """Convert various date formats to datetime."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    # fallback: try slicing or ignoring timezone offsets
    try:
        return datetime.fromisoformat(date_str[:19]).replace(tzinfo=timezone.utc)
    except Exception:
        return None

def fetch_feed(journal, url, limit=20):
    print(f"\n=== {journal} ===")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except Exception as e:
        print(f"❌ Error fetching {journal}: {e}")
        return

    root = ET.fromstring(data)
    ns = {
        "rss": "http://purl.org/rss/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    }
    items = root.findall(".//rss:item", ns)
    print(f"Found {len(items)} total entries")

    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_items = []

    for item in items:
        title = item.findtext("rss:title", "", ns)
        link = item.findtext("rss:link", "", ns)
        desc = clean_html(item.findtext("rss:description", "", ns))
        date_str = (
            item.findtext("dc:date", "", ns)
            or item.findtext("prism:publicationDate", "", ns)
        )
        pub_date = parse_date(date_str)

        # Skip if no date or older than 7 days
        if not pub_date or pub_date < one_week_ago:
            continue
        # Skip non-research
        if not is_research_article(journal, link):
            continue

        recent_items.append((title, pub_date, link, desc))

    # Sort by newest first
    recent_items.sort(key=lambda x: x[1], reverse=True)

    if not recent_items:
        print("⚠️ No research articles in the past week.")
        return

    for i, (title, pub_date, link, desc) in enumerate(recent_items[:limit], 1):
        short_desc = (desc[:300] + "…") if len(desc) > 300 else desc
        print(f"{i}. {title}\n   {pub_date.date()}\n   {link}\n   {short_desc}\n")

# --- Feeds ---
feeds = {
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Cell": "https://www.cell.com/cell/current.rss",
}

for journal, url in feeds.items():
    fetch_feed(journal, url)