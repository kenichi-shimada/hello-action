import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import html, re, json

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

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
    try:
        return datetime.fromisoformat(date_str[:19]).replace(tzinfo=timezone.utc)
    except Exception:
        return None

# --------------------------------------------------
# Fetch and filter feeds
# --------------------------------------------------

def fetch_feed(journal, url):
    """Fetch one feed and return a list of (title, date, link, desc)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except Exception as e:
        print(f"❌ Error fetching {journal}: {e}")
        return []

    root = ET.fromstring(data)
    ns = {
        "rss": "http://purl.org/rss/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    }
    items = root.findall(".//rss:item", ns)
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    results = []

    for item in items:
        title = item.findtext("rss:title", "", ns)
        link = item.findtext("rss:link", "", ns)
        desc = clean_html(item.findtext("rss:description", "", ns))
        date_str = (
            item.findtext("dc:date", "", ns)
            or item.findtext("prism:publicationDate", "", ns)
        )
        pub_date = parse_date(date_str)
        if not pub_date or pub_date < one_week_ago:
            continue
        if not is_research_article(journal, link):
            continue
        results.append((title, pub_date, link, desc))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

# --------------------------------------------------
# Main workflow
# --------------------------------------------------

feeds = {
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Cell": "https://www.cell.com/cell/current.rss",
}

timestamp = datetime.utcnow().strftime("%Y-%m-%d")
digest_file = f"WeeklyDigest_{timestamp}.txt"
one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

sections = []

for journal, url in feeds.items():
    print(f"\n=== {journal} ===")
    entries = fetch_feed(journal, url)
    if not entries:
        print("⚠️ No recent research articles found.")
        continue

    section_lines = [f"# {journal} — Research Articles (past 7 days)\n"]
    for title, pub_date, link, desc in entries:
        short_desc = (desc[:300] + "…") if len(desc) > 300 else desc
        section_lines.append(
            f"- {title} ({pub_date.date()})\n  {link}\n  {short_desc}\n"
        )
    sections.append("\n".join(section_lines))

if not sections:
    print("⚠️ No research articles found in any feed.")
else:
    with open(digest_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(sections))
    print(f"\n✅ Saved digest file: {digest_file}")

# --------------------------------------------------
# Upload to Dropbox (if token provided)
# --------------------------------------------------

token = os.environ.get("DROPBOX_TOKEN")
if token and os.path.exists(digest_file):
    print("📤 Uploading digest to Dropbox...")
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {token}",
        "Dropbox-API-Arg": json.dumps({
            "path": f"/{digest_file}",
            "mode": "overwrite",
            "mute": False
        }),
        "Content-Type": "application/octet-stream",
    }
    with open(digest_file, "rb") as f:
        data = f.read()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        print(f"✅ Uploaded to Dropbox: {result['path_display']}")
else:
    print("⚠️ Dropbox upload skipped (no token found).")